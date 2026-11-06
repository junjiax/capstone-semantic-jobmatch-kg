from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from typing import Optional

class ExperienceBase(BaseModel):
    CVId: int
    Company: str = Field(..., max_length=200)
    Position: Optional[str] = Field(None, max_length=200)
    StartDate: Optional[date] = None
    EndDate: Optional[date] = None
    DurationMonths: Optional[int] = None

class ExperienceCreate(ExperienceBase):
    pass

class ExperienceUpdate(BaseModel):
    Company: Optional[str] = None
    Position: Optional[str] = None
    StartDate: Optional[date] = None
    EndDate: Optional[date] = None
    DurationMonths: Optional[int] = None

class ExperienceResponse(ExperienceBase):
    Id: int
    
    model_config = ConfigDict(from_attributes=True)