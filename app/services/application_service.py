from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status


from app.models import User, UserRole
from app.models.application import Application, ApplicationHistory, ApplicationStatus
from app.models.job import JobStatus
from app.crud import application_crud
from app.crud.job import get_job_by_id
from app.crud.cv import get_cv_by_id   
from app.api.v1.schemas.application_schemas import ApplicationCreate, ApplicationStatusUpdate


def apply(
    db: Session,
    data: ApplicationCreate,
    applicant_id: int,
) -> Application:
        # Kiểm tra job tồn tại và đang mở
        job = get_job_by_id(db, data.JobId)
        if not job:
            raise HTTPException(status_code=404, detail="Không tìm thấy job")
        if job.Status != JobStatus.OPEN:
            raise HTTPException(status_code=400, detail="Job này không còn nhận hồ sơ")

        # Kiểm tra CV tồn tại và thuộc về user
        cv = get_cv_by_id(db, data.CVId)
        if not cv:
            raise HTTPException(status_code=404, detail="Không tìm thấy CV")
        if cv.UserId != applicant_id:
            raise HTTPException(status_code=403, detail="CV không thuộc về bạn")

        # Kiểm tra đã nộp chưa
        existing = application_crud.get_application_by_job_and_applicant(
            db, data.JobId, applicant_id
        )
        if existing:
            raise HTTPException(status_code=409, detail="Bạn đã nộp đơn vào vị trí này rồi")

        # Tạo application + ghi history trong 1 transaction
        app = application_crud.create_application(
            db,
            job_id=data.JobId,
            cv_id=data.CVId,
            applicant_id=applicant_id,
            cover_letter=data.CoverLetter,
        )
        application_crud.create_history_entry(
            db,
            application_id=app.Id,
            status=ApplicationStatus.APPLIED,
            changed_by_id=applicant_id,
            note="Nộp đơn ứng tuyển",
        )

        return application_crud.get_application_detail(db, app.Id)

    # ── Lịch sử ứng tuyển của user ───────────────────────────────────────────

def get_my_applications(
    db: Session,
    applicant_id: int,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[Application], int]:
    return application_crud.get_applications_by_applicant(
        db, applicant_id, skip=skip, limit=limit
    )

    # ── Chi tiết đơn ứng tuyển ───────────────────────────────────────────────
  
def get_application(db: Session, application_id: int) -> Application:
    app = application_crud.get_application_by_id(db, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn ứng tuyển")
    return app

    # ── Xem & Cập nhật trạng thái (HR / Admin) ─────────────────────────────────────
def get_applications_by_job(
    db: Session,
    job_id: int,
    app_status: Optional[str] = None,
) -> List[Application]:
    job = get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy job")
    return application_crud.get_applications_by_job(db, job_id, status=app_status)

def update_status(
    db: Session,
    application_id: int,
    data: ApplicationStatusUpdate,
    changed_by_id: int,
) -> Application:
    app = application_crud.get_application_by_id(db, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn ứng tuyển")
    new_status = ApplicationStatus(data.status)
    if app.Status == new_status:
       raise HTTPException(status_code=400, detail="Trạng thái không thay đổi")

    application_crud.update_application_status(db, application_id, new_status)
    application_crud.create_history_entry(
        db,
        application_id=application_id,
        status=new_status,
        changed_by_id=changed_by_id,
        note=data.note,
    )
    return application_crud.get_application_detail(db, application_id)

    # ── Lịch sử trạng thái ───────────────────────────────────────────────────

def get_history(
     db: Session, application_id: int
) -> List[ApplicationHistory]:
    app = application_crud.get_application_by_id(db, application_id)
    if not app:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn ứng tuyển")
    return application_crud.get_history_by_application(db, application_id)
    

def get_application_detail_with_auth(db: Session, application_id: int, current_user: User):
        """
        Lấy chi tiết đơn ứng tuyển với cơ chế phân quyền:
        - HR/Admin: Xem được tất cả.
        - Applicant: Chỉ xem được đơn do chính mình nộp.
        """
        # 1. Truy vấn dữ liệu từ CRUD
        application = application_crud.get_application_by_id(db, application_id)

        # 2. Kiểm tra tồn tại (404 Not Found)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Đơn ứng tuyển ID {application_id} không tồn tại."
            )

        # 3. Kiểm tra quyền sở hữu (403 Forbidden)
        # Nếu là Applicant, Id của họ phải khớp với ApplicantId trong đơn
        if current_user.role == UserRole.APPLICANT:
            if application.ApplicantId != current_user.Id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bạn không có quyền xem đơn ứng tuyển này."
                )

        # 4. Nếu vượt qua tất cả, trả về dữ liệu
        return application