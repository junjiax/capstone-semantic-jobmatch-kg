from datetime import datetime
from typing import TYPE_CHECKING, Optional
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.cv import CV
    from app.models.job import Job

class MatchResult(Base):
    __tablename__ = "MatchResults"
    __table_args__ = (
        UniqueConstraint("CVId", "JobId", name="uq_cv_job_match"),
    )

    CVId: Mapped[int] = mapped_column(ForeignKey("CVs.Id"))
    JobId: Mapped[int] = mapped_column(ForeignKey("Jobs.Id"))
    
    SemanticScore: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    SkillScore: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    ExperienceScore: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    EducationScore: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    TotalScore: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    
    Rank: Mapped[Optional[int]] = mapped_column(Integer)
    EvaluatedAt: Mapped[datetime] = mapped_column(server_default=func.now())

    cv: Mapped["CV"] = relationship(back_populates="match_results")
    job: Mapped["Job"] = relationship(back_populates="match_results")