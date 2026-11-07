from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.schemas.response import ResponseSchema
from app.services.skill_features.skill_matching import calculate_cv_jd_matching

router = APIRouter(tags=["Job"])

# Danh sách chuẩn hóa các Domain và Expertise chính trong ngành CNTT
STANDARD_IT_DOMAINS = [
    "Backend Development",
    "Frontend Development",
    "Cloud & DevOps Engineering",
    "Data Engineering & AI",
    "Software Testing & QA",
    "Information Security",
]

STANDARD_IT_EXPERTISES = [
    "Software & Backend Engineering",
    "Frontend Web Engineering",
    "CI/CD & Cloud Infrastructure",
    "Machine Learning & AI",
    "Automated Testing & QA",
    "Cybersecurity & InfoSec",
]


class TransferableSkillItem(BaseModel):
    required_skill: str = Field(..., description="Kỹ năng JD yêu cầu")
    candidate_skill: str = Field(..., description="Kỹ năng tương đương ứng viên có")
    cluster_name: str = Field(..., description="Nhóm chuyên môn chung trên Knowledge Graph")
    note: str = Field(..., description="Mô tả mức độ chuyển đổi")


class MatchEvaluationResponse(BaseModel):
    profile_id: int = Field(..., description="ID của hồ sơ ứng viên")
    jd_id: int = Field(..., description="ID của tin tuyển dụng")
    is_suitable: bool = Field(..., description="Có phù hợp để nộp đơn (apply) hay không")
    fit_level: str = Field(..., description="Cấp độ phù hợp (HIGHLY_SUITABLE, MODERATE_SUITABLE, LOW_SUITABLE)")
    match_score: float = Field(..., description="Điểm đánh giá phù hợp tổng hợp (0.0 đến 1.0)")
    verdict: str = Field(..., description="Kết luận đánh giá chi tiết mức độ phù hợp")
    matched_skills: List[str] = Field(default_factory=list, description="Kỹ năng CV đã có (khớp chính xác với JD)")
    transferable_skills: List[TransferableSkillItem] = Field(
        default_factory=list,
        description="Kỹ năng tương đương trên Knowledge Graph (dễ dàng chuyển đổi)",
    )
    missing_skills: List[str] = Field(default_factory=list, description="Kỹ năng CV còn thiếu so với JD")
    bonus_skills: List[str] = Field(default_factory=list, description="Kỹ năng thế mạnh cộng thêm của ứng viên")
    semantic_similarity: float = Field(..., description="Điểm tương đồng ngữ nghĩa câu từ (Cosine Similarity)")
    graph_synced: bool = Field(default=False, description="Trạng thái đồng bộ và lưu kết quả lên Neo4j Knowledge Graph")


class MatrixData(BaseModel):
    rows: List[str] = Field(..., description="Thuộc tính CV: Hard Skills, Work Experience, Education, Overall Profile")
    columns: List[str] = Field(..., description="Danh sách Domain và Expertise chuẩn hóa")
    column_types: List[str] = Field(..., description="Phân loại cột: 'domain' hoặc 'expertise'")
    data: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Ma trận tương quan dạng Key-Value (Row -> {Column: Score}) trực quan, dễ đọc và tra cứu",
    )


class RecommendedDomainItem(BaseModel):
    rank: int = Field(..., description="Thứ hạng phù hợp")
    domain: str = Field(..., description="Tên lĩnh vực CNTT")
    compatibility_score: float = Field(..., description="Điểm tương thích tổng hợp (0.0 đến 1.0)")
    skill_coverage_ratio: float = Field(..., description="Tỷ lệ đáp ứng kỹ năng trong Domain")
    matched_skills: List[str] = Field(default_factory=list, description="Kỹ năng CV đã có")
    missing_skills: List[str] = Field(default_factory=list, description="Kỹ năng CV cần học thêm để phát triển")
    career_guidance: str = Field(..., description="Lời khuyên định hướng sự nghiệp")


class CleanDomainMatrixResponse(BaseModel):
    profile_id: int = Field(..., description="ID hồ sơ ứng viên")
    matrix: MatrixData = Field(..., description="Ma trận tương quan N * K rút gọn súc tích")
    top_recommended_domains: List[RecommendedDomainItem] = Field(
        default_factory=list, description="Top các Domain phù hợp nhất với CV trong CNTT"
    )


@router.get("/")
def health_check():
    return {"status": "activate", "message": "API is running successfully."}


