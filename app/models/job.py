from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from decimal import Decimal

from sqlalchemy import String, Text, Numeric, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enum import JobStatus, EducationLevel as EducationLevelEnum
from app.models.application import Application



if TYPE_CHECKING:
    from app.models.cv import CV
    from app.models.job_skill import JobSkill
    from app.models.match_result import MatchResult
    from app.models.screen_batch import ScreeningBatch
    from app.models.job_embedding import JobEmbedding

class Job(Base):
    __tablename__ = "Jobs"

    Title: Mapped[str] = mapped_column(String(200))
    Description: Mapped[Optional[str]] = mapped_column(Text)
    RequirementsText: Mapped[Optional[str]] = mapped_column(Text)
    MinExperience: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 1))
    EducationLevel: Mapped[Optional[EducationLevelEnum]] = mapped_column(
        SQLEnum(EducationLevelEnum),
        nullable=True, default=EducationLevelEnum.BACHELOR)
    Status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus), 
        default=JobStatus.DRAFT
    )
    CreatedAt: Mapped[datetime] = mapped_column(server_default=func.now())


# --- Relationships ---
    applications: Mapped[List["Application"]] = relationship(
    back_populates="job",
    cascade="all, delete-orphan")

    required_skills: Mapped[List["JobSkill"]] = relationship(
        back_populates="job", 
        cascade="all, delete-orphan")
    
    match_results: Mapped[List["MatchResult"]] = relationship(back_populates="job")

    batches: Mapped[List["ScreeningBatch"]] = relationship(
        back_populates="job", 
        cascade="all, delete-orphan")
    
    embeddings: Mapped[List["JobEmbedding"]] = relationship(back_populates="job")
    embeddings: Mapped[List["JobEmbedding"]] = relationship(back_populates="job")
    cvs: Mapped[List["CV"]] = relationship(back_populates="position")
