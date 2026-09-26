from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal
from app.models.enum import JobStatus, EducationLevel as EducationLevelEnum

# Schema cơ sở chứa các thông tin chung của vị trí công việc
class JobBase(BaseModel):
    Title: str = Field(..., max_length=200)
    Description: Optional[str] = None
    RequirementsText: Optional[str] = None
    MinExperience: Optional[Decimal] = Field(None, max_digits=3, decimal_places=1)
    EducationLevel: Optional[EducationLevelEnum] = EducationLevelEnum.BACHELOR
    Status: JobStatus = JobStatus.DRAFT

# Schema trả về dữ liệu cho Frontend
class JobResponse(JobBase):
    Id: int 
    CreatedAt: datetime
    Status: JobStatus

    model_config = ConfigDict(from_attributes=True)

# Schema dùng để tạo tin tuyển dụng mới
class JobCreate(JobBase):
    pass

class JobFilter(BaseModel):
    title: Optional[str] = None
    requirement: Optional[str] = None
    status: Optional[JobStatus] = None

# Schema hỗ trợ cập nhật tin tuyển dụng (tất cả các trường đều là Optional)
class JobUpdate(BaseModel):
    Title: Optional[str] = None
    Description: Optional[str] = None
    RequirementsText: Optional[str] = None
    MinExperience: Optional[Decimal] = None
    EducationLevel: Optional[EducationLevelEnum] = None
    Status: Optional[JobStatus] = None

