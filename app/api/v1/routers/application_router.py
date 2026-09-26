from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_applicant, require_hr, require_hr_or_admin
from app.api.v1.schemas import ResponseSchema
from app.api.v1.schemas.application_schemas import (
    ApplicationCreate,
    ApplicationStatusUpdate,
    ApplicationResponse,
    ApplicationDetailResponse,
    ApplicationHistoryResponse,
)
from app.models import User
from app.models.enum import UserRole
from app.services import application_service

router = APIRouter()
applicant_router = APIRouter(dependencies=[Depends(require_applicant)])
hr_router = APIRouter(dependencies=[Depends(require_hr_or_admin)])


# ─────────────────────────────────────────────────────────────────────────────
# GENERAL ROUTER (Dành cho cả Applicant và HR - Xử lý phân quyền trong Service)
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{application_id}",
    response_model=ResponseSchema[ApplicationDetailResponse],
    summary="Get Application Detail",
    description="Xem chi tiết đơn ứng tuyển. Ứng viên chỉ xem được đơn của mình, HR xem được tất cả."
)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    application = application_service.get_application(
        db=db,
        application_id=application_id
    )
    if (
        current_user.role == UserRole.APPLICANT
        and application.ApplicantId != current_user.Id
    ):
        raise HTTPException(status_code=403, detail="Không có quyền truy cập")
 
    return ResponseSchema[ApplicationDetailResponse](
        success=True,
        message="Lấy chi tiết đơn ứng tuyển thành công",
        data=ApplicationDetailResponse.model_validate(application) # Convert SQLAlchemy ORM object -> Pydantic schema để validate và serialize đúng format response
    )


# @router.get(
#     "/{application_id}/history",
#     response_model=ResponseSchema[List[ApplicationHistoryResponse]],
#     summary="Get Status History",
#     description="Xem lịch sử thay đổi trạng thái của một đơn ứng tuyển."
# )
# def get_application_history(
#     application_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     # Kiểm tra quyền xem lịch sử trong Service
#     data = ApplicationService.get_history(db, application_id, current_user)
    
#     return ResponseSchema[List[ApplicationHistoryResponse]](
#         success=True,
#         message="Fetched application history successfully",
#         data=data
#     )

# ─────────────────────────────────────────────────────────────────────────────
# APPLICANT ROUTER (Dành cho ứng viên)
# ─────────────────────────────────────────────────────────────────────────────

@applicant_router.post(
    "/me/apply",
    response_model=ResponseSchema[ApplicationDetailResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Apply for Job",
    description="Ứng viên nộp hồ sơ vào một vị trí tuyển dụng nhất định."
)
def apply_for_job(
    data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    application = application_service.apply(
        db=db,
        data=data,
        applicant_id=current_user.Id
    )
    print(application)
    print(type(application))
    return ResponseSchema[ApplicationDetailResponse](
        success=True,
        message="Nộp đơn ứng tuyển thành công",
        data=ApplicationDetailResponse.model_validate(application)
    )


@applicant_router.get(
    "/me/applications",
    response_model=ResponseSchema[List[ApplicationResponse]],
    summary="Get My Applications",
    description="Xem danh sách các đơn đã nộp của chính người dùng hiện tại."
)
def my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    apps, _ = application_service.get_my_applications(
        db=db,
        applicant_id=current_user.Id
    )
    return ResponseSchema[List[ApplicationResponse]](
        success=True,
        message="Lấy lịch sử ứng tuyển thành công",
        data=[ApplicationResponse.model_validate(app) for app in apps]
    )


# ─────────────────────────────────────────────────────────────────────────────
# HR ROUTER (Dành cho nhân sự/quản lý)
# ─────────────────────────────────────────────────────────────────────────────

@hr_router.patch(
    "/{application_id}/status",
    response_model=ResponseSchema[ApplicationDetailResponse],
    summary="Update Application Status",
    description="HR cập nhật trạng thái đơn (Applied -> Shortlisted -> Interview -> Rejected/Hired).",
    dependencies=[Depends(require_hr_or_admin)]
)
def update_application_status(
    application_id: int,
    data: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    application = application_service.update_status(
        db=db,
        application_id=application_id,
        data=data,
        changed_by_id=current_user.Id
    )
    return ResponseSchema[ApplicationDetailResponse](
        success=True,
        message="Cập nhật trạng thái thành công",
        data=ApplicationDetailResponse.model_validate(application)
    )


@hr_router.get(
    "/job/{job_id}",
    response_model=ResponseSchema[List[ApplicationResponse]],
    summary="Danh sách đơn ứng tuyển theo job",
    description="HR/Admin xem tất cả đơn ứng tuyển của 1 vị trí. Có thể lọc theo status.",
    dependencies=[Depends(require_hr_or_admin)]
)
def get_applications_by_job(
    job_id: int,
    app_status: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    apps = application_service.get_applications_by_job(
        db=db, job_id=job_id, app_status=app_status
    )
    return ResponseSchema[List[ApplicationResponse]](
        success=True,
        message="Lấy danh sách đơn ứng tuyển thành công",
        data=[ApplicationResponse.model_validate(app) for app in apps]
    )


# ─────────────────────────────────────────────────────────────────────────────
# INCLUDE ROUTERS
# ─────────────────────────────────────────────────────────────────────────────

router.include_router(applicant_router)
router.include_router(hr_router)