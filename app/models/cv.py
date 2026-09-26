from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.enum import CVFileType
from sqlalchemy import Enum as SQLEnum

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.cv_skill import CVSkill
    from app.models.experience import Experience
    from app.models.education import Education
    from app.models.cv_embedding import CVEmbedding
    from app.models.match_result import MatchResult
    from app.models.application import Application

class CV(Base):
    __tablename__ = "CVs"

    UserId: Mapped[int] = mapped_column(ForeignKey("users.Id"))
    FileUrl: Mapped[str] = mapped_column(String(500))
    FileType: Mapped[Optional[CVFileType]] = mapped_column(
        SQLEnum(CVFileType),
        nullable=True,
        default=CVFileType.PDF) 

    RawText: Mapped[Optional[str]] = mapped_column(Text)
    CleanText: Mapped[Optional[str]] = mapped_column(Text)
    Summary: Mapped[Optional[str]] = mapped_column(Text)
    Language: Mapped[Optional[str]] = mapped_column(String(20), server_default="en")
    CreatedAt: Mapped[datetime] = mapped_column(server_default=func.now())
    PositionId: Mapped[Optional[int]] = mapped_column(ForeignKey("Jobs.Id"), nullable=True)

    # --- Relationships ---

    user = relationship("User", back_populates="cvs")
    skills: Mapped[List["CVSkill"]] = relationship(
        back_populates="cv", cascade="all, delete-orphan"
    )
    experiences: Mapped[List["Experience"]] = relationship(
        back_populates="cv", cascade="all, delete-orphan"
    )
    educations: Mapped[List["Education"]] = relationship(
        back_populates="cv", cascade="all, delete-orphan"
    )
    embeddings: Mapped[List["CVEmbedding"]] = relationship(
        back_populates="cv", cascade="all, delete-orphan"
    )
    match_results: Mapped[List["MatchResult"]] = relationship(back_populates="cv"
    )
    applications: Mapped[List["Application"]] = relationship(back_populates="cv"
    )
    position: Mapped[Optional["Job"]] = relationship(back_populates="cvs")
    match_results: Mapped[List["MatchResult"]] = relationship(back_populates="cv")
