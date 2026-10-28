from datetime import date, datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector  # type: ignore[reportMissingTypeStubs]
from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.profile import Profile


class ProfileWorkExp(Base):
    __tablename__ = "PROFILE_WORK_EXP"

    ProfileId: Mapped[int] = mapped_column(ForeignKey("PROFILE.id"), nullable=False)
    Domain: Mapped[str | None] = mapped_column(String(200), nullable=True)
    Expertise: Mapped[str | None] = mapped_column(String(200), nullable=True)
    Responsibility: Mapped[str | None] = mapped_column(Text, nullable=True)
    StartDate: Mapped[date | None] = mapped_column(Date, nullable=True)
    EndDate: Mapped[date | None] = mapped_column(Date, nullable=True)
    Vector: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    profile: Mapped["Profile"] = relationship(back_populates="work_experiences")
