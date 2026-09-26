from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.job_skill import JobSkill
from app.models.skill import Skill


def get_job_skills(db: Session, job_id: int):
    """Lấy danh sách kỹ năng của một công việc."""
    return db.query(JobSkill).filter(JobSkill.JobId == job_id).all()
