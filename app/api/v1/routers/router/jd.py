from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.models.jd import JD
from app.models.user import User

router = APIRouter()


@router.get(
    "/available",
    summary="Danh sách JD khả dụng",
    description="Trả về các Job Description, mới nhất trước.",
    responses={401: {"description": "Chưa đăng nhập hoặc token không hợp lệ."}},
)
def list_available_jobs(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    jobs = db.query(JD).order_by(JD.CreatedAt.desc()).all()
    return {
        "success": True,
        "data": [
            {
                "id": job.Id,
                "title": job.Title,
                "domain": job.Domain,
                "expertise": job.Expertise,
                "experience": job.Experience,
                "createdAt": job.CreatedAt,
            }
            for job in jobs
        ],
    }
