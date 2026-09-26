from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional
from app.api.v1.schemas.job import JobResponse
from app.models.enum import BatchStatus

# Schema cơ sở chứa thông tin về đợt sàng lọc
class ScreeningBatchBase(BaseModel):
    JobId: int
    TriggeredBy: int
    TotalCV: int = 0
    ProcessedCV: int = 0
    Status: BatchStatus = BatchStatus.PENDING

# Schema dùng để khởi tạo một đợt sàng lọc mới
class ScreeningBatchCreate(BaseModel):
    JobId: int
    TriggeredBy: int

# Schema dùng để cập nhật tiến độ xử lý CV
class ScreeningBatchUpdate(BaseModel):
    TotalCV: Optional[int] = None
    ProcessedCV: Optional[int] = None
    Status: Optional[BatchStatus] = None

# Schema trả về thông tin chi tiết của đợt sàng lọc
class ScreeningBatchResponse(ScreeningBatchBase):
    Id: int 
    CreatedAt: datetime
    # hr: HrResponse
    # job: JobResponse

    model_config = ConfigDict(from_attributes=True)