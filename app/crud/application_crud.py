from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationHistory, ApplicationStatus


# ── Application ───────────────────────────────────────────────────────────────

def get_application_by_id(db: Session, application_id: int) -> Optional[Application]:
    return db.query(Application).filter(Application.Id == application_id).first()


def get_application_detail(db: Session, application_id: int) -> Optional[Application]:
    """Lấy application kèm đầy đủ relationships."""
    return db.query(Application).filter(Application.Id == application_id).first()


def get_application_by_job_and_applicant(
    db: Session, job_id: int, applicant_id: int
) -> Optional[Application]:
    """Kiểm tra ứng viên đã nộp vào job này chưa."""
    return db.query(Application).filter(
        Application.JobId == job_id,
        Application.ApplicantId == applicant_id,
    ).first()


def get_applications_by_applicant(
    db: Session,
    applicant_id: int,
    skip: int = 0,
    limit: int = 20,
) -> tuple[List[Application], int]:
    query = db.query(Application).filter(Application.ApplicantId == applicant_id)
    total = query.count()
    applications = (
        query.order_by(Application.AppliedAt.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return applications, total


def get_applications_by_job(
    db: Session,
    job_id: int,
    status: Optional[str] = None,
) -> List[Application]:
    """Lấy danh sách ứng viên theo job (cho HR)."""
    query = db.query(Application).filter(Application.JobId == job_id)
    if status:
        query = query.filter(Application.Status == status)
    return query.order_by(Application.AppliedAt.desc()).all()


def create_application(
    db: Session,
    job_id: int,
    cv_id: int,
    applicant_id: int,
    cover_letter: Optional[str] = None,
) -> Application:
    try:
        app = Application(
            JobId=job_id,
            CVId=cv_id,
            ApplicantId=applicant_id,
            CoverLetter=cover_letter,
            Status=ApplicationStatus.APPLIED,
        )
        db.add(app)
        db.flush()
        return app
    except Exception:
        db.rollback()
        raise


def update_application_status(
    db: Session,
    application_id: int,
    new_status: ApplicationStatus,
) -> Application:
    try:
        app = get_application_by_id(db, application_id)
        if not app:
            raise ValueError("Không tìm thấy")
        app.Status = new_status
        db.commit()
        db.refresh(app)
        return app
    except ValueError:
        raise
    except Exception:
        db.rollback()
        raise


# ── ApplicationHistory ────────────────────────────────────────────────────────

def create_history_entry(
    db: Session,
    application_id: int,
    status: ApplicationStatus,
    changed_by_id: Optional[int] = None,
    note: Optional[str] = None,
) -> ApplicationHistory:
    try:
        entry = ApplicationHistory(
            ApplicationId=application_id,
            Status=status,
            Note=note,
            ChangedById=changed_by_id,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    except Exception:
        db.rollback()
        raise


def get_history_by_application(
    db: Session, application_id: int
) -> List[ApplicationHistory]:
    return (
        db.query(ApplicationHistory)
        .filter(ApplicationHistory.ApplicationId == application_id)
        .order_by(ApplicationHistory.ChangedAt)
        .all()
    )