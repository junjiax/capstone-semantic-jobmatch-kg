import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.User import User
from app.models.job import Job
from app.models.skill import Skill
from app.models.cv import CV
from app.models.job_skill import JobSkill
from app.models.cv_skill import CVSkill
from app.models.cv_embedding import CVEmbedding
from app.models.job_embedding import JobEmbedding

from app.crud.graph import schema as graph_schema
from app.crud.graph import sync_crud as graph_sync
from app.crud.graph import match_crud as graph_match

logger = logging.getLogger(__name__)


def setup_knowledge_graph_schema() -> Dict[str, Any]:
    """Khởi tạo schema (constraints, indexes, vector index) trên Neo4j."""
    return graph_schema.init_graph_schema()


def sync_cv_to_graph(db: Session, cv_id: int) -> bool:
    """Đồng bộ một CV và danh sách kỹ năng của nó từ PostgreSQL sang Neo4j."""
    try:
        cv_record = db.query(CV).filter(CV.Id == cv_id).first()
        if not cv_record:
            logger.warning("CV %s not found in DB to sync.", cv_id)
            return False

        # Lấy embedding vector (nếu có)
        emb_record = db.query(CVEmbedding).filter(CVEmbedding.CVId == cv_id).order_by(CVEmbedding.CreatedAt.desc()).first()
        vec = list(emb_record.Vector) if (emb_record and emb_record.Vector is not None) else None

        # Upsert Node CV & User
        graph_sync.upsert_cv_node(
            cv_id=cv_record.Id,
            user_id=cv_record.UserId,
            language=cv_record.Language or "en",
            summary=cv_record.Summary,
            embedding=vec
        )

        # Lấy danh sách kỹ năng
        cv_skills = db.query(CVSkill, Skill).join(Skill, CVSkill.SkillId == Skill.Id).filter(CVSkill.CVId == cv_id).all()
        skills_payload = []
        for cs, s in cv_skills:
            skills_payload.append({
                "skillId": s.Id,
                "skillName": s.Name,
                "confidence": float(cs.Confidence) if cs.Confidence is not None else 1.0,
                "source": cs.Source or "parsed"
            })

        graph_sync.sync_cv_skills_graph(cv_id, skills_payload)
        logger.info("Successfully synced CV %s and %s skills to Neo4j.", cv_id, len(skills_payload))
        return True
    except Exception as e:
        logger.error("Failed to sync CV %s to Neo4j: %s", cv_id, e)
        return False


def sync_job_to_graph(db: Session, job_id: int) -> bool:
    """Đồng bộ một JobPosition và danh sách kỹ năng yêu cầu từ PostgreSQL sang Neo4j."""
    try:
        job_record = db.query(Job).filter(Job.Id == job_id).first()
        if not job_record:
            logger.warning("Job %s not found in DB to sync.", job_id)
            return False

        # Lấy embedding vector (nếu có)
        emb_record = db.query(JobEmbedding).filter(JobEmbedding.JobId == job_id).order_by(JobEmbedding.CreatedAt.desc()).first()
        vec = list(emb_record.Vector) if (emb_record and emb_record.Vector is not None) else None

        # Upsert Node JobPosition
        graph_sync.upsert_job_position_node(
            job_id=job_record.Id,
            title=job_record.Title,
            min_experience=float(job_record.MinExperience) if job_record.MinExperience is not None else 0.0,
            education_level=job_record.EducationLevel.value if job_record.EducationLevel else "BACHELOR",
            status=job_record.Status.value if job_record.Status else "OPEN",
            embedding=vec
        )

        # Lấy danh sách kỹ năng yêu cầu
        job_skills = db.query(JobSkill, Skill).join(Skill, JobSkill.SkillId == Skill.Id).filter(JobSkill.JobId == job_id).all()
        skills_payload = []
        for js, s in job_skills:
            skills_payload.append({
                "skillId": s.Id,
                "skillName": s.Name,
                "importance": float(js.Importance) if js.Importance is not None else 1.0,
                "minYears": float(js.MinYears) if js.MinYears is not None else 0.0
            })

        graph_sync.sync_job_skills_graph(job_id, skills_payload)
        logger.info("Successfully synced Job %s and %s required skills to Neo4j.", job_id, len(skills_payload))
        return True
    except Exception as e:
        logger.error("Failed to sync Job %s to Neo4j: %s", job_id, e)
        return False


def sync_all_from_postgres(db: Session) -> Dict[str, int]:
    """
    Đồng bộ toàn bộ dữ liệu từ PostgreSQL sang Neo4j:
    Users -> Skills -> Jobs -> CVs -> Relationships.
    """
    stats = {"users": 0, "skills": 0, "jobs": 0, "cvs": 0}

    # 1. Khởi tạo schema & constraints
    setup_knowledge_graph_schema()

    # 2. Đồng bộ Skills master
    skills = db.query(Skill).all()
    for s in skills:
        graph_sync.upsert_skill_node(
            skill_id=s.Id,
            name=s.Name,
            category=s.Category,
            description=s.Description
        )
        stats["skills"] += 1

    # 3. Đồng bộ Users
    users = db.query(User).all()
    for u in users:
        graph_sync.upsert_user_node(
            user_id=u.Id,
            email=u.email,
            full_name=u.full_name,
            role=u.role.value if hasattr(u.role, 'value') else str(u.role)
        )
        stats["users"] += 1

    # 4. Đồng bộ Jobs và JobSkills
    jobs = db.query(Job).all()
    for j in jobs:
        sync_job_to_graph(db, j.Id)
        stats["jobs"] += 1

    # 5. Đồng bộ CVs và CVSkills
    cvs = db.query(CV).all()
    for c in cvs:
        sync_cv_to_graph(db, c.Id)
        stats["cvs"] += 1

    logger.info("Batch sync completed: %s", stats)
    return stats


def get_skill_gap_analysis_service(db: Session, cv_id: int, job_id: int) -> Dict[str, Any]:
    """
    Dịch vụ phân tích khoảng cách kỹ năng (Skill Gap Analysis) có giải thích chi tiết.
    Tự động đồng bộ nếu dữ liệu chưa có trên đồ thị.
    """
    # Đảm bảo dữ liệu tồn tại trên graph
    cv_record = db.query(CV).filter(CV.Id == cv_id).first()
    job_record = db.query(Job).filter(Job.Id == job_id).first()
    if not cv_record or not job_record:
        return {"error": "CV hoặc Job không tồn tại"}

    # Đồng bộ nhanh nếu cần
    sync_cv_to_graph(db, cv_id)
    sync_job_to_graph(db, job_id)

    # Chạy phân tích đồ thị
    gap_data = graph_match.analyze_skill_gap_graph(cv_id, job_id)

    # Thêm giải thích (Explanation) và khuyến nghị phát triển kỹ năng (Career Guidance)
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

    # Lấy vector của Job (nếu có)
    emb_record = db.query(JobEmbedding).filter(JobEmbedding.JobId == job_id).order_by(JobEmbedding.CreatedAt.desc()).first()
    job_vector = list(emb_record.Vector) if (emb_record and emb_record.Vector is not None) else None

    # Đảm bảo Job đã lên graph
    sync_job_to_graph(db, job_id)

    return graph_match.hybrid_match_cvs_for_job_graph(
        job_id=job_id,
        job_vector=job_vector,
        top_k=top_k
    )
