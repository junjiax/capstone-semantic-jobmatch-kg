

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models.User import UserRole



class UserRegister(BaseModel):

    email:            EmailStr
    full_name:        str = Field(..., min_length=2,  max_length=255, examples=["Nguyen Van A"])
    phone:            Optional[str] = Field(None, max_length=20, examples=["0901234567"])
    password:         str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "UserRegister":
        if self.password != self.confirm_password:
            raise ValueError("Mật khẩu xác nhận không khớp")
        return self


class UserUpdate(BaseModel):
    """Người dùng tự cập nhật hồ sơ của mình (chỉ tên & SĐT)."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone:     Optional[str] = Field(None, max_length=20)


class UserUpdateByHR(UserUpdate):
    """
    HR cập nhật thông tin user.
    Thêm quyền thay đổi role và kích hoạt/khóa tài khoản.
    """
    role:      Optional[UserRole] = None
    is_active: Optional[bool]     = None


class PasswordChange(BaseModel):
    """Đổi mật khẩu — bắt buộc nhập mật khẩu hiện tại để xác nhận."""
    current_password:  str
    new_password:      str = Field(..., min_length=8, max_length=128)
    confirm_new_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "PasswordChange":
        if self.new_password != self.confirm_new_password:
            raise ValueError("Mật khẩu mới xác nhận không khớp")
        return self


class ForgotPasswordRequest(BaseModel):
    """Gửi email đặt lại mật khẩu."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Đặt lại mật khẩu bằng token nhận từ email."""
    token:                str
    new_password:         str = Field(..., min_length=8, max_length=128)
    confirm_new_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "ResetPasswordRequest":
        if self.new_password != self.confirm_new_password:
            raise ValueError("Mật khẩu xác nhận không khớp")
        return self


class RefreshTokenRequest(BaseModel):
    """Dùng refresh token để lấy cặp token mới."""
    refresh_token: str


# ════════════════════════════════════════════════════════
# OUTPUT SCHEMAS (Response)
# ════════════════════════════════════════════════════════

class UserResponse(BaseModel):
    """
    Hồ sơ đầy đủ — trả về cho chính người dùng đó.
    Bao gồm role, trạng thái, timestamps.
    """
    Id:          int
    email:       EmailStr
    full_name:   str
    phone:       Optional[str]
    role:        UserRole
    is_active:   bool
    is_verified: bool
    created_at:  datetime
    updated_at:  datetime

    model_config = {"from_attributes": True}


class UserPublicResponse(BaseModel):
    """
    Hồ sơ rút gọn — HR dùng khi xem danh sách ứng viên.
    Loại bỏ thông tin nhạy cảm (is_verified, timestamps...).
    """
    Id:        int
    email:     EmailStr
    full_name: str
    phone:     Optional[str]
    role:      UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Cặp token trả về sau khi đăng nhập hoặc refresh."""
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


class PaginatedUsers(BaseModel):
    """Danh sách users có metadata phân trang."""
    total:     int
    page:      int
    page_size: int
    items:     list[UserPublicResponse]

class HRCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)