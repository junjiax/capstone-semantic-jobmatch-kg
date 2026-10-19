from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.jd import JD
    from app.models.profile import Profile


class Result(Base):
    __tablename__ = "RESULT"

    UserId: Mapped[int] = mapped_column(Integer, nullable=False)
    ProfileId: Mapped[int] = mapped_column(ForeignKey("PROFILE.id"), nullable=False)
    JobId: Mapped[int] = mapped_column(ForeignKey("JD.id"), nullable=False)
    EmbeddingModel: Mapped[str | None] = mapped_column(String(200), nullable=True)
    Domain: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    Expertise: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    Skill: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    Experience: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    Qualification: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    TotalResult: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    CreatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    profile: Mapped["Profile"] = relationship(back_populates="results")
    jd: Mapped["JD"] = relationship(back_populates="results")
