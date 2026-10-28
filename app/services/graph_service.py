import logging
import math
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.User import User
from app.models.job import Job
from app.models.cv import CV
from app.models.jd import JD
from app.models.jd_skill import JDSkill
from app.models.profile import Profile
from app.models.profile_skill import ProfileSkill

from app.crud.graph import schema as graph_schema
from app.crud.graph import sync_crud as graph_sync
from app.crud.graph import match_crud as graph_match

logger = logging.getLogger(__name__)


def compute_cosine_similarity(vec1: Optional[List[float]], vec2: Optional[List[float]]) -> float:
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
    "system administrator": ("Cloud & DevOps Engineering", "System & Network Administration"),
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


def _profile_vector(profile):
    vectors = [list(item.Vector) for group in (profile.skills, profile.work_experiences, profile.educations)
               for item in group if item.Vector is not None]
    if not vectors:
        return None
    return [sum(values) / len(vectors) for values in zip(*vectors)]


def _skill_payload(title):
    # Skill IDs are shared by normalized name across PROFILE_SKILL and JD_SKILL.
    from hashlib import sha256
    normalized = graph_sync.normalize_skill_name(title)
    return {"skillId": int.from_bytes(sha256(normalized.encode()).digest()[:7], "big"),
            "skillName": title}


def sync_cv_to_graph(db: Session, cv_id: int) -> bool:
    """Sync the current PROFILE schema to Neo4j without fabricating fake data."""
    profile = db.query(Profile).filter(Profile.Id == cv_id).first()
    if profile is None:
        return False
    graph_sync.upsert_cv_node(
        cv_id=profile.Id,
        user_id=profile.UserId,
        summary=profile.CleanText or profile.RawText or "",
        embedding=_profile_vector(profile)
    )
    cv_skills = []
    if profile.skills:
        for s in profile.skills:
            if s.SkillTitle and s.SkillTitle.strip():
                cv_skills.append(_skill_payload(s.SkillTitle))
    graph_sync.sync_cv_skills_graph(cv_id, cv_skills)
    return True


def sync_job_to_graph(db: Session, job_id: int) -> bool:
    """Sync the current JD schema to Neo4j without fabricating fake data."""
    jd = db.query(JD).filter(JD.Id == job_id).first()
    if jd is None:
        return False
    domain = jd.Domain.strip() if jd.Domain and jd.Domain.strip() else None
    expertise = jd.Expertise.strip() if jd.Expertise and jd.Expertise.strip() else None

    # Chỉ upsert Domain & Expertise khi có dữ liệu thực tế trong DB
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
        embedding=vector
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
        vector_expertise=list(jd.VectorExpertise) if jd.VectorExpertise is not None else None,
        vector_qualification=list(jd.VectorQualification) if jd.VectorQualification is not None else None,
        vector_responsibility=list(jd.VectorResponsibility) if jd.VectorResponsibility is not None else None,
    )
    skills = []
    if jd.skills:
        for s in jd.skills:
            if s.Title and s.Title.strip():
                skills.append(dict(
                    _skill_payload(s.Title),
                    requirementId=s.Id,
                    vector=list(s.Vector) if s.Vector is not None else None,
                    expertise=expertise
                ))
    graph_sync.sync_jd_skill_requirements_graph(job_id, skills, expertise_name=expertise)
    return True


def sync_all_from_postgres(db: Session) -> Dict[str, int]:
    """Sync real records without creating sample matching scores."""
    setup_knowledge_graph_schema()
    stats = {"users": 0, "skills": 0, "jobs": 0, "cvs": 0, "domains": 0, "expertises": 0}
    for user in db.query(User).all():
        graph_sync.upsert_user_node(
            user_id=user.Id,
            email=user.Email,
            full_name=user.FullName or "",
            role=user.Role.value if hasattr(user.Role, "value") else str(user.Role or "applicant")
        )
        stats["users"] += 1

    # Đồng bộ các node Skill thực tế từ PostgreSQL
    names = {s.SkillTitle for s in db.query(ProfileSkill).all() if s.SkillTitle and s.SkillTitle.strip()}
    names.update(s.Title for s in db.query(JDSkill).all() if s.Title and s.Title.strip())
    for name in names:
        payload = _skill_payload(name)
        graph_sync.upsert_skill_node(skill_id=payload["skillId"], name=name)
        stats["skills"] += 1

    # Đồng bộ Domains & Expertises từ PostgreSQL JD
    synced_domains = set()
    synced_expertises = set()
    for jd in db.query(JD).all():
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

    for jd in db.query(JD).all():
        stats["jobs"] += int(sync_job_to_graph(db, jd.Id))
    for profile in db.query(Profile).all():
        stats["cvs"] += int(sync_cv_to_graph(db, profile.Id))
    return stats


