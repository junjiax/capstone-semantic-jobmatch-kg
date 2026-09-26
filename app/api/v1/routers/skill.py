from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_admin, require_applicant
from app.api.v1.schemas import ResponseSchema
from app.api.v1.schemas.skill import CVSkillCreate, CVSkillResponse, CVSkillUpdate, SkillCreate, SkillResponse, SkillUpdate
from app.models import User
from app.services import skill as skill_service

router = APIRouter()
admin_router = APIRouter(dependencies=[Depends(require_admin)])
applicant_router = APIRouter(dependencies=[Depends(require_applicant)])


# --- QUẢN LÝ SKILL MASTER (ADMIN) ---

@admin_router.post(
    "/",
    response_model=ResponseSchema[SkillResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Skill",
    description="Admin thêm kỹ năng mới vào danh mục hệ thống."
)
def create_skill(
    skill: SkillCreate,
    db: Session = Depends(get_db),
):
    data = skill_service.create_skill_service(db, skill)
    return ResponseSchema[SkillResponse](
        success=True,
        message="Skill created successfully",
        data=data
    )


@admin_router.patch(
    "/{skill_id}",
    response_model=ResponseSchema[SkillResponse],
    summary="Update Skill",
    description="Admin cập nhật thông tin kỹ năng trong danh mục hệ thống."
)
def update_skill(
    skill_id: int,
    skill: SkillUpdate,
    db: Session = Depends(get_db),
):
    data = skill_service.update_skill_service(db, skill_id, skill)
    return ResponseSchema[SkillResponse](
        success=True,
        message="Skill updated successfully",
        data=data
    )


@admin_router.delete(
    "/{skill_id}",
    response_model=ResponseSchema,
    summary="Delete Skill",
    description="Admin xóa kỹ năng khỏi danh mục hệ thống."
)
def delete_skill_master(
    skill_id: int,
    db: Session = Depends(get_db),
):
    skill_service.delete_skill_master_service(db, skill_id)
    return ResponseSchema(
        success=True,
        message="Skill deleted successfully",
        data=None
    )


# --- QUẢN LÝ CV SKILL (APPLICANT) ---

@applicant_router.post(
    "/me/skills",
    response_model=ResponseSchema[CVSkillResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add Skill to CV",
    description="Gắn một kỹ năng từ danh mục hệ thống vào hồ sơ CV."
)
def add_skill(
    skill: CVSkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    data = skill_service.add_skill_to_cv(db, current_user.Id, skill)
    if not data:
        raise HTTPException(status_code=403, detail="CVId không hợp lệ hoặc quyền truy cập bị từ chối.")
    return ResponseSchema[CVSkillResponse](
        success=True,
        message="Skill added successfully",
        data=data
    )


@applicant_router.patch(
    "/me/skills/{cv_id}/{cv_skill_id}",
    response_model=ResponseSchema[CVSkillResponse],
    summary="Update CV Skill",
    description="Cập nhật Confidence hoặc Source của một kỹ năng đã gắn vào hồ sơ CV."
)
def patch_skill(
    cv_id: int,
    cv_skill_id: int,
    skill: CVSkillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    data = skill_service.patch_skill_service(
        db=db,
        cv_skill_id=cv_skill_id,
        cv_id=cv_id,
        user_id=current_user.Id,
        update_data=skill
    )
    return ResponseSchema[CVSkillResponse](
        success=True,
        message="Skill updated successfully",
        data=data
    )


@applicant_router.delete(
    "/me/skills/{cv_id}/{cv_skill_id}",
    response_model=ResponseSchema,
    summary="Remove CV Skill",
    description="Xóa kỹ năng khỏi hồ sơ ứng viên."
)
def delete_skill(
    cv_id: int,
    cv_skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    skill_service.delete_skill_service(
        db=db,
        cv_skill_id=cv_skill_id,
        cv_id=cv_id,
        user_id=current_user.Id
    )
    return ResponseSchema(
        success=True,
        message="Skill removed successfully",
        data=None
    )


router.include_router(admin_router)
router.include_router(applicant_router)