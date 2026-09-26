
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

from app.crud import user as user_crud
from app.models.User import User, UserRole
from app.api.v1.schemas.user import (
    PasswordChange,
    TokenResponse,
    UserRegister,
    UserUpdate,
    UserUpdateByHR,
)

# =========================================================

# =========================================================

def register_user(db: Session, data: UserRegister) -> User:

    if user_crud.get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email này đã được đăng ký."
        )

    return user_crud.create_user(
        db=db,
        email=data.email,
        full_name=data.full_name,
        phone=data.phone,
        hashed_password=hash_password(data.password),
        role=UserRole.APPLICANT,
    )


# def login_user(db: Session, email: str, password: str) -> TokenResponse:

#     user = user_crud.get_user_by_email(db, email)

#     if not user or not verify_password(password, user.hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Email hoặc mật khẩu không chính xác."
#         )

#     if not user.is_active:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Tài khoản đã bị khóa."
#         )

#     return _build_token_response(user)

def login_user(db: Session, email: str, password: str) -> TokenResponse:
    user: User | None = user_crud.get_user_by_email(db, email)

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên."
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vui lòng xác thực email trước khi đăng nhập."
        )

    return _build_token_response(user)

def refresh_user_tokens(db: Session, refresh_token: str) -> TokenResponse:

    payload = decode_token(refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token không hợp lệ."
        )

    user = user_crud.get_user_by_id(db, int(payload["sub"]))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không tìm thấy người dùng."
        )

    return _build_token_response(user)



# =========================================================
# PROFILE
# =========================================================

def get_user(db: Session, user_id: int) -> User:

    user = user_crud.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy user {user_id}"
        )

    return user


def update_profile(db: Session, user: User, data: UserUpdate) -> User:

    fields = data.model_dump(exclude_none=True)

    return user_crud.update_user(db, user, **fields)


def update_user_by_hr(db: Session, user_id: int, data: UserUpdateByHR) -> User:

    user = get_user(db, user_id)

    fields = data.model_dump(exclude_none=True)

    return user_crud.update_user(db, user, **fields)


def list_users(
    db: Session,
    page: int,
    page_size: int,
    role: UserRole | None,
    is_active: bool | None,
):

    skip = (page - 1) * page_size

    return user_crud.get_users(
        db=db,
        skip=skip,
        limit=page_size,
        role=role,
        is_active=is_active,
    )


def delete_user(db: Session, user_id: int) -> None:

    user = get_user(db, user_id)

    user_crud.delete_user(db, user)


# =========================================================
# PASSWORD
# =========================================================

def change_password(db: Session, user: User, data: PasswordChange) -> None:

    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu hiện tại không chính xác."
        )

    user_crud.update_user(
        db,
        user,
        hashed_password=hash_password(data.new_password),
    )


def reset_password(db: Session, token: str, new_password: str) -> None:

    payload = decode_token(token)

    if payload is None or payload.get("type") != "reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token không hợp lệ."
        )

    user = user_crud.get_user_by_reset_token(db, token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token không hợp lệ."
        )

    if user.reset_token_expires and user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token đã hết hạn."
        )

    user.hashed_password = hash_password(new_password)
    user.reset_token = None
    user.reset_token_expires = None

    user_crud.save_user(db, user)


# =========================================================
# INTERNAL
# =========================================================

def _build_token_response(user: User) -> TokenResponse:

    user_id = getattr(user, "id", None) or getattr(user, "Id", None)

    return TokenResponse(
        access_token=create_access_token(
            user_id=user_id,
            email=user.email,
            role=user.role.value if hasattr(user.role, "value") else user.role,
        ),
        refresh_token=create_refresh_token(user_id=user_id),
    )



def create_hr(db, data):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email đã tồn tại."
        )

    hr = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.HR,
        is_active=True,
        is_verified=True,  # HR tạo bởi admin thì auto verified
    )

    db.add(hr)
    db.commit()
    db.refresh(hr)
    return hr