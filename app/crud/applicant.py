from sqlalchemy.orm import Session, joinedload
from app.models.cv import CV
from app.models.cv_skill import CVSkill


def get_profile_by_id(db: Session, cv_id: int, user_id: int):
    """
    Lấy toàn bộ hồ sơ ứng viên bằng 1 query duy nhất (Eager Loading).
    Xác thực: CV phải thuộc về user_id đang đăng nhập.
    """
    return db.query(CV).options(
        joinedload(CV.educations),
        joinedload(CV.experiences),
        joinedload(CV.skills).joinedload(CVSkill.skill) 
    ).filter(CV.Id == cv_id, CV.UserId == user_id).first()


def update_personal_info(db: Session, cv_id: int, user_id: int, info_update: dict):
    """Cập nhật Summary, Language hoặc các thông tin metadata của CV."""
    db_cv = db.query(CV).filter(CV.Id == cv_id, CV.UserId == user_id).first()
    if db_cv:
        for key, value in info_update.items():
            if hasattr(db_cv, key):
                setattr(db_cv, key, value)
        db.commit()
        db.refresh(db_cv)
    return db_cv











