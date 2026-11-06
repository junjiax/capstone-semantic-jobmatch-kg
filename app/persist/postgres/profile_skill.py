from sqlalchemy.orm import Session
from app.models.profile import Profile
from app.models.profile_skill import ProfileSkill


def get_profile_skills(db: Session, profile_id: int):
    """Lấy danh sách kỹ năng của một hồ sơ cá nhân."""
    return db.query(ProfileSkill).filter(ProfileSkill.Id == profile_id).all()

def create_profile_skills(db: Session):
    pass

def update_profile_skills(db: Session):
    pass
