from sqlalchemy.orm import Session
from app.models.cv import CV
from app.models.education import Education

def get_education_by_school(db: Session, cv_id: int, school_name: str):
    """Tìm bản ghi học vấn dựa vào Tên trường và CV"""
    return db.query(Education).filter(
        Education.CVId == cv_id,
        Education.School == school_name
    ).first()

def create_education(db: Session, edu_data: dict):
    """Thêm mới một dòng học vấn"""
    db_edu = Education(**edu_data)
    db.add(db_edu)
    db.commit()
    db.refresh(db_edu)
    return db_edu

def update_education(db: Session, edu_id: int, cv_id: int, user_id: int, edu_in: dict):
    """Cập nhật học vấn - Xác thực quyền sở hữu chéo qua join CV."""
    db_edu = db.query(Education).join(CV).filter(
        Education.Id == edu_id, 
        CV.Id == cv_id, 
        CV.UserId == user_id
    ).first()
    
    if db_edu:
        for key, value in edu_in.items():
            setattr(db_edu, key, value)
        db.commit()
        db.refresh(db_edu)
    return db_edu

def delete_education(db: Session, edu_id: int, cv_id: int, user_id: int):
    """Xóa học vấn - Đảm bảo tính an toàn dữ liệu."""
    db_edu = db.query(Education).join(CV).filter(
        Education.Id == edu_id, 
        CV.Id == cv_id, 
        CV.UserId == user_id
    ).first()
    
    if db_edu:
        db.delete(db_edu)
        db.commit()
        return True
    return False