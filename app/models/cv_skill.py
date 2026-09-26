from typing import TYPE_CHECKING, Optional
from decimal import Decimal

from sqlalchemy import String, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


if TYPE_CHECKING:
    from app.models.cv import CV
    from app.models.skill import Skill

class CVSkill(Base):
    __tablename__ = "CVSkills"
    __table_args__ = (UniqueConstraint("CVId", "SkillId", name="uq_cv_skill"),)

    CVId: Mapped[int] = mapped_column(ForeignKey("CVs.Id"))
    SkillId: Mapped[int] = mapped_column(ForeignKey("Skills.Id"))
    Confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    Source: Mapped[Optional[str]] = mapped_column(String(100))

    cv: Mapped["CV"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship(back_populates="cv_skills")