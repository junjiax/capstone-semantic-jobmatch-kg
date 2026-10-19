from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enum import EducationLevel

if TYPE_CHECKING:
    from app.models.profile import Profile


class ProfileEdu(Base):
    __tablename__ = "PROFILE_EDU"

    ProfileId: Mapped[int] = mapped_column(ForeignKey("PROFILE.id"), nullable=False)
    Degree: Mapped[str | None] = mapped_column(String(200), nullable=True)
    Major: Mapped[str | None] = mapped_column(String(200), nullable=True)
    School: Mapped[str | None] = mapped_column(String(200), nullable=True)
    Level: Mapped[EducationLevel | None] = mapped_column(
        SQLEnum(EducationLevel, name="educationlevel"), nullable=True
    )
    GraduationYear: Mapped[int | None] = mapped_column(Integer, nullable=True)
    GPA: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    Vector: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    profile: Mapped["Profile"] = relationship(back_populates="educations")
