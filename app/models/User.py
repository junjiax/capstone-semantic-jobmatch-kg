from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enum import UserRole

if TYPE_CHECKING:
    from app.models.profile import Profile


def _user_role_values(role_enum: type[UserRole]) -> list[str]:
    return [
        role.value
        for name, role in role_enum.__members__.items()
        if name == role.name
    ]


class User(Base):
    __tablename__ = "USER"

    Email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    FullName: Mapped[str] = mapped_column(String(255))
    Phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    HashedPassword: Mapped[str] = mapped_column(String(255))
    Role: Mapped[UserRole] = mapped_column(
        SQLEnum(
            UserRole,
            name="userrole",
            values_callable=_user_role_values,
        ),
        default=UserRole.CANDIDATE,
        nullable=False,
    )
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    IsVerified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ResetToken: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ResetTokenExpires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    CreatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    UpdatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    profiles: Mapped[list["Profile"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.Id} email={self.Email!r} role={self.Role}>"
