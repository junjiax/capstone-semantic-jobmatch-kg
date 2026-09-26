from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_applicant
from app.api.v1.schemas.response import ResponseSchema
from app.api.v1.schemas.education import EducationCreate, EducationResponse, EducationUpdate
from app.models import User
from app.services import education as edu_service

router = APIRouter(dependencies=[Depends(require_applicant)])


# --- QUẢN LÝ HỌC VẤN (EDUCATION) ---

@router.post(
    "/me/education",
    response_model=ResponseSchema[EducationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add Education",
    description="Thêm mới một mốc học vấn vào hồ sơ CV."
)
def create_education(
    edu: EducationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    data = edu_service.create_education(db, current_user.Id, edu)
    if not data:
        raise HTTPException(status_code=403, detail="CVId không hợp lệ hoặc bạn không có quyền sở hữu.")
    return ResponseSchema[EducationResponse](
        success=True,
        message="Education added successfully",
        data=data
    )


@router.patch(
    "/me/education/{cv_id}/{edu_id}",
    response_model=ResponseSchema[EducationResponse],
    summary="Patch Education",
    description="Cập nhật từng phần thông tin học vấn."
)
def patch_education(
    cv_id: int,
    edu_id: int,
    edu: EducationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    data = edu_service.update_education_service(
        db=db,
        edu_id=edu_id,
        cv_id=cv_id,
        user_id=current_user.Id,
        edu_in=edu
    )
    return ResponseSchema[EducationResponse](
        success=True,
        message="Education updated successfully",
        data=data
    )


@router.delete(
    "/me/education/{cv_id}/{edu_id}",
    response_model=ResponseSchema,
    summary="Delete Education",
    description="Xóa một mốc học vấn khỏi hồ sơ CV."
)
def delete_education(
    cv_id: int,
    edu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    edu_service.delete_education_service(
        db=db,
        edu_id=edu_id,
        cv_id=cv_id,
        user_id=current_user.Id
    )
    return ResponseSchema(
        success=True,
        message="Education deleted successfully",
        data=None
    )