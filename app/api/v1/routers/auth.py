from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.User import User
from app.services import user_service
from app.api.v1.schemas.user import (
    ForgotPasswordRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserRegister,
    UserResponse,
)

router = APIRouter()


# ─── ĐĂNG KÝ ─────────────────────────────────────────────────


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản",
    description="""
    Ứng viên tự đăng ký tài khoản mới trên hệ thống.
    - Email phải chưa được đăng ký
    - Mật khẩu tối thiểu **8 ký tự**
    - Tự động gán vai trò **Applicant**
    """,
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db),
):
    return user_service.register_user(db, data)


# ─── ĐĂNG NHẬP ───────────────────────────────────────────────


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Đăng nhập",
    description="""
    Đăng nhập bằng JSON body:
    {
        "email": "example@gmail.com",
        "password": "12345678"
    }
    """,
)
async def login(
    body: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    return user_service.login_user(db, email=body.username, password=body.password)


# ─── ĐĂNG XUẤT ───────────────────────────────────────────────


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Đăng xuất",
    description="""
    Kết thúc phiên làm việc.
    Client cần tự xóa token khỏi bộ nhớ (localStorage / cookie).

    > 💡 Để hỗ trợ **token blacklist** phía server, tích hợp Redis ở bước sau.
    """,
)
async def logout(
    _: User = Depends(get_current_active_user),
):
    return {"message": "Đăng xuất thành công."}


# ─── LÀM MỚI TOKEN ───────────────────────────────────────────


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Làm mới Access Token",
    description="Dùng `refresh_token` để lấy cặp token mới khi `access_token` hết hạn.",
)
async def refresh_token(
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    return user_service.refresh_user_tokens(db, body.refresh_token)


# ─── QUÊN MẬT KHẨU ───────────────────────────────────────────


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Quên mật khẩu",
    description="""
    Gửi link đặt lại mật khẩu đến email đã đăng ký.
    **Luôn trả về thành công** dù email tồn tại hay không
    (bảo vệ khỏi email enumeration attack).
    """,
)
async def forgot_password(
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    user_service.forgot_password(db, body.email)
    return {
        "message": "Nếu email này tồn tại trong hệ thống, link đặt lại mật khẩu đã được gửi."
    }


# ─── ĐẶT LẠI MẬT KHẨU ───────────────────────────────────────


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Đặt lại mật khẩu",
    description="Đặt mật khẩu mới bằng token nhận từ email. Token chỉ dùng được **1 lần**.",
)
async def reset_password(
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    user_service.reset_password(db, token=body.token, new_password=body.new_password)
    return {"message": "Mật khẩu đã được đặt lại thành công. Vui lòng đăng nhập lại."}
