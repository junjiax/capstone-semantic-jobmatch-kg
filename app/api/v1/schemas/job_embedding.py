from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List, Optional

# Schema cơ sở chứa các thông tin đặc thù của Embedding
class JobEmbeddingBase(BaseModel):
    JobId: int
    ModelName: str = Field(..., max_length=100)
    # Vector định dạng List[float] với độ dài bắt buộc là 384
    Vector: List[float] = Field(..., min_length=384, max_length=384)

# Schema dùng để tạo mới bản ghi Embedding cho Job
class JobEmbeddingCreate(JobEmbeddingBase):
    pass

# Schema dùng để cập nhật thông tin Embedding
class JobEmbeddingUpdate(BaseModel):
    ModelName: Optional[str] = None
    Vector: Optional[List[float]] = None

# Schema định dạng dữ liệu trả về cho API
class JobEmbeddingResponse(JobEmbeddingBase):
    Id: int 
    CreatedAt: datetime
    UpdatedAt: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)