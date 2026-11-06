from sqlalchemy.orm import Session
from app.models.profile import Profile
from app.models.profile_work_exp import ProfileWorkExp


def get_profile_work_exp(db: Session, profile_id: int):
    """Lấy danh sách kinh nghiệm của một hồ sơ cá nhân."""
    return db.query(ProfileWorkExp).filter(ProfileWorkExp.Id == profile_id).all()

def create_profile_work_exp(db: Session):
    pass

def update_profile_work_exp(db: Session):
    pass
