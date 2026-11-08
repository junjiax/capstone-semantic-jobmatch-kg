from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class SkillBase(BaseModel):
    Name: str = Field(..., max_length=200)
    Description: Optional[str] = Field(None, max_length=500)
    Category: Optional[str] = Field(None, max_length=100)

class SkillCreate(SkillBase):
    pass

class SkillUpdate(BaseModel):
    Name: Optional[str] = None
    Description: Optional[str] = None
    Category: Optional[str] = None

class SkillResponse(SkillBase):
    Id: int
    
    model_config = ConfigDict(from_attributes=True)

# --- Bảng Kỹ năng của CV (Association Data) ---
class CVSkillBase(BaseModel):
    CVId: int
    SkillId: int

class CVSkillCreate(CVSkillBase):
    Confidence: Optional[Decimal] = None
    Source: Optional[str] = None

class CVSkillUpdate(BaseModel):
    Confidence: Optional[Decimal] = None
    Source: Optional[str] = None

class CVSkillResponse(CVSkillBase):
    Id: int
    
    # Lồng thêm thông tin chi tiết từ bảng Skill Master
    skill_master: Optional[SkillResponse] = None 
    model_config = ConfigDict(from_attributes=True)