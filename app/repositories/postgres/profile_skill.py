from typing import Any, List

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.profile_skill import ProfileSkill


def get_profile_skills(db: Session, profile_id: int):
    """Lấy danh sách kỹ năng của một hồ sơ cá nhân."""
    return db.query(ProfileSkill).filter(ProfileSkill.Id == profile_id).all()

def get_skills_by_profile_id(db: Session, profile_id: int) -> List[ProfileSkill]:
    """
    Lấy danh sách tất cả kỹ năng và vector của một Profile.
    Dùng ProfileSkill.ProfileId để lọc chính xác theo khóa ngoại.
    """
    return db.query(ProfileSkill).filter(ProfileSkill.ProfileId == profile_id).all()


def create_profile_skills(db: Session):
    pass


def sync_profile_skills(db: Session, **kwargs: Any) -> ProfileSkill:
    try:
        profile_skill = ProfileSkill(**kwargs)
    
        db.add(profile_skill)
        db.commit()
        db.refresh(profile_skill)
    
        return profile_skill
    
    except SQLAlchemyError:
        db.rollback()
        raise
    