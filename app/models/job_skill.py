from typing import TYPE_CHECKING, Optional
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.skill import Skill

class JobSkill(Base):
    __tablename__ = "JobSkills"
    __table_args__ = (
        UniqueConstraint("JobId", "SkillId", name="uq_job_skill"),
    )
    
    JobId: Mapped[int] = mapped_column(ForeignKey("Jobs.Id"))
    SkillId: Mapped[int] = mapped_column(ForeignKey("Skills.Id"))
    Importance: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), server_default="1.0")
    MinYears: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 1))

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="required_skills")
    skill: Mapped["Skill"] = relationship(back_populates="job_skills")