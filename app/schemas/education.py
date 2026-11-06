from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from app.models.enum import EducationLevel

class EducationBase(BaseModel):
    CVId: int
    Degree: Optional[str] = Field(None, max_length=200)
    Major: Optional[str] = Field(None, max_length=200)
    School: Optional[str] = Field(None, max_length=200)
    Level: Optional[EducationLevel] = EducationLevel.BACHELOR
    GraduationYear: Optional[int] = None
    GPA: Optional[Decimal] = Field(None, max_digits=3, decimal_places=2)

class EducationCreate(EducationBase):
    pass

class EducationUpdate(BaseModel):
    Degree: Optional[str] = None
    Major: Optional[str] = None
    School: Optional[str] = None
    Level: Optional[EducationLevel] = None
    GraduationYear: Optional[int] = None
    GPA: Optional[Decimal] = None

class EducationResponse(EducationBase):
    Id: int
    model_config = ConfigDict(from_attributes=True)