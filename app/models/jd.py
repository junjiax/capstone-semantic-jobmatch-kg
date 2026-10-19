from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.jd_skill import JDSkill
    from app.models.result import Result


class JD(Base):
    __tablename__ = "JD"

    RawText: Mapped[str | None] = mapped_column(Text, nullable=True)
    CleanText: Mapped[str | None] = mapped_column(Text, nullable=True)
    Title: Mapped[str] = mapped_column(String(200), nullable=False)
    Domain: Mapped[str | None] = mapped_column(String(200), nullable=True)
    Expertise: Mapped[str | None] = mapped_column(String(200), nullable=True)
    Qualification: Mapped[str | None] = mapped_column(String(200), nullable=True)
    Responsibility: Mapped[str | None] = mapped_column(Text, nullable=True)
    Experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    VectorTitle: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    VectorDomain: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    VectorExpertise: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    VectorQualification: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    VectorResponsibility: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    skills: Mapped[list["JDSkill"]] = relationship(
        back_populates="jd", cascade="all, delete-orphan"
    )
    results: Mapped[list["Result"]] = relationship(back_populates="jd")
