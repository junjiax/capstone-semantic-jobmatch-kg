from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User
from app.services import auth
from app.api.v1.schemas.user import (
    PasswordChange,
    UserResponse,
    UserUpdate,
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
    return auth.update_profile(db, current_user, data)


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
    auth.change_password(db, current_user, data)
    return {"message": "Mật khẩu đã được thay đổi thành công."}
