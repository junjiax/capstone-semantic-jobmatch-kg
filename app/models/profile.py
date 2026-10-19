from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enum import ProfileFileType

if TYPE_CHECKING:
    from app.models.User import User
    from app.models.profile_edu import ProfileEdu
    from app.models.profile_skill import ProfileSkill
    from app.models.profile_work_exp import ProfileWorkExp
    from app.models.result import Result


def _profile_file_type_values(
    file_type_enum: type[ProfileFileType],
) -> list[str]:
    return [file_type.value for file_type in file_type_enum.__members__.values()]


class Profile(Base):
    __tablename__ = "PROFILE"

    UserId: Mapped[int] = mapped_column(ForeignKey("USER.id"), nullable=False)
    FileUrl: Mapped[str | None] = mapped_column(Text, nullable=True)
    FileType: Mapped[ProfileFileType] = mapped_column(
        SQLEnum(
            ProfileFileType,
            name="profilefiletype",
            values_callable=_profile_file_type_values,
        ),
        default=ProfileFileType.PDF,
        nullable=False,
    )
    Title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    RawText: Mapped[str | None] = mapped_column(Text, nullable=True)
    CleanText: Mapped[str | None] = mapped_column(Text, nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="profiles")
    skills: Mapped[list["ProfileSkill"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    educations: Mapped[list["ProfileEdu"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    work_experiences: Mapped[list["ProfileWorkExp"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    results: Mapped[list["Result"]] = relationship(back_populates="profile")