@router.get(
    "/match-similarity",
    response_model=ResponseSchema[MatchEvaluationResponse],
    status_code=status.HTTP_200_OK,
    summary="BÀI TOÁN 1: Đánh giá CV có phù hợp để apply Job hay không (1 CV vs 1 JD)",
    description="Kiểm tra mức độ phù hợp toàn diện giữa CV của ứng viên (profile_id) và Job Description (jd_id). "
                "Tự động đồng bộ thực thể lên Neo4j và lưu quan hệ MATCHES_JD trực tiếp trên Đồ thị tri thức.",
)
def match_cv_jd_similarity(
    profile_id: int = Query(..., description="ID của hồ sơ ứng viên (Profile ID)", ge=1),
    jd_id: int = Query(..., description="ID của tin tuyển dụng (JD ID)", ge=1),
    db: Session = Depends(get_db),
):
    try:
        evaluation = calculate_cv_jd_matching(db=db, profile_id=profile_id, jd_id=jd_id)
    except ValueError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(exc)
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(exc))

    return ResponseSchema[MatchEvaluationResponse](
        success=True,
        message="Đánh giá mức độ phù hợp CV - JD thành công (Đã đồng bộ Knowledge Graph)",
        data=MatchEvaluationResponse(**evaluation),
    )


@router.get(
    "/domain-matrix/{profile_id}",
    response_model=ResponseSchema[CleanDomainMatrixResponse],
    status_code=status.HTTP_200_OK,
    summary="BÀI TOÁN 2: Ma trận tương quan Domain & Định hướng nghề nghiệp (1 CV vs Many Domains)",
    description="Trả lời câu hỏi: CV của tôi có thể apply vào những domain nào trong CNTT? "
                "Hệ thống tự động phân tích Profile để tạo ma trận tương quan linh hoạt: "
                "Rows động theo các mục thực tế có trong CV (Hard Skills, Work Experience, Education...) "
                "và Columns động gồm các Domain & Expertise liên quan nhất trên Knowledge Graph.",
)
def get_domain_correlation_matrix(
    profile_id: int,
    target_domains: Optional[List[str]] = Query(default=None, description="Tùy chọn lọc Domain cụ thể (để trống hệ thống sẽ tự động tìm các Domain & Expertise liên quan nhất trên Knowledge Graph)"),
    db: Session = Depends(get_db),
):
    from app.services import graph_service

    raw_res = graph_service.calculate_domain_skill_gap_matrix_service(
        db, cv_id=profile_id, target_domains=target_domains, target_expertises=None
    )
    if "error" in raw_res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=raw_res["error"])

    # Chuẩn hóa Top 5 domain gọn gàng
    top_domains = []
    for d in raw_res.get("domainRankings", [])[:5]:
        top_domains.append(
            RecommendedDomainItem(
                rank=d.get("rank", 1),
                domain=d.get("domain", ""),
                compatibility_score=d.get("compatibilityScore", 0.0),
                skill_coverage_ratio=d.get("skillCoverageRatio", 0.0),
                matched_skills=d.get("matchedSkills", []),
                missing_skills=d.get("missingSkills", []),
                career_guidance=d.get("careerGuidance", ""),
            )
        )

    matrix_info = raw_res.get("matrix", {})
    raw_matrix_data = matrix_info.get("data", [])
    row_names = matrix_info.get("rows", [])
    col_names = matrix_info.get("columns", [])

    # Chuyển data từ mảng số 2 chiều không nhãn [[0.5, 0, ...], ...] thành dictionary có nhãn theo từng Row và Column:
    # {
    #     "Hard Skills": {"Backend Development": 0.5, "Frontend Development": 0.0, ...},
    #     "Work Experience": {...},
    #     ...
    # }
    structured_matrix_data: Dict[str, Dict[str, float]] = {}
    for r_idx, r_name in enumerate(row_names):
        structured_matrix_data[r_name] = {}
        row_vals = raw_matrix_data[r_idx] if r_idx < len(raw_matrix_data) else []
        for c_idx, c_name in enumerate(col_names):
            val = row_vals[c_idx] if c_idx < len(row_vals) else 0.0
            structured_matrix_data[r_name][c_name] = round(float(val), 4)

    clean_matrix = MatrixData(
        rows=row_names,
        columns=col_names,
        column_types=matrix_info.get("columnTypes", []),
        data=structured_matrix_data,
    )

    clean_data = CleanDomainMatrixResponse(
        profile_id=profile_id,
        matrix=clean_matrix,
        top_recommended_domains=top_domains,
    )

    return ResponseSchema[CleanDomainMatrixResponse](
        success=True,
        message=f"Đã tạo ma trận tương quan và định hướng Domain cho CV {profile_id}",
        data=clean_data,
    )
