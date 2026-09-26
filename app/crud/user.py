
from typing import Optional

from sqlalchemy.orm import Session

from app.models.User import User, UserRole

# ─── READ ────────────────────────────────────────────────────

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Tìm user theo primary key. Trả None nếu không tồn tại."""
    return db.query(User).filter(User.Id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Tìm user theo email (unique). Dùng khi đăng nhập hoặc kiểm tra trùng."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_reset_token(db: Session, token: str) -> Optional[User]:
    """Tìm user đang giữ reset_token cụ thể (dùng khi đặt lại mật khẩu)."""
    return db.query(User).filter(User.reset_token == token).first()


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
) -> tuple[list[User], int]:
    query = db.query(User)

    if role is not None:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    total = query.count()
    users = (
        query
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return users, total


# ─── CREATE ──────────────────────────────────────────────────

def create_user(db: Session, **kwargs) -> User:
    user = User(**kwargs)
    db.add(user)
    db.commit()
    db.refresh(user) 
    return user


# ─── UPDATE ──────────────────────────────────────────────────

def update_user(db: Session, user: User, **kwargs) -> User:
    for field, value in kwargs.items():
        if value is not None:
            setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def save_user(db: Session, user: User) -> User:
    db.commit()
    db.refresh(user)
    return user


# ─── DELETE ──────────────────────────────────────────────────

def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()