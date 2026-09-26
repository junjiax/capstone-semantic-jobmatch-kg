from sqlalchemy.orm import Session
from app.models.cv import CV
from app.models.cv_skill import CVSkill
from app.models.skill import Skill

from app.models.skill import Skill

def create_skill(db: Session, skill_in: dict):
    """Thêm kỹ năng mới vào bảng master."""
    db_skill = Skill(**skill_in)
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    return db_skill


def update_skill(db: Session, skill_id: int, skill_in: dict):
    """Cập nhật thông tin kỹ năng master."""
    db_skill = db.query(Skill).filter(Skill.Id == skill_id).first()
    if db_skill:
        for key, value in skill_in.items():
            setattr(db_skill, key, value)
        db.commit()
        db.refresh(db_skill)
    return db_skill


def delete_skill(db: Session, skill_id: int) -> bool:
    """Xóa kỹ năng khỏi bảng master."""
    db_skill = db.query(Skill).filter(Skill.Id == skill_id).first()
    if db_skill:
        db.delete(db_skill)
        db.commit()
        return True
    return False

def get_skill_by_name(db: Session, name: str):
    """Tìm kỹ năng trong bảng danh mục Master."""
    return db.query(Skill).filter(Skill.Name.ilike(name)).first()

def create_cv_skill(db: Session, user_id: int, data: dict):
    cv_id = data.get("CVId")
    skill_id = data.get("SkillId")

    cv = db.query(CV).filter(CV.Id == cv_id, CV.UserId == user_id).first()
    if not cv:
        return None

    db_cv_skill = db.query(CVSkill).filter(
        CVSkill.CVId == cv_id, 
        CVSkill.SkillId == skill_id
    ).first()

    if db_cv_skill:
        for key, value in data.items():
            if hasattr(db_cv_skill, key) and key not in ["Id", "CVId", "SkillId"]:
                setattr(db_cv_skill, key, value)
        print(f"Đã dùng setattr để cập nhật SkillId {skill_id}")
    else:
        db_cv_skill = CVSkill(**data)
        db.add(db_cv_skill)
        print(f"Đã dùng unpacking để tạo mới SkillId {skill_id}")

    db.commit()
    db.refresh(db_cv_skill)

    return db_cv_skill

def update_cv_skill(db: Session, cv_skill_id: int, cv_id: int, user_id: int, update_data: dict):
    db_cv_skill = db.query(CVSkill).join(CV).filter(
        CVSkill.Id == cv_skill_id,
        CV.Id == cv_id,
        CV.UserId == user_id
    ).first()

    if db_cv_skill:
        for key, value in update_data.items():
            setattr(db_cv_skill, key, value)
        db.commit()
        db.refresh(db_cv_skill)
    return db_cv_skill

def delete_cv_skill(db: Session, cv_skill_id: int, cv_id: int, user_id: int):
    """Gỡ bỏ kỹ năng khỏi hồ sơ (không xóa Skill master)."""
    db_cv_skill = db.query(CVSkill).join(CV).filter(
        CVSkill.Id == cv_skill_id, 
        CV.Id == cv_id, 
        CV.UserId == user_id
    ).first()
    if db_cv_skill:
        db.delete(db_cv_skill)
        db.commit()
        return True
    return False