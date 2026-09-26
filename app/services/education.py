from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.schemas.education import EducationCreate, EducationUpdate
from app.crud import (
    education as edu_crud,
    cv as cv_crud
)

def create_education(db: Session, user_id: int, edu_in: EducationCreate):
    """Service điều phối nghiệp vụ Học vấn"""
    print("=== ACCESS EDUCATION SERVICE ===")
    
    cv_id = edu_in.CVId
    cv_exists = cv_crud.get_cv_by_id(db, cv_id=cv_id) 
    
    if not cv_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CV với ID {cv_id} không tồn tại."
        )
    
    if cv_exists.UserId != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền chỉnh sửa CV này."
        )

    edu_data = edu_in.model_dump(exclude_unset=True)
    school_name = edu_data.get("School")

    existing_edu = edu_crud.get_education_by_school(db, cv_id=cv_id, school_name=school_name)

    if existing_edu:
        return edu_crud.update_education(db, db_edu=existing_edu, update_data=edu_data)
    else:
        return edu_crud.create_education(db, edu_data=edu_data)


def update_education_service(db: Session, edu_id: int, cv_id: int, user_id: int, edu_in: EducationUpdate):
    """Cập nhật từng phần học vấn."""
    update_data = edu_in.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không có dữ liệu thay đổi."
        )

    data = edu_crud.update_education(db, edu_id, cv_id, user_id, update_data)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy bản ghi học vấn hoặc bạn không có quyền sở hữu."
        )
    return data


def delete_education_service(db: Session, edu_id: int, cv_id: int, user_id: int) -> bool:
    """Xóa học vấn."""
    success = edu_crud.delete_education(db, edu_id, cv_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy học vấn."
        )
    return success