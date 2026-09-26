from typing import Optional
from sqlalchemy.orm import Session
from app.models.job import Job
from app.models.enum import JobStatus
# ─── READ ────────────────────────────────────────────────────
def get_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    title: Optional[str] = None,
    requirement: Optional[str] = None,
    status: Optional[JobStatus] = None,
) -> tuple[list[Job], int]:

    query = db.query(Job)

    # Filter theo title (LIKE)
    if title:
        query = query.filter(Job.Title.ilike(f"%{title}%"))

    # Filter theo requirement text
    if requirement:
        query = query.filter(Job.RequirementsText.ilike(f"%{requirement}%"))

    # Filter theo status
    if status:
        query = query.filter(Job.Status == status)

    total = query.count()

    jobs = (
        query.order_by(Job.CreatedAt.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return jobs, total



def get_job_by_id(db: Session, job_id: int) -> Optional[Job]:  
    """Tìm job theo primary key. Trả None nếu không tồn tại."""
    return db.query(Job).filter(Job.Id == job_id).first()

def get_job_by_name(db: Session, name: str) -> Optional[Job]:
    """Tìm job theo tên (không phân biệt hoa thường)."""
    return db.query(Job).filter(Job.Title.ilike(name)).first()

# ─── CREATE ──────────────────────────────────────────────────
def create_job(db: Session, **kwargs) -> Job:
    job = Job(**kwargs)
    db.add(job)
    db.commit()
    db.refresh(job) 
    return job

# ─── UPDATE ──────────────────────────────────────────────────
def update_job(db: Session, job: Job, **kwargs) -> Job:
    for field, value in kwargs.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job

def update_job_status(db: Session, job_id: int, new_status: JobStatus) -> Job:
    try:
        job = get_job_by_id(db, job_id)
        if not job:
            raise ValueError("Job not found")
        job.Status = JobStatus(new_status)
        db.commit()
        db.refresh(job)
        return job
    except ValueError:
        raise ValueError("Invalid job status")
    except Exception:
        db.rollback()
        raise

# ─── DELETE ──────────────────────────────────────────────────
def delete_job(db: Session, job: Job) -> None:
    db.delete(job)
    db.commit()




