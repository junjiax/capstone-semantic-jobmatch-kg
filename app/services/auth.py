from collections.abc import Mapping
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import (
    RESET_TOKEN_EXPIRE_SECONDS,
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
    hash_password,
    verify_password,
)

from app.persist.postgres import user as UserPersist
from app.models.user import User, UserRole
from app.api.v1.schemas.user import (
    PasswordChange,
    TokenResponse,
    UserRegister,
    UserUpdate,
)


def _parse_user_record(
    record: UserRegister | Mapping[str, object],
) -> UserRegister:
    """Validate registration data and return the schema used by register_user."""
    if isinstance(record, UserRegister):
        return record

    return UserRegister.model_validate(record)


def register_user(db: Session, data: UserRegister) -> User:
    parsed_data = _parse_user_record(data)

    if UserPersist.get_user_by_email(db, str(parsed_data.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email này đã được đăng ký."
        )

    return UserPersist.create_user(
        db=db,
        Email=str(parsed_data.email),
        FullName=parsed_data.full_name,
        Phone=parsed_data.phone,
        HashedPassword=hash_password(parsed_data.password),
        Role=UserRole.CANDIDATE,
    )


def login_user(db: Session, email: str, password: str) -> TokenResponse:
    user: User | None = UserPersist.get_user_by_email(db, email)

    if not user or not verify_password(password, user.HashedPassword):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác.",
        )

    if not user.IsActive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.",
        )

    # if not user.IsVerified:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Vui lòng xác thực email trước khi đăng nhập.",
    #     )

    return _build_token_response(user)


def refresh_user_tokens(db: Session, refresh_token: str) -> TokenResponse:
    payload = decode_token(refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ.",
        )

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.isdecimal():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ.",
        )

    user = UserPersist.get_user_by_id(db, int(subject))
    if not user or not user.IsActive or not user.IsVerified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không tìm thấy người dùng.",
        )

    return _build_token_response(user)


# PROFILE
# =========================================================


def get_user(db: Session, user_id: int) -> User:

    user = UserPersist.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy user {user_id}",
        )

    return user


def update_profile(db: Session, user: User, data: UserUpdate) -> User:
    fields = data.model_dump(exclude_none=True)
    mapped_fields = {
        model_field: fields[schema_field]
        for schema_field, model_field in (("full_name", "FullName"), ("phone", "Phone"))
        if schema_field in fields
    }
    return UserPersist.update_user(db, user, **mapped_fields)


def list_users(
    db: Session,
    page: int,
    page_size: int,
    role: UserRole | None,
    is_active: bool | None,
) -> tuple[list[User], int]:
    skip = (page - 1) * page_size

    return UserPersist.get_users(
        db=db,
        skip=skip,
        limit=page_size,
        role=role.value if role is not None else None,
        is_active=is_active,
    )


def delete_user(db: Session, user_id: int) -> None:

    user = get_user(db, user_id)

    UserPersist.delete_user(db, user)


# =========================================================
# PASSWORD
# =========================================================


async def forgot_password(db: Session, email: str) -> None:
    """Tạo token reset mật khẩu cho email nếu user tồn tại.

    Luôn trả về thành công để tránh email enumeration attack.
    """
    user = UserPersist.get_user_by_email(db, email)

    if not user:
        return

    reset_token = create_reset_token(user.Email)
    user.ResetToken = reset_token
    user.ResetTokenExpires = datetime.now(timezone.utc) + timedelta(
        seconds=RESET_TOKEN_EXPIRE_SECONDS
    )

    UserPersist.save_user(db, user)


def change_password(db: Session, user: User, data: PasswordChange) -> None:
    if not verify_password(data.current_password, user.HashedPassword):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu hiện tại không chính xác.",
        )

    user.HashedPassword = hash_password(data.new_password)
    UserPersist.save_user(db, user)


def reset_password(db: Session, token: str, new_password: str) -> None:
    if not 8 <= len(new_password) <= 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu phải có từ 8 đến 128 ký tự.",
        )

    payload = decode_token(token)
    if payload is None or payload.get("type") != "reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token không hợp lệ."
        )

    user = UserPersist.get_user_by_reset_token(db, token)
    if not user or payload.get("sub") != user.Email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token không hợp lệ."
        )

    expires_at = user.ResetTokenExpires
    if expires_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token không hợp lệ."
        )
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Token đã hết hạn."
        )

    user.HashedPassword = hash_password(new_password)
    user.ResetToken = None
    user.ResetTokenExpires = None
    UserPersist.save_user(db, user)


# INTERNAL
# =========================================================


def _build_token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(
            user_id=user.Id,
            email=user.Email,
            role=user.Role.value,
        ),
        refresh_token=create_refresh_token(user_id=user.Id),
    )
