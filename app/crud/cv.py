from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.cv import CV

def get_cvs(db: Session, filters: dict) -> List[CV]:
    """
    Lấy toàn bộ danh sách CV thỏa mãn bộ lọc.
    """
    query = db.query(CV)

    if "UserId" in filters:
        query = query.filter(CV.UserId == filters["UserId"])
    if "FileType" in filters:
        query = query.filter(CV.FileType == filters["FileType"])
    if "Language" in filters:
        query = query.filter(CV.Language == filters["Language"])
    if filters.get("start_date"):
        query = query.filter(CV.CreatedAt >= filters["start_date"])
    if filters.get("end_date"):
        query = query.filter(CV.CreatedAt <= filters["end_date"])

    # Luôn trả về từ mới nhất đến cũ nhất
    return query.order_by(CV.CreatedAt.desc()).all()

def get_cv_by_id(db: Session, cv_id: int) -> Optional[CV]:
    """
    Lấy thông tin chi tiết của một bản CV dựa trên ID.
    """
    return db.query(CV).filter(CV.Id == cv_id).first()

def create_cv(db: Session, applicant_id: int, path: str, file_type: Any):
    """
    Lưu metadata của file CV mới. 
    Lưu ý: 'version' được quản lý tự động qua mốc thời gian CreatedAt.
    """
    db_cv = CV(
        UserId=applicant_id,
        FileUrl=path,
        FileType=file_type,
    )
    db.add(db_cv)
    db.commit()
    db.refresh(db_cv)
    return db_cv

def get_latest_cv(db: Session, applicant_id: int):
    """
    Truy vấn bản CV mới nhất để hiển thị mặc định hoặc thực hiện phân tích.
    """
    return db.query(CV)\
        .filter(CV.UserId == applicant_id)\
        .order_by(CV.CreatedAt.desc())\
        .first()

def save_parsed_data(db: Session, cv_id: int, parsed_data: Dict[str, Any]) -> Optional[CV]:
    """
    Lưu kết quả trích xuất (Parsing) vào các trường: RawText, CleanText, Summary, Language.
    """
    db_cv = db.query(CV).filter(CV.Id == cv_id).first()
    
    if db_cv:
        for key, value in parsed_data.items():
            if hasattr(db_cv, key):
                setattr(db_cv, key, value)
        
        db.commit()
        db.refresh(db_cv)
    return db_cv