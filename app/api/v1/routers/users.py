
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user, require_admin, require_hr
from app.models.User import User, UserRole
from app.services import user_service
from app.api.v1.schemas.user import (
    HRCreate,
    PaginatedUsers,
    PasswordChange,
    UserPublicResponse,
    UserResponse,
    UserUpdate,
    UserUpdateByHR,
)

router = APIRouter()


# ════════════════════════════════════════════════════════
# PROFILE — Người dùng quản lý hồ sơ bản thân
# ════════════════════════════════════════════════════════

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Xem hồ sơ bản thân",
)
def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """Trả về toàn bộ thông tin hồ sơ của người dùng đang đăng nhập."""
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Cập nhật hồ sơ bản thân",
)
def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    return user_service.update_profile(db, current_user, data)


@router.put(
    "/me/password",
    status_code=status.HTTP_200_OK,
    summary="Đổi mật khẩu",
)
def change_my_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):

    user_service.change_password(db, current_user, data)
    return {"message": "Mật khẩu đã được thay đổi thành công."}


# ════════════════════════════════════════════════════════
# HR — Quản lý toàn bộ người dùng
# ════════════════════════════════════════════════════════

@router.get(
    "/",
    response_model=PaginatedUsers,
    summary="[HR] Danh sách người dùng",
    description="Lấy danh sách users có phân trang và bộ lọc. **Chỉ HR.**",
)
def list_users(
    page:      int                = Query(1,  ge=1, description="Trang hiện tại"),
    page_size: int                = Query(20, ge=1, le=100, description="Số bản ghi mỗi trang"),
    role:      Optional[UserRole] = Query(None, description="Lọc theo vai trò"),
    is_active: Optional[bool]     = Query(None, description="Lọc theo trạng thái"),
    _: User = Depends(require_hr),
    db: Session = Depends(get_db),
):
    users, total = user_service.list_users(db, page, page_size, role, is_active)
    return PaginatedUsers(total=total, page=page, page_size=page_size, items=users)


@router.get(
    "/{user_id}",
    response_model=UserPublicResponse,
    summary="[HR] Xem hồ sơ người dùng",
    description="Xem thông tin của bất kỳ user nào. **Chỉ HR.**",
)
def get_user(
    user_id: int,
    _: User = Depends(require_hr),
    db: Session = Depends(get_db),
):
    return user_service.get_user(db, user_id)


@router.put(
    "/{user_id}",
    response_model=UserPublicResponse,
    summary="[HR] Cập nhật người dùng",
    description="""
    HR cập nhật thông tin user bất kỳ.
    Bao gồm: `full_name`, `phone`, `role`, `is_active`.
    **Chỉ HR.**
    """,
)
def update_user(
    user_id: int,
    data: UserUpdateByHR,
    _: User = Depends(require_hr),
    db: Session = Depends(get_db),
):
    return user_service.update_user_by_hr(db, user_id, data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[HR] Xóa người dùng",
    description="Xóa vĩnh viễn tài khoản. **Chỉ HR.** Hành động không thể hoàn tác.",
)
def delete_user(
    user_id: int,
    _: User = Depends(require_hr),
    db: Session = Depends(get_db),
):
    user_service.delete_user(db, user_id)



@router.post(
    "/admin/create-hr",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[ADMIN] Tạo tài khoản HR",
    description="Chỉ ADMIN mới được tạo tài khoản HR."
)
def create_hr(
    data: HRCreate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return user_service.create_hr(db, data)