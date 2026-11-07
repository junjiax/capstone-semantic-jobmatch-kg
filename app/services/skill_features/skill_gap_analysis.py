import logging
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.clients.sentence_transformer import get_sentence_transformer
from app.repositories.postgres import profile_skill as profile_skill_repo
from app.repositories.postgres import jd_skill as jd_skill_repo
from app.repositories.postgres import profile as profile_repo
from app.repositories.postgres import jd as jd_repo
from app.schemas.skill_gap import (
    SkillGapAnalysisRequest,
    SkillGapResponse,
    SkillGapSummary,
    MatchedSkillItem,
    PartialSkillItem,
    MissingSkillItem,
    ExtraSkillItem,
    MatchStatus,
)

logger = logging.getLogger(__name__)


def _normalize_skill(skill: str) -> str:
    """Chuẩn hóa chuỗi kỹ năng: loại bỏ khoảng trắng dư thừa và chuyển về chữ thường."""
    if not skill:
        return ""
    return " ".join(skill.strip().lower().split())


def _generate_recommendation(missing_skill: str, closest_skill: Optional[str] = None, similarity: float = 0.0) -> str:
    """Tạo câu khuyến nghị hành động học tập thông minh dựa trên kỹ năng thiếu."""
    if closest_skill and similarity >= 0.60:
        return (
            f"Bạn đã có nền tảng tốt về '{closest_skill}' (độ tương đồng {similarity*100:.1f}%). "
            f"Hãy tập trung học thêm cú pháp và kiến trúc đặc thù của '{missing_skill}' qua dự án mẫu 1-2 tuần."
        )
    return (
        f"Kỹ năng '{missing_skill}' là yêu cầu còn thiếu. "
        f"Khuyến nghị tham gia khóa học cấp tốc hoặc tự xây dựng đồ án thực hành từ căn bản."
    )


