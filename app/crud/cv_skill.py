from sqlalchemy.orm import Session
from app.models.cv import CV
from app.models.cv_skill import CVSkill
from app.models.skill import Skill


def get_cv_skills(db: Session, cv_id: int):
    """Lấy danh sách kỹ năng của một hồ sơ cá nhân."""
    return db.query(CVSkill).filter(CVSkill.CVId == cv_id).all()
