from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum as SQLEnum
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.job import Job


class JobEmbedding(Base):
    __tablename__ = "JobEmbeddings"

    JobId: Mapped[int] = mapped_column(ForeignKey("Jobs.Id"))
    ModelName: Mapped[str] = mapped_column(String(100))
    Vector: Mapped[list] = mapped_column(Vector(384))
    CreatedAt: Mapped[datetime] = mapped_column(server_default=func.now())
    UpdatedAt: Mapped[Optional[datetime]] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    job: Mapped["Job"] = relationship(back_populates="embeddings")