def analyze_skill_gap_service(
    db: Optional[Session],
    request: SkillGapAnalysisRequest
) -> SkillGapResponse:
    """
    Thực hiện phân tích khoảng trống kỹ năng:
    - Xác định kỹ năng Đáp ứng (Matched)
    - Kỹ năng Đáp ứng một phần (Partially Matched)
    - Kỹ năng Còn thiếu (Missing)
    - Kỹ năng bổ trợ (Extra)
    """
    model_client = get_sentence_transformer()

    # ─────────────────────────────────────────────────────────────
    # BƯỚC 1: THU THẬP DANH SÁCH KỸ NĂNG CỦA ỨNG VIÊN VÀ JD
    # ─────────────────────────────────────────────────────────────
    cand_skill_entries: List[Dict[str, Any]] = []  # [{name, vector, ...}]
    req_skill_entries: List[Dict[str, Any]] = []

    # 1.1. Lấy kỹ năng Ứng viên (Profile)
    if request.profile_id is not None and db is not None:
        db_cand_skills = profile_skill_repo.get_skills_by_profile_id(db, request.profile_id)
        for s in db_cand_skills:
            cand_skill_entries.append({
                "name": s.SkillTitle,
                "vector": s.Vector,
            })
    elif request.candidate_skills:
        for s_name in request.candidate_skills:
            cand_skill_entries.append({
                "name": s_name.strip(),
                "vector": None,
            })

    # 1.2. Lấy kỹ năng Yêu cầu (JD)
    if request.jd_id is not None and db is not None:
        db_req_skills = jd_skill_repo.get_jd_skills(db, request.jd_id)
        for s in db_req_skills:
            req_skill_entries.append({
                "name": s.Title,
                "vector": s.Vector,
                "importance": 1.0,
            })
    elif request.required_skills:
        for s_name in request.required_skills:
            req_skill_entries.append({
                "name": s_name.strip(),
                "vector": None,
                "importance": 1.0,
            })

    # Kiểm tra trường hợp danh sách rỗng
    if not req_skill_entries:
        return SkillGapResponse(
            profile_id=request.profile_id,
            jd_id=request.jd_id,
            summary=SkillGapSummary(
                total_required_skills=0,
                total_matched_skills=0,
                total_partial_skills=0,
                total_missing_skills=0,
                total_extra_skills=len(cand_skill_entries),
                skill_coverage_ratio=1.0 if not cand_skill_entries else 0.0,
                skill_coverage_percentage=100.0 if not cand_skill_entries else 0.0,
                fit_level="NOT_APPLICABLE",
            ),
            matched_skills=[],
            partially_matched_skills=[],
            missing_skills=[],
            extra_skills=[
                ExtraSkillItem(skill_name=item["name"], potential_value="Kỹ năng tự do") 
                for item in cand_skill_entries
            ],
            recommendations=["Vị trí công việc hiện không liệt kê yêu cầu kỹ năng cụ thể."],
        )

    # ─────────────────────────────────────────────────────────────
    # BƯỚC 2: TỰ ĐỘNG SINH VECTOR EMBEDDING NẾU CHƯA CÓ
    # ─────────────────────────────────────────────────────────────
    # Encode vector cho ứng viên nếu cần
    for item in cand_skill_entries:
        if item["vector"] is None or len(item["vector"]) == 0:
            item["vector"] = model_client.encode(item["name"], normalize=True)

    # Encode vector cho yêu cầu JD nếu cần
    for item in req_skill_entries:
        if item["vector"] is None or len(item["vector"]) == 0:
            item["vector"] = model_client.encode(item["name"], normalize=True)

    # ─────────────────────────────────────────────────────────────
    # BƯỚC 3: SO KHỚP KHOA HỌC (EXACT MATCH & COSINE SIMILARITY)
    # ─────────────────────────────────────────────────────────────
    match_threshold = request.match_threshold
    partial_threshold = request.partial_threshold

    matched_results: List[MatchedSkillItem] = []
    partial_results: List[PartialSkillItem] = []
    missing_results: List[MissingSkillItem] = []
    recommendations: List[str] = []

    # Tập hợp các kỹ năng của ứng viên đã được ghép để sau đó tìm Extra Skills
    used_candidate_indices = set()

    for req_idx, req in enumerate(req_skill_entries):
        req_name = req["name"]
        req_norm = _normalize_skill(req_name)
        req_vec = req["vector"]
        req_importance = req.get("importance", 1.0)

        # 3.1. Thử Exact Name Match trước
        exact_found = False
        for cand_idx, cand in enumerate(cand_skill_entries):
            cand_name = cand["name"]
            cand_norm = _normalize_skill(cand_name)

            if req_norm == cand_norm:
                matched_results.append(
                    MatchedSkillItem(
                        skill_name=req_name,
                        matched_with=cand_name,
                        similarity_score=1.0,
                        is_exact_match=True,
                        importance=req_importance,
                    )
                )
                used_candidate_indices.add(cand_idx)
                exact_found = True
                break

        if exact_found:
            continue

        # 3.2. Nếu không trùng tên, tính Cosine Similarity với từng kỹ năng của ứng viên
        best_cand_idx = -1
        best_cand_name = ""
        max_sim = -1.0

        for cand_idx, cand in enumerate(cand_skill_entries):
            cand_vec = cand["vector"]
            sim = model_client.cosine_similarity(req_vec, cand_vec)
            if sim > max_sim:
                max_sim = sim
                best_cand_idx = cand_idx
                best_cand_name = cand["name"]

        # 3.3. Phân loại theo Ngưỡng
        if max_sim >= match_threshold:
            # Tương đương rất cao -> ĐÁP ỨNG HOÀN TOÀN
            matched_results.append(
                MatchedSkillItem(
                    skill_name=req_name,
                    matched_with=best_cand_name,
                    similarity_score=round(max_sim, 4),
                    is_exact_match=False,
                    importance=req_importance,
                )
            )
            used_candidate_indices.add(best_cand_idx)

        elif max_sim >= partial_threshold:
            # Tương đương gần gũi -> ĐÁP ỨNG MỘT PHẦN
            partial_results.append(
                PartialSkillItem(
                    skill_name=req_name,
                    closest_candidate_skill=best_cand_name,
                    similarity_score=round(max_sim, 4),
                    importance=req_importance,
                    gap_reason=(
                        f"Ứng viên có '{best_cand_name}' có độ tương đồng {max_sim*100:.1f}% với '{req_name}'. "
                        f"Có thể chuyển giao kinh nghiệm sau thời gian đào tạo ngắn."
                    ),
                )
            )
            used_candidate_indices.add(best_cand_idx)
            rec = _generate_recommendation(req_name, closest_skill=best_cand_name, similarity=max_sim)
            recommendations.append(rec)

        else:
            # Độ tương đồng dưới ngưỡng -> CÒN THIẾU (SKILL GAP)
            missing_results.append(
                MissingSkillItem(
                    skill_name=req_name,
                    importance=req_importance,
                    urgency_level="HIGH" if req_importance >= 1.5 else "MEDIUM",
                    learning_recommendation=_generate_recommendation(req_name),
                )
            )
            rec = _generate_recommendation(req_name)
            recommendations.append(rec)

    # 3.4. Xác định Extra Skills (Kỹ năng CV có mà JD không đòi)
    extra_results: List[ExtraSkillItem] = []
    for cand_idx, cand in enumerate(cand_skill_entries):
        if cand_idx not in used_candidate_indices:
            extra_results.append(
                ExtraSkillItem(
                    skill_name=cand["name"],
                    potential_value="Thế mạnh mở rộng, hỗ trợ phát triển"
                )
            )

    # ─────────────────────────────────────────────────────────────
    # BƯỚC 4: TÍNH TOÁN CHỈ SỐ BAO PHỦ VÀ XẾP LOẠI PHÙ HỢP
    # ─────────────────────────────────────────────────────────────
    total_req = len(req_skill_entries)
    total_matched = len(matched_results)
    total_partial = len(partial_results)
    total_missing = len(missing_results)
    total_extra = len(extra_results)

    # Trọng số kỹ năng:
    # Matched được 100% trọng số, Partial được 50% trọng số
    matched_weight_sum = sum(item.importance for item in matched_results)
    partial_weight_sum = sum(item.importance * 0.5 for item in partial_results)
    total_weight_sum = sum(req.get("importance", 1.0) for req in req_skill_entries)

    if total_weight_sum > 0:
        coverage_ratio = round((matched_weight_sum + partial_weight_sum) / total_weight_sum, 4)
    else:
        coverage_ratio = 0.0

    coverage_percentage = round(coverage_ratio * 100, 2)

    # Phân hạng mức độ phù hợp
    if coverage_ratio >= 0.85:
        fit_level = "EXCELLENT"
    elif coverage_ratio >= 0.70:
        fit_level = "GOOD"
    elif coverage_ratio >= 0.50:
        fit_level = "MODERATE"
    else:
        fit_level = "LOW"

    summary = SkillGapSummary(
        total_required_skills=total_req,
        total_matched_skills=total_matched,
        total_partial_skills=total_partial,
        total_missing_skills=total_missing,
        total_extra_skills=total_extra,
        skill_coverage_ratio=coverage_ratio,
        skill_coverage_percentage=coverage_percentage,
        fit_level=fit_level,
    )

    return SkillGapResponse(
        profile_id=request.profile_id,
        jd_id=request.jd_id,
        summary=summary,
        matched_skills=matched_results,
        partially_matched_skills=partial_results,
        missing_skills=missing_results,
        extra_skills=extra_results,
        recommendations=recommendations,
    )
