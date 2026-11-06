from sqlalchemy.orm import Session
from app.models.profile import Profile
from app.models.profile_edu import ProfileEdu


def get_profile_edu(db: Session, profile_id: int):
    """Lấy danh sách học vấn của một hồ sơ cá nhân."""
    return db.query(ProfileEdu).filter(ProfileEdu.Id == profile_id).all()

def create_profile_edu(db: Session):
    pass

def update_profile_edu(db: Session):
    pass
