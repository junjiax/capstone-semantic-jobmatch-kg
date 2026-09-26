from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Date, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.cv import CV

class Experience(Base):
    __tablename__ = "Experiences"

    CVId: Mapped[int] = mapped_column(ForeignKey("CVs.Id"))
    Company: Mapped[str] = mapped_column(String(200))
    Position: Mapped[Optional[str]] = mapped_column(String(200))
    StartDate: Mapped[Optional[date]] = mapped_column(Date)
    EndDate: Mapped[Optional[date]] = mapped_column(Date)
    DurationMonths: Mapped[Optional[int]] = mapped_column(Integer)

    cv: Mapped["CV"] = relationship(back_populates="experiences")