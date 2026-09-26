from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, ForeignKey, DateTime, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from enum import Enum

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.cv import CV
    from app.models.User import User


class ApplicationStatus(str, Enum):
    APPLIED = "APPLIED"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW = "INTERVIEW"
    REJECTED = "REJECTED"
    HIRED = "HIRED"


class Application(Base):
    """Ứng viên nộp CV vào vị trí tuyển dụng."""
    __tablename__ = "Applications"
    __table_args__ = (
        UniqueConstraint("JobId", "CVId", name="uq_job_cv"),
    )

    JobId: Mapped[int] = mapped_column(ForeignKey("Jobs.Id"), nullable=False)
    CVId: Mapped[int] = mapped_column(ForeignKey("CVs.Id"), nullable=False)
    ApplicantId: Mapped[int] = mapped_column(ForeignKey("users.Id"), nullable=False)

    Status: Mapped[ApplicationStatus] = mapped_column(
        SQLEnum(ApplicationStatus),
        default=ApplicationStatus.APPLIED,
        nullable=False,
    )
    CoverLetter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    AppliedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    UpdatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="applications")
    cv: Mapped["CV"] = relationship(back_populates="applications")
    applicant: Mapped["User"] = relationship(back_populates="applications")
    history: Mapped[List["ApplicationHistory"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationHistory.ChangedAt",
    )


class ApplicationHistory(Base):
    """Lịch sử thay đổi trạng thái ứng tuyển."""
    __tablename__ = "ApplicationHistories"

    ApplicationId: Mapped[int] = mapped_column(
        ForeignKey("Applications.Id"), nullable=False
    )
    Status: Mapped[ApplicationStatus] = mapped_column(
        SQLEnum(ApplicationStatus), nullable=False
    )
    Note: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    ChangedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ChangedById: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.Id"), nullable=True
    )

    # Relationships
    application: Mapped["Application"] = relationship(back_populates="history")
    changed_by_user: Mapped[Optional["User"]] = relationship(foreign_keys=[ChangedById])
