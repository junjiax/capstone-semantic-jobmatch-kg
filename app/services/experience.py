from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.schemas.experience import ExperienceCreate, ExperienceUpdate
from app.crud import experience as exp_crud


def validate_date_range(start_date, end_date):
    """Kiểm tra logic thời gian."""
    if end_date and start_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ngày bắt đầu không thể sau ngày kết thúc."
        )


def add_experience(db: Session, user_id: int, exp_in: ExperienceCreate):
    """Thêm mới kinh nghiệm làm việc."""
    validate_date_range(exp_in.StartDate, exp_in.EndDate)
    return exp_crud.create_experience(
        db, exp_in.CVId, user_id,
        exp_in.model_dump(exclude={"CVId"})
    )


def patch_experience_service(db: Session, exp_id: int, cv_id: int, user_id: int, exp_in: ExperienceUpdate):
    """Cập nhật từng phần kinh nghiệm."""
    update_data = exp_in.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không có dữ liệu thay đổi."
        )
    validate_date_range(
        update_data.get("StartDate"),
        update_data.get("EndDate")
    )

    data = exp_crud.update_experience(db, exp_id, cv_id, user_id, update_data)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy kinh nghiệm."
        )
    return data


def delete_experience_service(db: Session, exp_id: int, cv_id: int, user_id: int) -> bool:
    """Xóa kinh nghiệm làm việc."""
    success = exp_crud.delete_experience(db, exp_id, cv_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy kinh nghiệm."
        )
    return success