from sqlalchemy.orm import Session
from app.models.jd_skill import JDSkill
from typing import List


# ─── READ ──────────────────────────────────────────────────
def get_jd_skills(db: Session, jd_id: int) -> List[JDSkill]:
    """Lấy danh sách kỹ năng của một công việc."""
    return db.query(JDSkill).filter(JDSkill.JDId == jd_id).all()


# ─── CREATE ──────────────────────────────────────────────────
def create_jd_skill(db: Session, jd_id: int, skill_id: int) -> JDSkill:
    """Thêm kỹ năng vào một công việc."""
    jd_skill = JDSkill(JDId=jd_id, SkillId=skill_id)
    db.add(jd_skill)
    db.commit()
    db.refresh(jd_skill)
    return jd_skill
