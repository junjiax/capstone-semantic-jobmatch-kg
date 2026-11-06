from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.profile import Profile


def get_profiles(db: Session, filters: Dict[str, Profile]) -> List[Profile]:
    """
    Lấy toàn bộ danh sách Profile thỏa mãn bộ lọc.
    """
    query = db.query(Profile)

    if "UserId" in filters:
        query = query.filter(Profile.UserId == filters["UserId"])
    if "FileType" in filters:
        query = query.filter(Profile.FileType == filters["FileType"])
    if filters.get("start_date"):
        query = query.filter(Profile.CreatedAt >= filters["start_date"])
    if filters.get("end_date"):
        query = query.filter(Profile.CreatedAt <= filters["end_date"])

    # Luôn trả về từ mới nhất đến cũ nhất
    return query.order_by(Profile.CreatedAt.desc()).all()


def get_profile_by_id(db: Session, Profile_id: int) -> Optional[Profile]:
    """
    Lấy thông tin chi tiết của một bản Profile dựa trên ID.
    """
    return db.query(Profile).filter(Profile.Id == Profile_id).first()


def create_profile(db: Session, candidate_id: int, path: str, file_type: Any):
    """
    Lưu metadata của file Profile mới.
    Lưu ý: 'version' được quản lý tự động qua mốc thời gian CreatedAt.
    """
    db_Profile = Profile(
        UserId=candidate_id,
        FileUrl=path,
        FileType=file_type,
    )
    db.add(db_Profile)
    db.commit()
    db.refresh(db_Profile)
    return db_Profile


def get_latest_Profile(db: Session, candidate_id: int):
    """
    Truy vấn bản Profile mới nhất để hiển thị mặc định hoặc thực hiện phân tích.
    """
    return (
        db.query(Profile)
        .filter(Profile.UserId == candidate_id)
        .order_by(Profile.CreatedAt.desc())
        .first()
    )


def save_parsed_data(
    db: Session, Profile_id: int, parsed_data: Dict[str, Any]
) -> Optional[Profile]:
    """
    Lưu kết quả trích xuất (Parsing) vào các trường: RawText, CleanText, Summary, Language.
    """
    db_Profile = db.query(Profile).filter(Profile.Id == Profile_id).first()

    if db_Profile:
        for key, value in parsed_data.items():
            if hasattr(db_Profile, key):
                setattr(db_Profile, key, value)

        db.commit()
        db.refresh(db_Profile)
    return db_Profile
