from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector  # type: ignore[reportMissingTypeStubs]
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.profile import Profile


class ProfileSkill(Base):
    __tablename__ = "PROFILE_SKILL"

    ProfileId: Mapped[int] = mapped_column(ForeignKey("PROFILE.id"), nullable=False)
    SkillTitle: Mapped[str] = mapped_column(String(200), nullable=False)
    Vector: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    profile: Mapped["Profile"] = relationship(back_populates="skills")
