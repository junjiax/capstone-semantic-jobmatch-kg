from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Column, DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SQLEnum

from app.core.database import Base
from app.models.enum import UserRole, UserStatus

if TYPE_CHECKING:
    from app.models.screen_batch import ScreeningBatch

class User(Base):
    __tablename__ = "users"

    # ── Thông tin định danh ──────────────────────────────
    email     = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    phone     = Column(String(20),  nullable=True)

    # ── Xác thực ─────────────────────────────────────────
    hashed_password = Column(String(255), nullable=False)

    # ── Phân quyền & trạng thái ──────────────────────────
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(
            UserRole,
            values_callable=lambda obj: [e.value for e in obj]
        ),
        default=UserRole.APPLICANT,
    )    
    is_active   = Column(Boolean, default=True,  nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # ── Reset mật khẩu (lưu tạm, xóa sau khi dùng) ──────
    reset_token         = Column(String(512), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)

    # ── Timestamps ───────────────────────────────────────
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    cvs = relationship("CV", back_populates="user")
    batches: Mapped[list["ScreeningBatch"]] = relationship(
    back_populates="user"
    )
    applications = relationship("Application", back_populates="applicant", foreign_keys="Application.ApplicantId")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
