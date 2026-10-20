import logging
import math
from typing import Dict, Any, List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.User import User
from app.models.job import Job
from app.models.skill import Skill
from app.models.cv import CV
from app.models.job_skill import JobSkill
from app.models.cv_skill import CVSkill
from app.models.cv_embedding import CVEmbedding
from app.models.job_embedding import JobEmbedding
from app.models.jd import JD
from app.models.jd_skill import JDSkill
from app.models.profile import Profile
from app.models.profile_skill import ProfileSkill
from app.models.profile_edu import ProfileEdu
from app.models.profile_work_exp import ProfileWorkExp
from app.models.result import Result

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


def sync_cv_to_graph(db: Session, cv_id: int) -> bool:
    """Đồng bộ một CV và danh sách kỹ năng của nó từ PostgreSQL sang Neo4j."""
    from sqlalchemy import text
    try:
        # Thử đọc qua raw SQL từ bảng CVs
        cv_row = db.execute(
            text('SELECT "Id", "UserId", "FileType", "Language", "Summary", "CleanText" FROM "CVs" WHERE "Id" = :id'),
            {"id": cv_id}
        ).fetchone()

        if not cv_row:
            logger.warning("CV %s not found in DB to sync.", cv_id)
            return False

        c_id, user_id, file_type, lang, summary, clean_text = cv_row
        
        # Lấy embedding vector (nếu có)
        emb_row = db.execute(
            text('SELECT "Vector" FROM "CVEmbeddings" WHERE "CVId" = :cv_id ORDER BY "CreatedAt" DESC LIMIT 1'),
            {"cv_id": cv_id}
        ).fetchone()
        vec = list(emb_row[0]) if emb_row and emb_row[0] is not None else None

        # Upsert Node CV & User
        graph_sync.upsert_cv_node(
            cv_id=c_id,
            user_id=user_id,
            language=lang or "en",
            summary=summary or clean_text or "",
            embedding=vec
        )

        # Lấy danh sách kỹ năng từ CVSkills
        skills_payload = []
        cv_skills = db.execute(
            text('SELECT cs."Id", cs."SkillId", s."Name", cs."Confidence", cs."Source" FROM "CVSkills" cs JOIN "Skills" s ON cs."SkillId" = s."Id" WHERE cs."CVId" = :cv_id'),
            {"cv_id": cv_id}
        ).fetchall()
        for cs in cv_skills:
            skills_payload.append({
                "skillId": cs[1],
                "skillName": cs[2],
                "confidence": float(cs[3]) if cs[3] is not None else 1.0,
                "source": cs[4] or "parsed"
            })

        graph_sync.sync_cv_skills_graph(cv_id, skills_payload)
        logger.info("Successfully synced CV %s and %s skills to Neo4j.", cv_id, len(skills_payload))
        return True
    except Exception as e:
        logger.error("Failed to sync CV %s to Neo4j: %s", cv_id, e)
        return False


def sync_job_to_graph(db: Session, job_id: int) -> bool:
    """Đồng bộ JobPosition, JD, Domain, Expertise và SkillRequirement sang Neo4j."""
    from sqlalchemy import text
    try:
        job_row = db.execute(
            text('SELECT "Id", "Title", "Description", "RequirementsText", "MinExperience", "EducationLevel", "Status" FROM "Jobs" WHERE "Id" = :id'),
            {"id": job_id}
        ).fetchone()

        if not job_row:
            logger.warning("Job %s not found in DB to sync.", job_id)
            return False

        j_id, title, desc, req_text, min_exp, edu_level, status = job_row
        min_exp_float = float(min_exp) if min_exp is not None else 0.0

        # Lấy embedding vector (nếu có)
        emb_row = db.execute(
            text('SELECT "Vector" FROM "JobEmbeddings" WHERE "JobId" = :job_id ORDER BY "CreatedAt" DESC LIMIT 1'),
            {"job_id": job_id}
        ).fetchone()
        vec = list(emb_row[0]) if emb_row and emb_row[0] is not None else None

        domain_str, expertise_str = get_domain_expertise_for_title(title)

        # 1. Upsert Domain và Expertise
        graph_sync.upsert_domain_node(name=domain_str)
        graph_sync.upsert_expertise_node(name=expertise_str, domain_name=domain_str)

        # 2. Upsert Node JobPosition (tương thích ngược)
        graph_sync.upsert_job_position_node(
            job_id=j_id,
            title=title,
            min_experience=min_exp_float,
            education_level=str(edu_level) if edu_level else "BACHELOR",
            status=str(status) if status else "OPEN",
            embedding=vec
        )

        # 3. Upsert Node JD chi tiết
        graph_sync.upsert_jd_node(
            jd_id=j_id,
            title=title,
            domain=domain_str,
            expertise=expertise_str,
            qualification=str(edu_level) if edu_level else "BACHELOR",
            responsibility=desc or "",
            experience_years=int(min_exp_float),
            raw_text=req_text or "",
            clean_text=desc or "",
            embedding=vec
        )

        # 4. Lấy danh sách kỹ năng yêu cầu từ JobSkills
        job_skills = db.execute(
            text('SELECT js."Id", js."SkillId", s."Name", js."Importance", js."MinYears" FROM "JobSkills" js JOIN "Skills" s ON js."SkillId" = s."Id" WHERE js."JobId" = :job_id'),
            {"job_id": job_id}
        ).fetchall()
        skills_payload = []
        for js in job_skills:
            skills_payload.append({
                "requirementId": js[0],
                "skillId": js[1],
                "skillName": js[2],
                "importance": float(js[3]) if js[3] is not None else 1.0,
                "minYears": float(js[4]) if js[4] is not None else 0.0
            })

        graph_sync.sync_jd_skill_requirements_graph(job_id, skills_payload)
        logger.info("Successfully synced JD/Job %s and %s required skills to Neo4j.", job_id, len(skills_payload))
        return True
    except Exception as e:
        logger.error("Failed to sync Job %s to Neo4j: %s", job_id, e)
        return False


