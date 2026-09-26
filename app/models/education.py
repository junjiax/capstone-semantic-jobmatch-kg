from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Numeric, String, ForeignKey, Integer
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enum import EducationLevel

if TYPE_CHECKING:
    from app.models.cv import CV
    
class Education(Base):
    __tablename__ = "Educations"

    CVId: Mapped[int] = mapped_column(ForeignKey("CVs.Id"))
    Degree: Mapped[Optional[str]] = mapped_column(String(200))
    Major: Mapped[Optional[str]] = mapped_column(String(200))
    School: Mapped[Optional[str]] = mapped_column(String(200))
    Level: Mapped[Optional[EducationLevel]] = mapped_column(
        SQLEnum(EducationLevel),
        nullable=True, 
        default=EducationLevel.BACHELOR)
    GraduationYear: Mapped[Optional[int]] = mapped_column(Integer)
    GPA: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))

    cv: Mapped["CV"] = relationship(back_populates="educations")