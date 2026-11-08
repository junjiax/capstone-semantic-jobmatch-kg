import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from sqlalchemy.orm import Session

from app.clients.sentence_transformer import get_sentence_transformer
from app.repositories.graph.match_crud import save_cv_jd_match_result_graph
from app.models.jd import JD
from app.models.profile import Profile
from app.services.graph.graph_service import sync_cv_to_graph, sync_job_to_graph
from app.services.semantic_search.text_embedding import build_job_text, normalize_text

logger = logging.getLogger(__name__)

# ── 1. PHÂN CỤM KỸ NĂNG TƯƠNG ĐƯƠNG TRÊN KNOWLEDGE GRAPH ─────────────────────
# Các kỹ năng cùng nhóm có thể dễ dàng chuyển đổi qua lại (được tính 75% điểm tương thích)
TRANSFERABLE_CLUSTERS: Dict[str, Dict[str, Any]] = {
    "rdbms": {
        "name": "Cơ sở dữ liệu quan hệ (RDBMS)",
        "skills": {
            "postgresql",
            "postgres",
            "mysql",
            "sql",
            "mariadb",
            "oracle",
            "sql server",
            "sqlite",
        },
    },
    "nosql": {
        "name": "Cơ sở dữ liệu NoSQL",
        "skills": {"mongodb", "redis", "cassandra", "dynamodb", "elasticsearch"},
    },
    "python_web": {
        "name": "Python Web Frameworks",
        "skills": {"fastapi", "flask", "django", "tornado"},
    },
    "frontend_frameworks": {
        "name": "Modern Frontend Frameworks",
        "skills": {
            "react",
            "reactjs",
            "vue",
            "vuejs",
            "angular",
            "nextjs",
            "nuxt",
            "svelte",
        },
    },
    "containers": {
        "name": "Container & Orchestration",
        "skills": {"docker", "kubernetes", "podman", "containerization", "openshift"},
    },
    "cloud": {
        "name": "Nền tảng Điện toán đám mây (Cloud)",
        "skills": {"aws", "azure", "gcp", "google cloud"},
    },
    "ci_cd": {
        "name": "Hệ thống CI/CD & Tự động hóa",
        "skills": {"ci/cd", "github actions", "gitlab ci", "jenkins", "circleci"},
    },
    "java_frameworks": {
        "name": "Java Ecosystem",
        "skills": {"spring", "spring boot", "quarkus", "micronaut", "hibernate"},
    },
}

# ── 2. PHÂN LOẠI KỸ NĂNG CỐT LÕI (CORE) VS CÔNG CỤ PHỤ (SECONDARY) ───────────
CORE_TECH_SKILLS = {
    # Ngôn ngữ lập trình cốt lõi
    "python",
    "java",
    "c++",
    "c#",
    "javascript",
    "typescript",
    "golang",
    "go",
    "php",
    "ruby",
    "rust",
    "scala",
    "swift",
    "kotlin",
    "dart",
    # Frameworks chính
    "fastapi",
    "django",
    "flask",
    "spring",
    "spring boot",
    "react",
    "reactjs",
    "vue",
    "vuejs",
    "angular",
    "node.js",
    "express",
    "nextjs",
    ".net",
    "asp.net",
    # Chuyên môn Data/AI cốt lõi
    "machine learning",
    "deep learning",
    "ai",
    "nlp",
    "computer vision",
    "data science",
}

