import logging
import math
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.profile import Profile
from app.models.jd import JD
from app.models.jd_skill import JDSkill
from app.models.profile import Profile
from app.models.profile_skill import ProfileSkill

from app.repositories.graph import schema as graph_schema
from app.repositories.graph import sync_crud as graph_sync
from app.repositories.graph import match_crud as graph_match

logger = logging.getLogger(__name__)


def compute_cosine_similarity(
    vec1: Optional[List[float]], vec2: Optional[List[float]]
) -> float:
    """Tính độ tương đồng Cosine chuẩn giữa 2 vector, trả về float trong [0.0, 1.0]."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    raw_sim = dot_product / (norm_a * norm_b)
    return round(max(0.0, min(1.0, float(raw_sim))), 4)


def setup_knowledge_graph_schema() -> Dict[str, Any]:
    """Khởi tạo schema (constraints, indexes, vector index) trên Neo4j."""
    return graph_schema.init_graph_schema()


JOB_DOMAIN_MAP = {
    "marketing intern": ("Business & Marketing", "Digital Marketing"),
    "customer service representative": ("Customer Support", "Customer Operations"),
    "software engineer": ("Backend Development", "Software & Backend Engineering"),
    "data analyst": ("Data Engineering & AI", "Data Analytics & Business Intelligence"),
    "project manager": ("IT Management", "Technical Project Management"),
    "ui/ux designer": ("Frontend Development", "UI/UX & Design Systems"),
    "qa engineer": ("Software Testing & QA", "Automated Testing & QA"),
    "product manager": ("IT Management", "Product Management"),
    "devops engineer": ("Cloud & DevOps Engineering", "CI/CD & Cloud Infrastructure"),
    "system administrator": (
        "Cloud & DevOps Engineering",
        "System & Network Administration",
    ),
    "frontend": ("Frontend Development", "Frontend Web Engineering"),
    "backend": ("Backend Development", "Backend Web Engineering"),
    "fullstack": ("Software Engineering", "Fullstack Development"),
    "data engineer": ("Data Engineering & AI", "Data Engineering"),
    "machine learning": ("Data Engineering & AI", "Machine Learning & AI"),
    "security": ("Information Security", "Cybersecurity & InfoSec"),
}


def get_domain_expertise_for_title(title: str) -> tuple[str, str]:
    t = (title or "").strip().lower()
    for k, v in JOB_DOMAIN_MAP.items():
        if k in t:
            return v[0], v[1]
    return "Information Technology", "General IT"


def _mean_vector(vectors):
    vectors = [list(v) for v in vectors if v is not None]
    if not vectors:
        return None
    return [sum(values) / len(vectors) for values in zip(*vectors)]


def _profile_vector(profile):
    return _mean_vector(
        item.Vector
        for group in (profile.skills, profile.work_experiences, profile.educations)
        for item in group
    )


def _experience_years(experiences, today=None):
    """Count calendar days once, including overlapping jobs and ongoing work."""
    from datetime import date

    today = today or date.today()
    intervals = sorted(
        (item.StartDate, min(item.EndDate or today, today))
        for item in experiences
        if item.StartDate and item.StartDate <= today
    )
    merged = []
    for start, end in intervals:
        if end <= start:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return sum((end - start).days for start, end in merged) / 365.25


def _skill_payload(title):
    # Skill IDs are shared by normalized name across PROFILE_SKILL and JD_SKILL.
    from hashlib import sha256

    normalized = graph_sync.normalize_skill_name(title)
    return {
        "skillId": int.from_bytes(sha256(normalized.encode()).digest()[:7], "big"),
        "skillName": title,
    }


def sync_cv_to_graph(db: Session, cv_id: int) -> bool:
    """Sync the current PROFILE schema to Neo4j without fabricating fake data."""
    profile = db.query(Profile).filter(Profile.Id == cv_id).first()
    if profile is None:
        return False
    if profile.user:
        owner = profile.user
        role_val = (
            owner.Role.value
            if hasattr(owner.Role, "value")
            else str(owner.Role or "applicant")
        )
        graph_sync.upsert_user_node(
            user_id=owner.Id,
            email=owner.Email,
            full_name=owner.FullName or "",
            role=role_val,
        )
    graph_sync.upsert_cv_node(
        cv_id=profile.Id,
        user_id=profile.UserId,
        title=profile.Title or "",
        summary=profile.CleanText or profile.RawText or "",
        embedding=_profile_vector(profile),
    )
    cv_skills = []
    if profile.skills:
        for s in profile.skills:
            if s.SkillTitle and s.SkillTitle.strip():
                cv_skills.append(_skill_payload(s.SkillTitle))
    graph_sync.sync_cv_skills_graph(cv_id, cv_skills)

    # Đồng bộ Học vấn (PROFILE_EDU)
    cv_educations = []
    if profile.educations:
        for idx, edu in enumerate(profile.educations):
            edu_id = getattr(edu, "Id", None) or int(f"{cv_id}1{idx:02d}")
            level_str = ""
            if getattr(edu, "Level", None):
                level_str = edu.Level.value if hasattr(edu.Level, "value") else str(edu.Level)
            cv_educations.append({
                "educationId": edu_id,
                "school": getattr(edu, "School", None) or "",
                "major": getattr(edu, "Major", None) or "",
                "degree": getattr(edu, "Degree", None) or "",
                "level": level_str,
                "graduationYear": getattr(edu, "GraduationYear", None),
                "gpa": float(edu.GPA) if getattr(edu, "GPA", None) is not None else None,
            })
    graph_sync.sync_cv_educations_graph(cv_id, cv_educations)

    # Đồng bộ Kinh nghiệm làm việc (PROFILE_WORK_EXP)
    cv_experiences = []
    if profile.work_experiences:
        from datetime import date
        today = date.today()
        for idx, exp in enumerate(profile.work_experiences):
            exp_id = getattr(exp, "Id", None) or int(f"{cv_id}2{idx:02d}")
            start = getattr(exp, "StartDate", None)
            end = getattr(exp, "EndDate", None) or today
            years = 0.0
            if start and end and end >= start:
                years = round((end - start).days / 365.25, 2)
            cv_experiences.append({
                "experienceId": exp_id,
                "domain": getattr(exp, "Domain", None) or "",
                "expertise": getattr(exp, "Expertise", None) or "",
                "responsibility": getattr(exp, "Responsibility", None) or "",
                "years": years,
            })
    graph_sync.sync_cv_work_experiences_graph(cv_id, cv_experiences)

    return True


def sync_job_to_graph(db: Session, job_id: int) -> bool:
    """Sync the current JD schema to Neo4j without fabricating fake data."""
    jd = db.query(JD).filter(JD.Id == job_id).first()
    if jd is None:
        return False
    domain = jd.Domain.strip() if jd.Domain and jd.Domain.strip() else None
    expertise = jd.Expertise.strip() if jd.Expertise and jd.Expertise.strip() else None

    # Tự động suy luận Domain & Expertise từ chức danh nếu chưa có trong DB
    if not domain or not expertise:
        fb_domain, fb_expertise = get_domain_expertise_for_title(jd.Title or "")
        domain = domain or fb_domain
        expertise = expertise or fb_expertise

    # Upsert Domain & Expertise
    if domain:
        graph_sync.upsert_domain_node(name=domain)
    if expertise:
        graph_sync.upsert_expertise_node(name=expertise, domain_name=domain)

    vector = list(jd.VectorTitle) if jd.VectorTitle is not None else None
    graph_sync.upsert_job_position_node(
        job_id=jd.Id,
        title=jd.Title or "",
        min_experience=float(jd.Experience or 0),
        education_level=jd.Qualification or "",
        embedding=vector,
    )
    graph_sync.upsert_jd_node(
        jd_id=jd.Id,
        title=jd.Title or "",
        domain=domain,
        expertise=expertise,
        qualification=jd.Qualification or "",
        responsibility=jd.Responsibility or "",
        experience_years=jd.Experience or 0,
        raw_text=jd.RawText or "",
        clean_text=jd.CleanText or "",
        embedding=vector,
        vector_title=vector,
        vector_domain=list(jd.VectorDomain) if jd.VectorDomain is not None else None,
        vector_expertise=(
            list(jd.VectorExpertise) if jd.VectorExpertise is not None else None
        ),
        vector_qualification=(
            list(jd.VectorQualification) if jd.VectorQualification is not None else None
        ),
        vector_responsibility=(
            list(jd.VectorResponsibility)
            if jd.VectorResponsibility is not None
            else None
        ),
    )
    skills = []
    if jd.skills:
        for s in jd.skills:
            if s.Title and s.Title.strip():
                skills.append(
                    dict(
                        _skill_payload(s.Title),
                        requirementId=s.Id,
                        vector=list(s.Vector) if s.Vector is not None else None,
                        expertise=expertise,
                    )
                )
    graph_sync.sync_jd_skill_requirements_graph(
        job_id, skills, expertise_name=expertise
    )
    return True


def sync_all_from_postgres(db: Session) -> Dict[str, int]:
    """Sync real records without creating sample matching scores."""
    setup_knowledge_graph_schema()
    stats = {
        "users": 0,
        "skills": 0,
        "jobs": 0,
        "cvs": 0,
        "domains": 0,
        "expertises": 0,
        "educations": 0,
        "work_experiences": 0,
    }
    users = db.query(User).all()
    jobs = db.query(JD).all()
    profiles = db.query(Profile).all()
    for user in users:
        graph_sync.upsert_user_node(
            user_id=user.Id,
            email=user.Email,
            full_name=user.FullName or "",
            role=(
                user.Role.value
                if hasattr(user.Role, "value")
                else str(user.Role or "applicant")
            ),
        )
        stats["users"] += 1

    # Đồng bộ các node Skill thực tế từ PostgreSQL
    names = {
        s.SkillTitle
        for s in db.query(ProfileSkill).all()
        if s.SkillTitle and s.SkillTitle.strip()
    }
    names.update(
        s.Title for s in db.query(JDSkill).all() if s.Title and s.Title.strip()
    )
    for name in names:
        payload = _skill_payload(name)
        graph_sync.upsert_skill_node(skill_id=payload["skillId"], name=name)
        stats["skills"] += 1

    # Đồng bộ Domains & Expertises từ PostgreSQL JD
    synced_domains = set()
    synced_expertises = set()
    for jd in jobs:
        d_name = jd.Domain.strip() if jd.Domain and jd.Domain.strip() else None
        e_name = jd.Expertise.strip() if jd.Expertise and jd.Expertise.strip() else None
        if d_name and d_name not in synced_domains:
            graph_sync.upsert_domain_node(name=d_name)
            synced_domains.add(d_name)
            stats["domains"] += 1
        if e_name and e_name not in synced_expertises:
            graph_sync.upsert_expertise_node(name=e_name, domain_name=d_name)
            synced_expertises.add(e_name)
            stats["expertises"] += 1

    for jd in jobs:
        stats["jobs"] += int(sync_job_to_graph(db, jd.Id))
    for profile in profiles:
        stats["cvs"] += int(sync_cv_to_graph(db, profile.Id))
        stats["educations"] += len(profile.educations) if profile.educations else 0
        stats["work_experiences"] += len(profile.work_experiences) if profile.work_experiences else 0
    graph_sync.prune_deleted_records_graph(
        [p.Id for p in profiles], [j.Id for j in jobs], [u.Id for u in users]
    )
    return stats


def calculate_cv_jd_matching_service(
    db: Session, cv_id: int, jd_id: int, weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    BÀI TOÁN 1: SKILL MATCHING (1 CV vs 1 JD) -> Trả về 1 số thực float trong [0, 1].
    Trả lời câu hỏi: 'CV của tôi có phù hợp để apply vào job tôi đang muốn ứng tuyển hay không?'
    Tính toán mức độ tương hợp kết hợp Cosine Similarity đa khía cạnh (Domain, Expertise, Skill, Experience, Qualification)
    và Knowledge Graph Skill Gap.
    """
    cv_record = db.query(Profile).filter(Profile.Id == cv_id).first()
    jd_record = db.query(JD).filter(JD.Id == jd_id).first()
    if not cv_record or not jd_record:
        return {"error": "Không tìm thấy thông tin CV hoặc JD tương ứng"}

    # Đảm bảo đồng bộ lên Neo4j
    sync_cv_to_graph(db, cv_id)
    sync_job_to_graph(db, jd_id)

    # 1. Phân tích đồ thị Knowledge Graph (Skill Gap)
    gap_data = graph_match.analyze_skill_gap_graph(cv_id, jd_id)
    graph_coverage = float(gap_data.get("skillCoverageRatio", 0.0))

    # 2. Tính Vector Similarity từng khía cạnh
    cv_vec = _profile_vector(cv_record)

    # Lấy vector kỹ năng CV
    cv_skill_vec = _mean_vector(item.Vector for item in cv_record.skills)

    # Lấy vector kinh nghiệm CV
    cv_exp_vec = _mean_vector(item.Vector for item in cv_record.work_experiences)

    # Lấy vector học vấn CV
    cv_edu_vec = _mean_vector(item.Vector for item in cv_record.educations)

    # Sub-scores
    # Skill Score: kết hợp độ phủ đồ thị và vector kỹ năng
    jd_skill_vec = _mean_vector(item.Vector for item in jd_record.skills)
    vec_skill_sim = compute_cosine_similarity(cv_skill_vec or cv_vec, jd_skill_vec)
    skill_score = round(
        0.60 * graph_coverage
        + 0.40 * (vec_skill_sim if vec_skill_sim > 0 else graph_coverage),
        4,
    )

    # Domain Score
    jd_domain_vec = (
        list(jd_record.VectorDomain)
        if getattr(jd_record, "VectorDomain", None) is not None
        else None
    )
    domain_score = compute_cosine_similarity(cv_exp_vec or cv_vec, jd_domain_vec)

    # Expertise Score
    jd_exp_vec = (
        list(jd_record.VectorExpertise)
        if getattr(jd_record, "VectorExpertise", None) is not None
        else None
    )
    expertise_score = compute_cosine_similarity(cv_exp_vec or cv_vec, jd_exp_vec)

    # Experience Score (so sánh kinh nghiệm thực tế từ ProfileWorkExp, không dùng giá trị giả)
    jd_min_exp = float(
        getattr(jd_record, "Experience", 0)
        or getattr(jd_record, "MinExperience", 0)
        or 0.0
    )
    cand_exp = _experience_years(getattr(cv_record, "work_experiences", None) or [])
    experience_score = (
        1.0 if jd_min_exp == 0 else min(1.0, max(0.0, round(cand_exp / jd_min_exp, 4)))
    )

    # Qualification Score
    jd_qual_vec = (
        list(jd_record.VectorQualification)
        if getattr(jd_record, "VectorQualification", None) is not None
        else None
    )
    qualification_score = compute_cosine_similarity(cv_edu_vec, jd_qual_vec)

    # 3. Trọng số tổng hợp (Weighted Fusion)
    w = weights or {
        "skill": 0.40,
        "domain": 0.20,
        "expertise": 0.20,
        "experience": 0.10,
        "qualification": 0.10,
    }
    total_result = round(
        w.get("skill", 0.40) * skill_score
        + w.get("domain", 0.20) * domain_score
        + w.get("expertise", 0.20) * expertise_score
        + w.get("experience", 0.10) * experience_score
        + w.get("qualification", 0.10) * qualification_score,
        4,
    )
    total_result = max(0.0, min(1.0, total_result))

    scores = {
        "totalResult": total_result,
        "skillScore": skill_score,
        "domainScore": domain_score,
        "expertiseScore": expertise_score,
        "experienceScore": experience_score,
        "qualificationScore": qualification_score,
    }

    # 4. Lưu quan hệ MATCHES_JD vào Knowledge Graph
    graph_match.save_cv_jd_match_result_graph(cv_id, jd_id, scores)

    # 5. Giải thích tính phù hợp
    is_suitable = total_result >= 0.65
    explanation = (
        f"CV có độ phù hợp {total_result * 100:.1f}% đối với vị trí {jd_record.Title}. "
        f"Kỹ năng đáp ứng {gap_data.get('totalMatchedSkills', 0)}/{gap_data.get('totalRequiredSkills', 0)} yêu cầu cốt lõi. "
        + (
            "Rất phù hợp để nộp đơn ứng tuyển!"
            if is_suitable
            else "Nên bổ sung thêm kỹ năng còn thiếu trước khi ứng tuyển."
        )
    )

    return {
        "cvId": cv_id,
        "jdId": jd_id,
        "jobTitle": jd_record.Title,
        "totalResult": total_result,
        "isSuitable": is_suitable,
        "scores": scores,
        "skillGap": gap_data,
        "explanation": explanation,
    }


def hybrid_search_candidates_service(
    db: Session, job_id: int, top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Dịch vụ tìm kiếm và xếp hạng ứng viên kết hợp Vector + Knowledge Graph.
    """
    job_record = db.query(JD).filter(JD.Id == job_id).first()
    if not job_record:
        return []

    job_vector = (
        list(job_record.VectorTitle) if job_record.VectorTitle is not None else None
    )

    # Đảm bảo Job đã lên graph
    sync_job_to_graph(db, job_id)

    results = graph_match.hybrid_match_cvs_for_job_graph(
        job_id=job_id, job_vector=job_vector, top_k=top_k
    )
    profile_ids = [item.get("cvId") for item in results if item.get("cvId") is not None]
    titles = dict(
        db.query(Profile.Id, Profile.Title)
        .filter(Profile.Id.in_(profile_ids))
        .all()
    ) if profile_ids else {}
    for item in results:
        item["candidateTitle"] = titles.get(item.get("cvId")) or f"CV #{item.get('cvId')}"
    return results
