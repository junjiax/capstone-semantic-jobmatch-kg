from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.jd import JD


class JDSkill(Base):
    __tablename__ = "JD_SKILL"

    JDId: Mapped[int] = mapped_column(ForeignKey("JD.id"), nullable=False)
    Title: Mapped[str] = mapped_column(String(200), nullable=False)
    Vector: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)

    jd: Mapped["JD"] = relationship(back_populates="skills")