# Từ điển các kỹ năng dùng để fallback trích xuất từ văn bản khi JD chưa có dữ liệu bảng con
COMMON_EXTRACT_SKILLS = [
    "Python",
    "Java",
    "C++",
    "C#",
    ".NET",
    "PHP",
    "JavaScript",
    "TypeScript",
    "HTML",
    "CSS",
    "React",
    "Vue",
    "Angular",
    "Node.js",
    "Django",
    "Flask",
    "FastAPI",
    "Spring Boot",
    "SQL",
    "MySQL",
    "PostgreSQL",
    "MongoDB",
    "Redis",
    "Oracle",
    "Docker",
    "Kubernetes",
    "AWS",
    "Azure",
    "GCP",
    "CI/CD",
    "Git",
    "Linux",
    "Machine Learning",
    "Deep Learning",
    "AI",
    "NLP",
    "Data Analysis",
    "Marketing",
    "Digital Marketing",
    "SEO",
    "Content Writing",
    "Social Media",
    "Sales",
    "Customer Service",
    "Product Management",
    "Project Management",
    "Communication",
    "Teamwork",
    "Problem Solving",
    "English",
    "Excel",
    "UI/UX",
    "Figma",
]


def _find_cluster_for_skill(skill_name: str) -> Optional[Tuple[str, str]]:
    """Tìm cụm kỹ năng tương đương cho một skill."""
    s_low = skill_name.strip().lower()
    for cluster_id, cluster_info in TRANSFERABLE_CLUSTERS.items():
        skills = cluster_info["skills"]
        if any(kw == s_low or kw in s_low or s_low in kw for kw in skills):
            return cluster_id, cluster_info["name"]
    return None


def compute_cosine_similarity(
    vec_a: Union[List[float], np.ndarray],
    vec_b: Union[List[float], np.ndarray],
) -> float:
    """Tính độ tương đồng Cosine giữa 2 vector embedding."""
    a = np.asarray(vec_a, dtype=np.float64)
    b = np.asarray(vec_b, dtype=np.float64)

    if a.shape != b.shape:
        raise ValueError(f"Embedding dimensions do not match: {a.shape} vs {b.shape}")

    if np.isnan(a).any() or np.isnan(b).any():
        raise ValueError("Embedding vector contains NaN values")

    if np.isinf(a).any() or np.isinf(b).any():
        raise ValueError("Embedding vector contains Inf values")

    norm_a = float(np.linalg.norm(a))
    norm_b = float(np.linalg.norm(b))

    if norm_a < 1e-9 or norm_b < 1e-9:
        raise ValueError(
            "Cannot calculate cosine similarity: vector norm is zero or near zero"
        )

    similarity = float(np.dot(a, b) / (norm_a * norm_b))
    return float(max(-1.0, min(1.0, similarity)))