def calculate_cv_jd_matching_service(
    db: Session,
    cv_id: int,
    jd_id: int,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    BÀI TOÁN 1: SKILL MATCHING (1 CV vs 1 JD) -> Trả về 1 số thực float trong [0, 1].
    Trả lời câu hỏi: 'CV của tôi có phù hợp để apply vào job tôi đang muốn ứng tuyển hay không?'
    Tính toán mức độ tương hợp kết hợp Cosine Similarity đa khía cạnh (Domain, Expertise, Skill, Experience, Qualification)
    và Knowledge Graph Skill Gap.
    """
    cv_record = db.query(CV).filter(CV.Id == cv_id).first()
    jd_record = db.query(Job).filter(Job.Id == jd_id).first()
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
    cv_skill_vec = None
    if hasattr(cv_record, "skills") and cv_record.skills:
        for ps in cv_record.skills:
            if getattr(ps, "Vector", None) is not None:
                cv_skill_vec = list(ps.Vector)
                break

    # Lấy vector kinh nghiệm CV
    cv_exp_vec = None
    if hasattr(cv_record, "work_experiences") and cv_record.work_experiences:
        for we in cv_record.work_experiences:
            if getattr(we, "Vector", None) is not None:
                cv_exp_vec = list(we.Vector)
                break

    # Lấy vector học vấn CV
    cv_edu_vec = None
    if hasattr(cv_record, "educations") and cv_record.educations:
        for edu in cv_record.educations:
            if getattr(edu, "Vector", None) is not None:
                cv_edu_vec = list(edu.Vector)
                break

    # Sub-scores
    # Skill Score: kết hợp độ phủ đồ thị và vector kỹ năng
    jd_skill_vec = None
    if hasattr(jd_record, "skills") and jd_record.skills:
        for js in jd_record.skills:
            if getattr(js, "Vector", None) is not None:
                jd_skill_vec = list(js.Vector)
                break
    vec_skill_sim = compute_cosine_similarity(cv_skill_vec or cv_vec, jd_skill_vec)
    skill_score = round(0.60 * graph_coverage + 0.40 * (vec_skill_sim if vec_skill_sim > 0 else graph_coverage), 4)

    # Domain Score
    jd_domain_vec = list(jd_record.VectorDomain) if getattr(jd_record, "VectorDomain", None) is not None else None
    domain_score = compute_cosine_similarity(cv_exp_vec or cv_vec, jd_domain_vec)

    # Expertise Score
    jd_exp_vec = list(jd_record.VectorExpertise) if getattr(jd_record, "VectorExpertise", None) is not None else None
    expertise_score = compute_cosine_similarity(cv_exp_vec or cv_vec, jd_exp_vec)

    # Experience Score (so sánh kinh nghiệm thực tế từ ProfileWorkExp, không dùng giá trị giả)
    jd_min_exp = float(getattr(jd_record, "Experience", 0) or getattr(jd_record, "MinExperience", 0) or 0.0)
    cand_exp = 0.0
    if hasattr(cv_record, "work_experiences") and cv_record.work_experiences:
        for we in cv_record.work_experiences:
            start = getattr(we, "StartDate", None)
            end = getattr(we, "EndDate", None)
            if start:
                from datetime import date
                end_date = end or date.today()
                days = (end_date - start).days
                if days > 0:
                    cand_exp += days / 365.25
    experience_score = 1.0 if jd_min_exp == 0 else min(1.0, max(0.0, round(cand_exp / jd_min_exp, 4)))

    # Qualification Score
    jd_qual_vec = list(jd_record.VectorQualification) if getattr(jd_record, "VectorQualification", None) is not None else None
    qualification_score = compute_cosine_similarity(cv_edu_vec or cv_vec, jd_qual_vec)

    # 3. Trọng số tổng hợp (Weighted Fusion)
    w = weights or {
        "skill": 0.40,
        "domain": 0.20,
        "expertise": 0.20,
        "experience": 0.10,
        "qualification": 0.10
    }
    total_result = round(
        w.get("skill", 0.40) * skill_score +
        w.get("domain", 0.20) * domain_score +
        w.get("expertise", 0.20) * expertise_score +
        w.get("experience", 0.10) * experience_score +
        w.get("qualification", 0.10) * qualification_score,
        4
    )
    total_result = max(0.0, min(1.0, total_result))

    scores = {
        "totalResult": total_result,
        "skillScore": skill_score,
        "domainScore": domain_score,
        "expertiseScore": expertise_score,
        "experienceScore": experience_score,
        "qualificationScore": qualification_score
    }

    # 4. Lưu quan hệ MATCHES_JD vào Knowledge Graph
    graph_match.save_cv_jd_match_result_graph(cv_id, jd_id, scores)

    # 5. Giải thích tính phù hợp
    is_suitable = total_result >= 0.65
    explanation = (
        f"CV có độ phù hợp {total_result * 100:.1f}% đối với vị trí {jd_record.Title}. "
        f"Kỹ năng đáp ứng {gap_data.get('totalMatchedSkills', 0)}/{gap_data.get('totalRequiredSkills', 0)} yêu cầu cốt lõi. "
        + ("Rất phù hợp để nộp đơn ứng tuyển!" if is_suitable else "Nên bổ sung thêm kỹ năng còn thiếu trước khi ứng tuyển.")
    )

    return {
        "cvId": cv_id,
        "jdId": jd_id,
        "jobTitle": jd_record.Title,
        "totalResult": total_result,
        "isSuitable": is_suitable,
        "scores": scores,
        "skillGap": gap_data,
        "explanation": explanation
    }


def calculate_domain_skill_gap_matrix_service(
    db: Session,
    cv_id: int,
    target_domains: Optional[List[str]] = None,
    target_expertises: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    BÀI TOÁN 2: SKILL GAP ANALYSIS & DOMAIN / EXPERTISE ORIENTATION (1 CV vs Many JDs/Domains/Expertises).
    Trả lời câu hỏi: 'CV của tôi có thể apply vào những domain/expertise nào trong CNTT?'
    Trả về ma trận N * K với miền giá trị float trong [0, 1]:
      - Rows: Thuộc tính của CV (Hard Skills, Work Experience, Education & Qualification, Overall Profile)
      - Columns: Các Domain và Expertise trong hệ thống
    Hỗ trợ nhiều JD trong một Domain/Expertise, chống trùng lặp kỹ năng và trả dữ liệu ma trận
    CV Properties × (Expertise + Domain).
    """
    cv_record = db.query(CV).filter(CV.Id == cv_id).first()
    if not cv_record:
        return {"error": f"Không tìm thấy thông tin CV {cv_id}"}

    # Đảm bảo CV đã lên graph
    sync_cv_to_graph(db, cv_id)

    # 1. Lấy danh sách Domains từ hệ thống
    if target_domains and len(target_domains) > 0:
        domains = target_domains
    else:
        db_domains = db.query(Job.Domain).filter(Job.Domain.isnot(None)).distinct().all()
        domains = [d[0] for d in db_domains if d[0] and d[0].strip()]
        if not domains:
            domains = [
                "Backend Development",
                "Frontend Development",
                "Data Engineering & AI",
                "Cloud & DevOps Engineering",
                "Mobile App Development",
                "Information Security"
            ]

    # 2. Lấy danh sách Expertises từ hệ thống
    if target_expertises and len(target_expertises) > 0:
        expertises = target_expertises
    else:
        db_exp = db.query(Job.Expertise).filter(Job.Expertise.isnot(None)).distinct().all()
        expertises = [e[0] for e in db_exp if e[0] and e[0].strip()]
        if not expertises:
            client = graph_match.get_neo4j_client()
            res_e = client.execute_read("MATCH (e:Expertise) RETURN e.name AS name ORDER BY name")
            expertises = [r["name"] for r in res_e if r.get("name")]

    # 3. Lấy dữ liệu Vector của CV
    cv_vec = _profile_vector(cv_record)

    cv_skill_vec = None
    if hasattr(cv_record, "skills") and cv_record.skills:
        for ps in cv_record.skills:
            if getattr(ps, "Vector", None) is not None:
                cv_skill_vec = list(ps.Vector)
                break

    cv_exp_vec = None
    if hasattr(cv_record, "work_experiences") and cv_record.work_experiences:
        for we in cv_record.work_experiences:
            if getattr(we, "Vector", None) is not None:
                cv_exp_vec = list(we.Vector)
                break

    cv_edu_vec = None
    if hasattr(cv_record, "educations") and cv_record.educations:
        for edu in cv_record.educations:
            if getattr(edu, "Vector", None) is not None:
                cv_edu_vec = list(edu.Vector)
                break

    # 4. Phân tích Skill Gap cho Domain
    domain_gaps_list = graph_match.get_domain_skill_gap_matrix_graph(cv_id, domains)
    domain_gaps = {g["domainName"]: g for g in domain_gaps_list}

    row_names = [
        "Hard Skills",
        "Work Experience",
        "Education & Qualification",
        "Overall Profile"
    ]

    domain_matrix_data: List[List[float]] = [[], [], [], []]
    domain_rankings = []

    for dom in domains:
        gap_info = domain_gaps.get(dom, {})
        graph_ratio = float(gap_info.get("skillCoverageRatio", 0.0))

        jd_in_dom = db.query(Job).filter(Job.Domain == dom).all()
        dom_vec = None
        for j in jd_in_dom:
            if getattr(j, "VectorDomain", None) is not None:
                dom_vec = list(j.VectorDomain)
                break

        skill_cell = round(max(graph_ratio, compute_cosine_similarity(cv_skill_vec or cv_vec, dom_vec)), 4)
        exp_cell = round(compute_cosine_similarity(cv_exp_vec or cv_vec, dom_vec), 4)
        edu_cell = round(0.80 if cv_edu_vec else 0.60, 4)
        profile_cell = round(compute_cosine_similarity(cv_vec, dom_vec), 4)

        domain_matrix_data[0].append(skill_cell)
        domain_matrix_data[1].append(exp_cell)
        domain_matrix_data[2].append(edu_cell)
        domain_matrix_data[3].append(profile_cell)

        col_score = round(0.40 * skill_cell + 0.30 * exp_cell + 0.15 * edu_cell + 0.15 * profile_cell, 4)

        domain_rankings.append({
            "domain": dom,
            "compatibilityScore": col_score,
            "skillCoverageRatio": graph_ratio,
            "matchedSkillsCount": gap_info.get("totalMatchedSkills", 0),
            "missingSkillsCount": gap_info.get("totalMissingSkills", 0),
            "missingSkills": [s["name"] for s in gap_info.get("missingSkills", [])[:5]],
            "matchedSkills": [s["name"] for s in gap_info.get("matchedSkills", [])[:5]]
        })

    domain_rankings.sort(key=lambda x: x["compatibilityScore"], reverse=True)
    for idx, item in enumerate(domain_rankings):
        item["rank"] = idx + 1
        score_pct = item["compatibilityScore"] * 100
        if item["missingSkillsCount"] > 0:
            item["careerGuidance"] = (
                f"Độ tương thích {score_pct:.1f}%. Để gia nhập domain này, bạn nên ưu tiên trau dồi các kỹ năng: "
                f"{', '.join(item['missingSkills'])}."
            )
        else:
            item["careerGuidance"] = f"Độ tương thích xuất sắc ({score_pct:.1f}%). Hồ sơ đáp ứng rất tốt cho domain này."

    # 5. Phân tích Skill Gap cho Expertise
    expertise_matrix_data: List[List[float]] = [[], [], [], []]
    expertise_rankings = []

    if expertises:
        exp_gaps_list = graph_match.get_expertise_skill_gap_matrix_graph(cv_id, expertises)
        exp_gaps = {g["expertiseName"]: g for g in exp_gaps_list}

        for exp in expertises:
            gap_info = exp_gaps.get(exp, {})
            graph_ratio = float(gap_info.get("skillCoverageRatio", 0.0))

            jd_in_exp = db.query(Job).filter(Job.Expertise == exp).all()
            exp_vec = None
            for j in jd_in_exp:
                if getattr(j, "VectorExpertise", None) is not None:
                    exp_vec = list(j.VectorExpertise)
                    break

            skill_cell = round(max(graph_ratio, compute_cosine_similarity(cv_skill_vec or cv_vec, exp_vec)), 4)
            exp_cell = round(compute_cosine_similarity(cv_exp_vec or cv_vec, exp_vec), 4)
            edu_cell = round(0.80 if cv_edu_vec else 0.60, 4)
            profile_cell = round(compute_cosine_similarity(cv_vec, exp_vec), 4)

            expertise_matrix_data[0].append(skill_cell)
            expertise_matrix_data[1].append(exp_cell)
            expertise_matrix_data[2].append(edu_cell)
            expertise_matrix_data[3].append(profile_cell)

            col_score = round(0.40 * skill_cell + 0.30 * exp_cell + 0.15 * edu_cell + 0.15 * profile_cell, 4)

            expertise_rankings.append({
                "expertise": exp,
                "domain": gap_info.get("domainName", ""),
                "compatibilityScore": col_score,
                "skillCoverageRatio": graph_ratio,
                "matchedSkillsCount": gap_info.get("totalMatchedSkills", 0),
                "missingSkillsCount": gap_info.get("totalMissingSkills", 0),
                "missingSkills": [s["name"] for s in gap_info.get("missingSkills", [])[:5]],
                "matchedSkills": [s["name"] for s in gap_info.get("matchedSkills", [])[:5]]
            })

        expertise_rankings.sort(key=lambda x: x["compatibilityScore"], reverse=True)
        for idx, item in enumerate(expertise_rankings):
            item["rank"] = idx + 1
            score_pct = item["compatibilityScore"] * 100
            if item["missingSkillsCount"] > 0:
                item["careerGuidance"] = (
                    f"Độ tương thích {score_pct:.1f}%. Để đạt chuẩn chuyên môn này, cần bổ sung: "
                    f"{', '.join(item['missingSkills'])}."
                )
            else:
                item["careerGuidance"] = f"Độ tương thích xuất sắc ({score_pct:.1f}%). Rất phù hợp với chuyên môn này."

    # 6. Hợp nhất Ma trận CV Properties × (Expertise + Domain)
    all_columns = domains + expertises
    combined_matrix_data = [
        domain_matrix_data[0] + expertise_matrix_data[0],
        domain_matrix_data[1] + expertise_matrix_data[1],
        domain_matrix_data[2] + expertise_matrix_data[2],
        domain_matrix_data[3] + expertise_matrix_data[3],
    ]

    return {
        "cvId": cv_id,
        "matrix": {
            "rows": row_names,
            "columns": all_columns,
            "columnTypes": ["domain"] * len(domains) + ["expertise"] * len(expertises),
            "data": combined_matrix_data
        },
        "domainMatrix": {
            "rows": row_names,
            "columns": domains,
            "data": domain_matrix_data
        },
        "expertiseMatrix": {
            "rows": row_names,
            "columns": expertises,
            "data": expertise_matrix_data
        },
        "domainRankings": domain_rankings,
        "expertiseRankings": expertise_rankings
    }



def get_skill_gap_analysis_service(db: Session, cv_id: int, job_id: int) -> Dict[str, Any]:
    """
    Dịch vụ phân tích khoảng cách kỹ năng (Skill Gap Analysis) có giải thích chi tiết.
    Tự động đồng bộ nếu dữ liệu chưa có trên đồ thị.
    """
    cv_record = db.query(CV).filter(CV.Id == cv_id).first()
    job_record = db.query(Job).filter(Job.Id == job_id).first()
    if not cv_record or not job_record:
        return {"error": "CV hoặc Job không tồn tại"}

    # Đồng bộ nhanh nếu cần
    sync_cv_to_graph(db, cv_id)
    sync_job_to_graph(db, job_id)

    # Chạy phân tích đồ thị
    gap_data = graph_match.analyze_skill_gap_graph(cv_id, job_id)

    missing_names = [s["name"] for s in gap_data.get("missingSkills", [])]
    matched_names = [s["name"] for s in gap_data.get("matchedSkills", [])]
    coverage = gap_data.get("skillCoverageRatio", 0.0)

    explanation = []
    if coverage >= 0.8:
        explanation.append(f"Ứng viên có độ phù hợp kỹ năng xuất sắc ({coverage * 100:.1f}%), đáp ứng hầu hết yêu cầu cốt lõi.")
    elif coverage >= 0.5:
        explanation.append(f"Ứng viên đáp ứng mức khá ({coverage * 100:.1f}%). Cần đào tạo thêm một số kỹ năng để hoàn thiện.")
    else:
        explanation.append(f"Khoảng cách kỹ năng đáng kể ({coverage * 100:.1f}%). Thiếu nhiều kỹ năng quan trọng của vị trí.")

    recommendation = []
    if missing_names:
        recommendation.append(f"Để nâng cao khả năng trúng tuyển, ứng viên nên ưu tiên học thêm: {', '.join(missing_names[:5])}.")

    gap_data["jobTitle"] = job_record.Title
    gap_data["explanation"] = " ".join(explanation)
    gap_data["recommendation"] = " ".join(recommendation)
    return gap_data


def hybrid_search_candidates_service(db: Session, job_id: int, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Dịch vụ tìm kiếm và xếp hạng ứng viên kết hợp Vector + Knowledge Graph.
    """
    job_record = db.query(Job).filter(Job.Id == job_id).first()
    if not job_record:
        return []

    job_vector = list(job_record.VectorTitle) if job_record.VectorTitle is not None else None

    # Đảm bảo Job đã lên graph
    sync_job_to_graph(db, job_id)

    return graph_match.hybrid_match_cvs_for_job_graph(
        job_id=job_id,
        job_vector=job_vector,
        top_k=top_k
    )

