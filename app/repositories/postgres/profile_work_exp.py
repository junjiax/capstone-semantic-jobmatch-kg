from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.profile_work_exp import ProfileWorkExp

"""
    GET PROFILE WORK EXP BASE ON PROFILE ID
"""


def get_profile_work_exp(db: Session, profile_id: int):
    """Lấy danh sách kinh nghiệm của một hồ sơ cá nhân."""
    return db.query(ProfileWorkExp).filter(ProfileWorkExp.Id == profile_id).all()


"""
    UPADTE PROFILE WORK EXP BASE ON PROFILE ID
"""


def sync_profile_work_exp(db: Session, **kwargs: Any) -> ProfileWorkExp:
    try:
        profile_work_exp = ProfileWorkExp(**kwargs)

        db.add(profile_work_exp)
        db.commit()
        db.refresh(profile_work_exp)

        return profile_work_exp

    except SQLAlchemyError:
        db.rollback()
        raise