def evaluate_smart_skill_matching(
    profile: Profile,
    jd: JD,
) -> Dict[str, Any]:
    """
    So khớp thông minh đa chiều:
    - Kỹ năng cốt lõi (Core Skills)
    - Kỹ năng tương đương / chuyển đổi (Transferable Skills trên Knowledge Graph)
    - Kỹ năng công cụ còn thiếu (Missing Tools)
    - Kỹ năng cộng thêm (Bonus Skills)
    """
    candidate_skills = [
        s.SkillTitle.strip()
        for s in (profile.skills or [])
        if s.SkillTitle and s.SkillTitle.strip()
    ]
    jd_skills = [
        s.Title.strip() for s in (jd.skills or []) if s.Title and s.Title.strip()
    ]

    jd_full_text = (
        f"{build_job_text(jd) or ''} {jd.CleanText or ''} {jd.RawText or ''} "
        f"{jd.Title or ''} {jd.Qualification or ''} {jd.Responsibility or ''}"
    )

    # Nếu JD chưa có records trong bảng JD_SKILL, tự động trích xuất từ văn bản
    if not jd_skills and jd_full_text.strip():
        extracted = []
        for kw in COMMON_EXTRACT_SKILLS:
            if re.search(r"\b" + re.escape(kw) + r"\b", jd_full_text, re.IGNORECASE):
                extracted.append(kw)
        jd_skills = extracted

    cand_skills_map = {s.lower(): s for s in candidate_skills}

    matched_core_skills: List[str] = []
    matched_tool_skills: List[str] = []
    transferable_skills: List[Dict[str, str]] = []
    missing_skills: List[str] = []
    consumed_cand_skills = set()

    # Duyệt từng kỹ năng JD yêu cầu
    for req in jd_skills:
        req_low = req.lower()

        # 1. Kiểm tra Exact Match hoặc Substring Match
        direct_match = None
        if req_low in cand_skills_map:
            direct_match = cand_skills_map[req_low]
        else:
            for c_low, c_orig in cand_skills_map.items():
                if req_low in c_low or c_low in req_low:
                    direct_match = c_orig
                    break

        if direct_match:
            consumed_cand_skills.add(direct_match.lower())
            if any(k in req_low for k in CORE_TECH_SKILLS):
                matched_core_skills.append(req)
            else:
                matched_tool_skills.append(req)
            continue

        # 2. Kiểm tra Transferable Skill (Kỹ năng tương đương trên Knowledge Graph)
        req_cluster = _find_cluster_for_skill(req)
        found_transferable = False

        if req_cluster:
            cluster_id, cluster_name = req_cluster
            for c_low, c_orig in cand_skills_map.items():
                if c_low not in consumed_cand_skills:
                    c_cluster = _find_cluster_for_skill(c_orig)
                    if c_cluster and c_cluster[0] == cluster_id:
                        transferable_skills.append(
                            {
                                "required_skill": req,
                                "candidate_skill": c_orig,
                                "cluster_name": cluster_name,
                                "note": f"Cùng nhóm {cluster_name} - Dễ dàng chuyển đổi",
                            }
                        )
                        consumed_cand_skills.add(c_low)
                        found_transferable = True
                        break

        if not found_transferable:
            missing_skills.append(req)

    # 3. Kỹ năng cộng thêm (Bonus Skills): Ứng viên có nhưng JD không bắt buộc
    bonus_skills = [
        s for s in candidate_skills if s.lower() not in consumed_cand_skills
    ]

    # 4. Tính toán điểm trọng số thông minh
    total_req_count = len(jd_skills)
    if total_req_count > 0:
        earned_points = (
            len(matched_core_skills) * 1.0
            + len(matched_tool_skills) * 1.0
            + len(transferable_skills) * 0.75
        )
        base_skill_ratio = earned_points / total_req_count
    else:
        base_skill_ratio = 0.0

    return {
        "total_required_skills": total_req_count,
        "matched_core_skills": matched_core_skills,
        "matched_tool_skills": matched_tool_skills,
        "transferable_skills": transferable_skills,
        "missing_skills": missing_skills,
        "bonus_skills": bonus_skills,
        "base_skill_ratio": base_skill_ratio,
    }


