from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List
from app.api.v1.schemas.cv import CVResponse

# Schema cơ sở cho Embedding
class CVEmbeddingBase(BaseModel):
    CVId: int
    ModelName: str = Field(..., max_length=100)
    # Vector 384 chiều thường thấy ở các model Sentence Transformers
    Vector: List[float] = Field(..., min_length=384, max_length=384)

# Schema dùng để tạo mới Embedding 
class CVEmbeddingCreate(CVEmbeddingBase):
    pass

# Schema trả về thông tin Embedding
class CVEmbeddingResponse(CVEmbeddingBase):
    Id: int
    CreatedAt: datetime
    cv: CVResponse

    model_config = ConfigDict(from_attributes=True)