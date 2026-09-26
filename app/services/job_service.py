from fastapi import HTTPException, status
from huggingface_hub import User
from sqlalchemy.orm import Session
from app.crud import job as job_crud
from app.models.enum import UserRole
from app.models.job import Job
from app.api.v1.schemas.job import JobCreate, JobUpdate, JobFilter, JobResponse

def get_jobs(db: Session, filters: JobFilter,     page: int = 1,
    size: int = 10,):
    skip = (page - 1) * size
    limit = size

    jobs, total = job_crud.get_jobs(
        db,
        skip=skip,
        limit=limit,
        title=filters.title,
        requirement=filters.requirement,
        status=filters.status
    )
    if not jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy job nào."
        )
    return jobs, total

def get_job_detail(db: Session, job_id: int):
    job = job_crud.get_job_by_id(db, job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy job {job_id}"
        )
    else:
        return job
    
def get_job_by_name(db: Session, name: str):
    return job_crud.get_job_by_name(db, name=name)

#---------------------------------
#--------- HR & Admin ---------
#---------------------------------

def create_job(db: Session, current_user: User, job_data: JobCreate):
    is_hr = (current_user.role == UserRole.HR) 
    if not is_hr:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người dùng có vai trò HR mới có thể tạo job."
        )
    job = job_data.model_dump(exclude_unset=True)

    data = job_crud.create_job(db, **job)
    return data

def update_job(db: Session, current_user: User, job_id: int, job_data: JobUpdate):
    is_hr = (current_user.role == UserRole.HR) 
    if not is_hr:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ người dùng có vai trò HR mới có thể cập nhật job."
        )
    
    job = job_crud.get_job_by_id(db, job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy job {job_id}"
        )

    updated_job = job_data.model_dump(exclude_unset=True)
    if not updated_job:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không có dữ liệu thay đổi."
        )   
    data = job_crud.update_job(db, job, **updated_job)
    return data