def calculate_cv_jd_matching(
    db: Session,
    profile_id: int,
    jd_id: int,
) -> Dict[str, Any]:
    """
    Đánh giá mức độ phù hợp toàn diện giữa CV và JD.
    Tự động đồng bộ và lưu kết quả MATCHES_JD lên Knowledge Graph Neo4j.
    """
    # 1. Truy vấn Profile và JD từ PostgreSQL
    profile = db.query(Profile).filter(Profile.Id == profile_id).first()
    if profile is None:
        raise ValueError(f"Profile with id {profile_id} not found")

    jd = db.query(JD).filter(JD.Id == jd_id).first()
    if jd is None:
        raise ValueError(f"JD with id {jd_id} not found")

    # 2. Lấy nội dung văn bản để tính Semantic Similarity
    cv_text = normalize_text(profile.CleanText) or normalize_text(profile.RawText)
    if not cv_text:
        raise ValueError(f"Profile with id {profile_id} has no valid text content")

    jd_text = (
        build_job_text(jd) or normalize_text(jd.CleanText) or normalize_text(jd.RawText)
    )
    if not jd_text:
        raise ValueError(f"JD with id {jd_id} has no valid text content")

    # 3. Tính Cosine Similarity câu từ
    client = get_sentence_transformer()
    cv_vector = client.encode(cv_text, normalize=True)
    jd_vector = client.encode(jd_text, normalize=True)
    semantic_similarity = compute_cosine_similarity(cv_vector, jd_vector)

    # 4. Phân tích Kỹ năng Đa chiều (Cốt lõi, Tương đương, Công cụ, Bonus)
    analysis = evaluate_smart_skill_matching(profile, jd)

    base_skill_ratio = analysis["base_skill_ratio"]
    matched_core = analysis["matched_core_skills"]
    transferable = analysis["transferable_skills"]
    missing = analysis["missing_skills"]
    bonus = analysis["bonus_skills"]

    # 5. Tính điểm tổng hợp (Overall Match Score)
    bonus_points = min(0.05, len(bonus) * 0.025)
    semantic_component = max(0.0, semantic_similarity) * 0.15

    if analysis["total_required_skills"] > 0:
        match_score = (base_skill_ratio * 0.80) + semantic_component + bonus_points
        # Nếu ứng viên đáp ứng các kỹ năng cốt lõi -> đạt tối thiểu 75%
        if matched_core and len(missing) <= len(matched_core):
            match_score = max(match_score, 0.75)
    else:
        match_score = max(0.0, semantic_similarity)

    match_score = round(min(1.0, max(0.0, match_score)), 4)
    percentage = round(match_score * 100, 1)

    # 6. Đưa ra Kết luận
    if match_score >= 0.70:
        is_suitable = True
        fit_level = "HIGHLY_SUITABLE"
        core_str = ", ".join(matched_core) if matched_core else "chuyên môn chính"
        verdict = (
            f"CV rất phù hợp để ứng tuyển vào vị trí {jd.Title} ({percentage}%). "
            f"Bạn đã đáp ứng vững chắc các kỹ năng cốt lõi ({core_str})."
        )
    elif match_score >= 0.40:
        is_suitable = True
        fit_level = "MODERATE_SUITABLE"
        missing_str = ", ".join(missing[:3]) if missing else "một số yêu cầu phụ"
        verdict = (
            f"CV có tiềm năng và phù hợp một phần với vị trí {jd.Title} ({percentage}%). "
            f"Bạn nên trang bị thêm các kỹ năng còn thiếu ({missing_str}) để tăng khả năng trúng tuyển."
        )
    else:
        is_suitable = False
        fit_level = "LOW_SUITABLE"
        verdict = (
            f"CV hiện tại chưa phù hợp để ứng tuyển vào vị trí {jd.Title} ({percentage}%). "
            f"Vị trí này đòi hỏi các kỹ năng chuyên môn khác với hồ sơ hiện tại của bạn."
        )

    all_matched = matched_core + analysis["matched_tool_skills"]

    # 7. Tích hợp trực tiếp lên Knowledge Graph Neo4j
    graph_synced = False
    try:
        sync_cv_to_graph(db, profile_id)
        sync_job_to_graph(db, jd_id)
        save_cv_jd_match_result_graph(
            cv_id=profile_id,
            jd_id=jd_id,
            scores={
                "totalResult": match_score,
                "domainScore": semantic_similarity,
                "expertiseScore": semantic_similarity,
                "skillScore": base_skill_ratio,
                "experienceScore": 1.0 if is_suitable else 0.5,
                "qualificationScore": 1.0,
            },
        )
        graph_synced = True
        logger.info(
            f"Persisted MATCHES_JD edge on Neo4j for CV {profile_id} and JD {jd_id}"
        )
    except Exception as exc:
        logger.warning(f"Neo4j sync warning: {exc}")
        graph_synced = False

    return {
        "profile_id": profile_id,
        "jd_id": jd_id,
        "is_suitable": is_suitable,
        "fit_level": fit_level,
        "match_score": match_score,
        "verdict": verdict,
        "matched_skills": all_matched,
        "transferable_skills": transferable,
        "missing_skills": missing,
        "bonus_skills": bonus,
        "semantic_similarity": round(semantic_similarity, 4),
        "graph_synced": graph_synced,
    }
