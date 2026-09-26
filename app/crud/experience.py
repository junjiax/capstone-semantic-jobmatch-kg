from sqlalchemy.orm import Session
from app.models.cv import CV
from app.models.experience import Experience

def create_experience(db: Session, cv_id: int, user_id: int, exp_in: dict):
    """Thêm mới kinh nghiệm làm việc."""
    cv_exists = db.query(CV).filter(CV.Id == cv_id, CV.UserId == user_id).first()
    if not cv_exists:
        return None

    db_exp = Experience(**exp_in, CVId=cv_id)
    db.add(db_exp)
    db.commit()
    db.refresh(db_exp)
    return db_exp

def update_experience(db: Session, exp_id: int, cv_id: int, user_id: int, exp_in: dict):
    """Cập nhật kinh nghiệm làm việc."""
    db_exp = db.query(Experience).join(CV).filter(
        Experience.Id == exp_id, 
        CV.Id == cv_id, 
        CV.UserId == user_id
    ).first()

    if db_exp:
        for key, value in exp_in.items():
            setattr(db_exp, key, value)
        db.commit()
        db.refresh(db_exp)
    return db_exp

def delete_experience(db: Session, exp_id: int, cv_id: int, user_id: int):
    """Xóa kinh nghiệm làm việc."""
    db_exp = db.query(Experience).join(CV).filter(
        Experience.Id == exp_id, 
        CV.Id == cv_id, 
        CV.UserId == user_id
    ).first()
    if db_exp:
        db.delete(db_exp)
        db.commit()
        return True
    return False