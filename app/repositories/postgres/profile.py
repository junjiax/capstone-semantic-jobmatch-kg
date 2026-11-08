from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.profile import Profile

"""
    GET LIST OF FILTERED PROFILES
"""


def get_profiles(db: Session, filters: Dict[str, Any]) -> List[Profile]:
    query = db.query(Profile)

    if filters.get("UserId") is not None:
        query = query.filter(Profile.UserId == filters["UserId"])

    if filters.get("FileType") is not None:
        query = query.filter(Profile.FileType == filters["FileType"])

    if filters.get("start_date") is not None:
        query = query.filter(Profile.CreatedAt >= filters["start_date"])

    if filters.get("end_date") is not None:
        query = query.filter(Profile.CreatedAt <= filters["end_date"])

    return query.order_by(Profile.CreatedAt.desc()).all()


"""
    GET PROFILE BY ID
"""


def get_profile_by_id(db: Session, profile_id: int) -> Optional[Profile]:
    return db.get(Profile, profile_id)


"""
    SYNC PROFILE TO DATABASE
"""


def sync_profile(db: Session, **kwargs: Profile) -> Profile:
    """
    Lưu metadata của file Profile mới.
    Lưu ý: 'version' được quản lý tự động qua mốc thời gian CreatedAt.
    """
    try:
        profile = Profile(**kwargs)

        db.add(profile)
        db.commit()
        db.refresh(profile)

        return profile

    except SQLAlchemyError:
        db.rollback()
        raise


"""
    SYNC BATCH OF PROFILES TO DATABASE
"""


def sync_list_of_profiles(
    db: Session, parsed_profiles_data: List[Dict[str, Any]]
) -> List[Profile]:
    try:
        list_of_profiles = [Profile(**profile) for profile in parsed_profiles_data]

        db.add_all(list_of_profiles)
        db.commit()

        for profile in list_of_profiles:
            db.refresh(profile)

        return list_of_profiles

    except SQLAlchemyError:
        db.rollback()
        raise
