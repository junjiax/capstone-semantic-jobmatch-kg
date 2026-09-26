from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base
from sqlalchemy import Enum as SQLEnum

if TYPE_CHECKING:
    from app.models.cv import CV


class CVEmbedding(Base):
    __tablename__ = "CVEmbeddings"

    CVId: Mapped[int] = mapped_column(ForeignKey("CVs.Id"))
    ModelName: Mapped[str] = mapped_column(String(100))
    Vector: Mapped[list] = mapped_column(Vector(384))
    CreatedAt: Mapped[datetime] = mapped_column(server_default=func.now())

    cv: Mapped["CV"] = relationship(back_populates="embeddings")
