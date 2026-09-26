from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, Optional
from app.api.v1.schemas.education import EducationResponse
from app.api.v1.schemas.experience import ExperienceResponse
from app.api.v1.schemas.skill import CVSkillResponse
from app.models.enum import CVFileType


from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class CVUploadResponse(BaseModel):
    cv_id: int
    file_url: str

    class Config:
        from_attributes = True

class PersonalInfoBase(BaseModel):
    Summary: Optional[str] = None
    Language: Optional[str] = Field("en", max_length=20)

class PersonalInfoUpdate(BaseModel):
    Summary: Optional[str] = None
    Language: Optional[str] = None

class PersonalInfoResponse(PersonalInfoBase):
    Id: int
    model_config = ConfigDict(from_attributes=True)
    
# Schema cơ sở chứa các thông tin cốt lõi của một bản CV
class CVBase(BaseModel):
    UserId: int
    FileUrl: str
    FileType: Optional[CVFileType] = CVFileType.PDF
    Language: Optional[str] = "en"

# Schema dùng cho việc upload hoặc tạo mới CV
class CVCreate(CVBase):
    RawText: Optional[str] = None
    CleanText: Optional[str] = None
    Summary: Optional[str] = None

# Schema hỗ trợ cập nhật từng phần thông tin
class CVUpdate(BaseModel):
    FileUrl: Optional[str] = None
    FileType: Optional[CVFileType] = None
    RawText: Optional[str] = None
    CleanText: Optional[str] = None
    Summary: Optional[str] = None
    Language: Optional[str] = None

class CVFilter(BaseModel):
    FileType: Optional[CVFileType] = Field(None, description="Lọc theo loại file (PDF/DOCX)")
    Language: Optional[str] = Field(None, description="Lọc theo ngôn ngữ")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

# Schema định dạng dữ liệu trả về cho Frontend
class CVResponse(CVBase):
    Id: int 
    RawText: Optional[str] = None
    CleanText: Optional[str] = None
    Summary: Optional[str] = None
    CreatedAt: datetime
    skills: List[CVSkillResponse] = []
    experiences: List[ExperienceResponse] = []
    educations: List[EducationResponse] = []

    model_config = ConfigDict(from_attributes=True)