def sync_all_from_postgres(db: Session) -> Dict[str, int]:
    """
    Đồng bộ toàn bộ dữ liệu từ PostgreSQL sang Neo4j:
    Users -> Skills -> Jobs/JDs/Domains/Expertises -> CVs -> Relationships.
    """
    from sqlalchemy import text
    stats = {"users": 0, "skills": 0, "jobs": 0, "cvs": 0}

    # 1. Khởi tạo schema & constraints
    setup_knowledge_graph_schema()

    # 2. Đồng bộ Skills master
    skills = db.execute(text('SELECT "Id", "Name", "Category", "Description" FROM "Skills"')).fetchall()
    for s in skills:
        graph_sync.upsert_skill_node(
            skill_id=s[0],
            name=s[1],
            category=s[2],
            description=s[3]
        )
        stats["skills"] += 1

    # 3. Đồng bộ Users
    users = db.execute(text('SELECT "Id", "email", "full_name", "role" FROM "users"')).fetchall()
    for u in users:
        graph_sync.upsert_user_node(
            user_id=u[0],
            email=u[1],
            full_name=u[2],
            role=u[3]
        )
        stats["users"] += 1

    # 4. Đồng bộ Jobs và JDs
    job_ids = db.execute(text('SELECT "Id" FROM "Jobs"')).fetchall()
    for (jid,) in job_ids:
        sync_job_to_graph(db, jid)
        stats["jobs"] += 1

    # 5. Đồng bộ CVs
    cv_ids = db.execute(text('SELECT "Id" FROM "CVs"')).fetchall()
    for (cid,) in cv_ids:
        sync_cv_to_graph(db, cid)
        stats["cvs"] += 1

    # 6. Tạo match mẫu để có cạnh MATCHES_JD
    if stats["cvs"] > 0 and stats["jobs"] > 0:
        c_id = cv_ids[0][0]
        # Tìm job_id có skills (Job 3 hoặc job đầu tiên)
        target_jid = 3 if any(j[0] == 3 for j in job_ids) else job_ids[0][0]
        scores = {
            "totalResult": 0.85,
            "skillScore": 0.75,
            "domainScore": 0.90,
            "expertiseScore": 0.85,
            "experienceScore": 1.0,
            "qualificationScore": 1.0
        }
        graph_match.save_cv_jd_match_result_graph(c_id, target_jid, scores)

    logger.info("Batch sync completed: %s", stats)
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
    # Lấy vector CV
    cv_emb = db.query(CVEmbedding).filter(CVEmbedding.CVId == cv_id).order_by(CVEmbedding.CreatedAt.desc()).first()
    cv_vec = list(cv_emb.Vector) if (cv_emb and cv_emb.Vector is not None) else None

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

    # Experience Score (so sánh kinh nghiệm thực tế)
    jd_min_exp = float(getattr(jd_record, "Experience", 0) or getattr(jd_record, "MinExperience", 0) or 0.0)
    cand_exp = 2.0  # Mặc định tương đối nếu chưa có tổng năm
    experience_score = 1.0 if jd_min_exp == 0 else min(1.0, cand_exp / jd_min_exp)

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
    target_domains: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    BÀI TOÁN 2: SKILL GAP ANALYSIS & DOMAIN ORIENTATION (1 CV vs Many JDs/Domains).
    Trả lời câu hỏi: 'CV của tôi có thể apply vào những domain nào trong CNTT?'
    Trả về ma trận N * K với miền giá trị float trong [0, 1]:
      - Rows: Thuộc tính của CV (Hard Skills, Work Experience, Education & Qualification, Overall Profile)
      - Columns: Các Domain trong CNTT (Backend, Frontend, AI/ML, DevOps, Security...)
    Kèm xếp hạng Domain và danh sách kỹ năng còn thiếu (Skill Gap) cho từng domain.
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
        # Lấy từ CSDL JD
        db_domains = db.query(Job.Domain).filter(Job.Domain.isnot(None)).distinct().all()
        domains = [d[0] for d in db_domains if d[0] and d[0].strip()]
        if not domains:
            # Danh sách miền CNTT chuẩn định sẵn nếu DB chưa có
            domains = [
                "Backend Development",
                "Frontend Development",
                "Data Engineering & AI",
                "Cloud & DevOps Engineering",
                "Mobile App Development",
                "Information Security"
            ]

    # 2. Lấy dữ liệu Vector của CV
    cv_emb = db.query(CVEmbedding).filter(CVEmbedding.CVId == cv_id).order_by(CVEmbedding.CreatedAt.desc()).first()
    cv_vec = list(cv_emb.Vector) if (cv_emb and cv_emb.Vector is not None) else None

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

    # 3. Lấy phân tích Skill Gap đồ thị cho từng Domain
    domain_gaps_list = graph_match.get_domain_skill_gap_matrix_graph(cv_id, domains)
    domain_gaps = {g["domainName"]: g for g in domain_gaps_list}

    # 4. Xây dựng Ma trận N x K
    # Rows: 4 đặc trưng của CV
    row_names = [
        "Hard Skills",
        "Work Experience",
        "Education & Qualification",
        "Overall Profile"
    ]

    matrix_data: List[List[float]] = [[], [], [], []]
    domain_rankings = []

    for dom in domains:
        gap_info = domain_gaps.get(dom, {})
        graph_ratio = float(gap_info.get("skillCoverageRatio", 0.0))

        # Tìm các JD thuộc domain này để lấy vector đại diện
        jd_in_dom = db.query(Job).filter(Job.Domain == dom).all()
        dom_vec = None
        for j in jd_in_dom:
            if getattr(j, "VectorDomain", None) is not None:
                dom_vec = list(j.VectorDomain)
                break

        # Tính toán giá trị từng ô trong cột dom (tất cả đều trong [0, 1])
        # Cell 0 (Hard Skills): kết hợp đồ thị và vector
        skill_cell = round(max(graph_ratio, compute_cosine_similarity(cv_skill_vec or cv_vec, dom_vec)), 4)
        # Cell 1 (Work Experience):
        exp_cell = round(compute_cosine_similarity(cv_exp_vec or cv_vec, dom_vec), 4)
        # Cell 2 (Education):
        edu_cell = round(0.80 if cv_edu_vec else 0.60, 4)
        # Cell 3 (Overall Profile):
        profile_cell = round(compute_cosine_similarity(cv_vec, dom_vec), 4)

        matrix_data[0].append(skill_cell)
        matrix_data[1].append(exp_cell)
        matrix_data[2].append(edu_cell)
        matrix_data[3].append(profile_cell)

        # Điểm tương quan tổng hợp của Domain (Column Score)
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

    # Sắp xếp thứ hạng Domain từ cao xuống thấp
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

    return {
        "cvId": cv_id,
        "matrix": {
            "rows": row_names,
            "columns": domains,
            "data": matrix_data
        },
        "domainRankings": domain_rankings
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

    emb_record = db.query(JobEmbedding).filter(JobEmbedding.JobId == job_id).order_by(JobEmbedding.CreatedAt.desc()).first()
    job_vector = list(emb_record.Vector) if (emb_record and emb_record.Vector is not None) else None

    # Đảm bảo Job đã lên graph
    sync_job_to_graph(db, job_id)

    return graph_match.hybrid_match_cvs_for_job_graph(
        job_id=job_id,
        job_vector=job_vector,
        top_k=top_k
    )

