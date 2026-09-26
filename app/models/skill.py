from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.cv_skill import CVSkill
    from app.models.job_skill import JobSkill

class Skill(Base):
    __tablename__ = "Skills"

    Name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    Description: Mapped[Optional[str]] = mapped_column(String(500))
    Category: Mapped[Optional[str]] = mapped_column(String(100), index=True)

    cv_skills: Mapped[List["CVSkill"]] = relationship(back_populates="skill")
    job_skills: Mapped[List["JobSkill"]] = relationship(back_populates="skill")