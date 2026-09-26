from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from decimal import Decimal

from app.api.v1.schemas.cv import CVResponse
from app.api.v1.schemas.job import JobResponse

# Schema cơ sở chứa các loại điểm số so khớp
class MatchResultBase(BaseModel):
    CVId: int
    JobId: int
    SemanticScore: Optional[Decimal] = Field(None, max_digits=5, decimal_places=4)
    SkillScore: Optional[Decimal] = Field(None, max_digits=5, decimal_places=4)
    ExperienceScore: Optional[Decimal] = Field(None, max_digits=5, decimal_places=4)
    EducationScore: Optional[Decimal] = Field(None, max_digits=5, decimal_places=4)
    TotalScore: Optional[Decimal] = Field(None, max_digits=5, decimal_places=4)
    Rank: Optional[int] = None

# Schema dùng để lưu kết quả sau khi thuật toán chạy xong
class MatchResultCreate(MatchResultBase):
    pass

# Schema dùng để cập nhật lại điểm số hoặc thứ hạng
class MatchResultUpdate(BaseModel):
    SemanticScore: Optional[Decimal] = None
    SkillScore: Optional[Decimal] = None
    ExperienceScore: Optional[Decimal] = None
    EducationScore: Optional[Decimal] = None
    TotalScore: Optional[Decimal] = None
    Rank: Optional[int] = None

# Schema trả về cho Frontend để hiển thị danh sách ứng viên tiềm năng
class MatchResultResponse(MatchResultBase):
    Id: int 
    EvaluatedAt: datetime
    # cv: CVResponse
    # job: JobResponse

    model_config = ConfigDict(from_attributes=True)