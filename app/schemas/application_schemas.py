from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ── Enums ─────────────────────────────────────────────────────────────────────
class ApplicationStatusEnum(str, Enum):
    APPLIED = "APPLIED"
    SHORTLISTED = "SHORTLISTED"
    INTERVIEW = "INTERVIEW"
    REJECTED = "REJECTED"
    HIRED = "HIRED"


# ── Application schemas ───────────────────────────────────────────────────────
class ApplicationCreate(BaseModel):
    JobId: int
    CVId: int
    CoverLetter: Optional[str] = None


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatusEnum
    note: Optional[str] = Field(default=None, max_length=1000)


class ApplicationResponse(BaseModel):
    Id: int
    JobId: int
    job_title: Optional[str] = None
    CVId: int
    ApplicantId: int
    applicant_name: Optional[str] = None
    Status: ApplicationStatusEnum
    CoverLetter: Optional[str] = None
    AppliedAt: datetime
    UpdatedAt: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationHistoryResponse(BaseModel):
    Id: int
    Status: ApplicationStatusEnum
    Note: Optional[str] = None
    ChangedAt: datetime
    ChangedById: Optional[int] = None
    changed_by: Optional[str] = None

    model_config = {"from_attributes": True}


class ApplicationDetailResponse(ApplicationResponse):
    history: List[ApplicationHistoryResponse] = []
