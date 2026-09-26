from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.api.v1.schemas.cv import PersonalInfoUpdate
from app.crud import applicant as applicant_crud, cv as cv_crud
from app.models import User
from app.models.enum import UserRole


def get_applicant_profile(db: Session, cv_id: int, current_user: User, applicant_id: Optional[int] = None):
    """Lấy hồ sơ ứng viên (HR hoặc chính chủ)."""
    target_user_id = current_user.Id

    if applicant_id and applicant_id != current_user.Id:
        if current_user.role != UserRole.HR:
            raise HTTPException(status_code=403, detail="Bạn không có quyền xem hồ sơ này.")
        target_user_id = applicant_id

    profile = applicant_crud.get_profile_by_id(db, cv_id, target_user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Hồ sơ không tồn tại.")
    return profile


def update_personal_info(db: Session, cv_id: int, current_user: User, info: PersonalInfoUpdate):
    """Cập nhật thông tin cá nhân (PATCH)."""
    return applicant_crud.update_personal_info(
        db, cv_id, current_user.Id, info.model_dump(exclude_none=True)
    )

def get_cv_list_service(db: Session, applicant_id: int):
    cvs = cv_crud.get_cvs(db, filters={"UserId": applicant_id})
    if not cvs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ứng viên chưa có CV nào."
        )
    return cvs