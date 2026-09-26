from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_applicant
from app.api.v1.schemas import ResponseSchema
from app.api.v1.schemas.experience import ExperienceCreate, ExperienceResponse, ExperienceUpdate
from app.models import User

from app.services import experience as exp_service

router = APIRouter(dependencies=[Depends(require_applicant)])


@router.post(
    "/me/experience",
    response_model=ResponseSchema[ExperienceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add Experience",
    description="Thêm mới kinh nghiệm làm việc."
)
def create_experience(
    exp: ExperienceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    data = exp_service.add_experience(db, current_user.Id, exp)
    if not data:
        raise HTTPException(status_code=403, detail="CVId không hợp lệ hoặc bạn không có quyền sở hữu.")
    return ResponseSchema[ExperienceResponse](
        success=True,
        message="Experience added successfully",
        data=data
    )


@router.patch(
    "/me/experience/{cv_id}/{exp_id}",
    response_model=ResponseSchema[ExperienceResponse],
    summary="Patch Experience",
    description="Cập nhật từng phần thông tin kinh nghiệm làm việc."
)
def patch_experience(
    cv_id: int,
    exp_id: int,
    exp: ExperienceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    data = exp_service.patch_experience_service(
        db=db,
        exp_id=exp_id,
        cv_id=cv_id,
        user_id=current_user.Id,
        exp_in=exp
    )
    return ResponseSchema[ExperienceResponse](
        success=True,
        message="Experience updated successfully",
        data=data
    )


@router.delete(
    "/me/experience/{cv_id}/{exp_id}",
    response_model=ResponseSchema,
    summary="Delete Experience",
    description="Xóa một mốc kinh nghiệm làm việc khỏi hồ sơ CV."
)
def delete_experience(
    cv_id: int,
    exp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp_service.delete_experience_service(
        db=db,
        exp_id=exp_id,
        cv_id=cv_id,
        user_id=current_user.Id
    )
    return ResponseSchema(
        success=True,
        message="Experience deleted successfully",
        data=None
    )