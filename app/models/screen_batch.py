from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, func
from sqlalchemy.types import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.enum import BatchStatus

if TYPE_CHECKING:
    from app.models.User import User
    from app.models.job import Job

class ScreeningBatch(Base):
    __tablename__ = "ScreeningBatches"

    JobId: Mapped[int] = mapped_column(ForeignKey("Jobs.Id"))
    TriggeredBy: Mapped[int] = mapped_column(ForeignKey("users.Id"))
    TotalCV: Mapped[int] = mapped_column(Integer, server_default="0")
    ProcessedCV: Mapped[int] = mapped_column(Integer, server_default="0")
    Status: Mapped[BatchStatus] = mapped_column(
        SQLEnum(BatchStatus), 
        default=BatchStatus.PENDING
    )
    CreatedAt: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="batches")
    job: Mapped["Job"] = relationship(back_populates="batches")