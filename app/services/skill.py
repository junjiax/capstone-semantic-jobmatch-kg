from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.schemas.skill import CVSkillCreate, CVSkillUpdate
from app.crud import skill as skill_crud

from app.api.v1.schemas.skill import SkillCreate, SkillUpdate

def get_skill_by_name(db:Session, skill_name):
    return skill_crud.get_skill_by_name(db, skill_name)

def create_skill_service(db: Session, skill_in: SkillCreate):
    """Admin thêm kỹ năng mới vào danh mục master."""
    existing = skill_crud.get_skill_by_name(db, skill_in.Name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Kỹ năng '{skill_in.Name}' đã tồn tại trong hệ thống."
        )
    return skill_crud.create_skill(db, skill_in.model_dump())


def update_skill_service(db: Session, skill_id: int, skill_in: SkillUpdate):
    """Admin cập nhật thông tin kỹ năng master."""
    update_data = skill_in.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không có dữ liệu thay đổi."
        )
    data = skill_crud.update_skill(db, skill_id, update_data)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy kỹ năng."
        )
    return data


def delete_skill_master_service(db: Session, skill_id: int) -> bool:
    """Admin xóa kỹ năng khỏi danh mục master."""
    success = skill_crud.delete_skill(db, skill_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy kỹ năng."
        )
    return success

def add_skill_to_cv(db: Session, user_id: int, skill_in: CVSkillCreate):
    skill_dict = skill_in.model_dump(exclude_unset=True) 

    return skill_crud.create_cv_skill(
        db=db,
        user_id=user_id,
        data=skill_dict
    )

def patch_skill_service(db: Session, cv_skill_id: int, cv_id: int, user_id: int, update_data: CVSkillUpdate):
    """Cập nhật Confidence hoặc Source của kỹ năng."""
    data = skill_crud.update_cv_skill(
        db, cv_skill_id, cv_id, user_id,
        update_data.model_dump(exclude_none=True)
    )
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy kỹ năng."
        )
    return data


def delete_skill_service(db: Session, cv_skill_id: int, cv_id: int, user_id: int) -> bool:
    """Xóa kỹ năng khỏi hồ sơ."""
    success = skill_crud.delete_cv_skill(db, cv_skill_id, cv_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không thể xóa: Kỹ năng không tồn tại hoặc không thuộc hồ sơ này."
        )
    return success