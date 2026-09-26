from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_hr_or_admin
from app.api.v1.schemas.response import PaginationMeta, ResponseSchema
from app.models.User import User
from app.services import job_service
from app.core.database import get_db
from app.models.enum import JobStatus
from app.api.v1.schemas.job import JobCreate, JobFilter, JobResponse, JobUpdate

public_router = APIRouter()
private_router = APIRouter()

@public_router.get("/", response_model=ResponseSchema[list[JobResponse]], summary="Xem danh sách tất cả các job")
async def get_all_jobs(
    filters: JobFilter = Depends(),
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    """Xem danh sách tất cả các job, có thể lọc theo title, requirement text, status."""
    jobs, total = job_service.get_jobs(db, filters, page, size)
    return ResponseSchema[list[JobResponse]](
        success=True,
        message="Fetched jobs successfully",
        data=[JobResponse.model_validate(job) for job in jobs],
        meta=PaginationMeta(
            total=total,
            page=page,
            limit=size
        ).model_dump()
    )


@public_router.get(
    "/{job_id}",
    response_model=ResponseSchema[JobResponse],
    summary="Xem chi tiết một job"
)
async def get_job_detail(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Xem chi tiết một job theo ID."""
    job = job_service.get_job_detail(db, job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy job {job_id}"
        )

    return ResponseSchema[JobResponse](
        success=True,
        message="Fetched job successfully",
        data=JobResponse.model_validate(job),
        meta=None
    )


#=═══════════════════════════════════════════════════════
# QUẢN LÝ JOB — HR và Admin quản lý các job
#=═══════════════════════════════════════════════════════

@private_router.post(
    "/",
    response_model=ResponseSchema[JobResponse],
    summary="Tạo một job mới",
    dependencies=[Depends(require_hr_or_admin)]
)
async def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tạo một job mới với thông tin được cung cấp."""

    new_job = job_service.create_job(db,current_user, job_data)

    return ResponseSchema[JobResponse](
        success=True,
        message="Created job successfully",
        data=JobResponse.model_validate(new_job),
        meta=None
    )


@private_router.put(
    "/{job_id}",
    response_model=ResponseSchema[JobResponse],
    summary="Cập nhật thông tin của một job",
    dependencies=[Depends(require_hr_or_admin)]
)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cập nhật thông tin của một job (title, description, requirements_text)."""
    
    updated_job = job_service.update_job(db, current_user, job_id, job_data)

    if not updated_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy job {job_id}"
        )

    return ResponseSchema[JobResponse](
        success=True,
        message="Updated job successfully",
        data=JobResponse.model_validate(updated_job),
        meta=None
    )