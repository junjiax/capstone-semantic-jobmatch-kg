from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.profile_edu import ProfileEdu


def get_profile_edu(db: Session, profile_id: int):
    """Lấy danh sách học vấn của một hồ sơ cá nhân."""
    return db.query(ProfileEdu).filter(ProfileEdu.Id == profile_id).all()


def create_profile_edu(db: Session):
    pass


def sync_profile_edu(db: Session, **kwargs: Any) -> ProfileEdu:
    try:
        profile_edu = ProfileEdu(**kwargs)

        db.add(profile_edu)
        db.commit()
        db.refresh(profile_edu)

        return profile_edu

    except SQLAlchemyError:
        db.rollback()
        raise
