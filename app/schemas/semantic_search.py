from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class SkillSearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Nội dung cần tìm kiếm kỹ năng tương đồng"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Số lượng kỹ năng tối đa cần trả về"
    )
    min_similarity: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Điểm tương đồng Cosine tối thiểu để lọc kết quả"
    )
    source: Literal["all", "profile_skill", "jd_skill"] = Field(
        default="all",
        description="Nguồn kỹ năng cần tìm: 'all', 'profile_skill' (CV), hoặc 'jd_skill' (JD tuyển dụng)"
    )


class SkillSearchResultItem(BaseModel):
    id: int = Field(..., description="Mã định danh kỹ năng")
    title: str = Field(..., description="Tên kỹ năng")
    similarity: float = Field(..., description="Điểm tương đồng ngữ nghĩa (0.0 đến 1.0)")
    source: str = Field(..., description="Nguồn kỹ năng: PROFILE_SKILL hoặc JD_SKILL")
    entity_id: Optional[int] = Field(None, description="Mã ProfileId hoặc JDId tương ứng")


class SkillSearchResponse(BaseModel):
    query: str = Field(..., description="Câu truy vấn gốc của người dùng")
    model_name: str = Field(..., description="Mô hình embedding sử dụng")
    total_results: int = Field(..., description="Số kết quả tìm thấy")
    results: List[SkillSearchResultItem] = Field(default_factory=list, description="Danh sách kỹ năng tương đồng")


class JobRequirementSearchRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Mô tả kỹ năng, trách nhiệm hoặc yêu cầu cần tìm vị trí việc làm phù hợp"
    )
    top_k: int = Field(default=5, ge=1, le=50, description="Số lượng JD tối đa cần trả về")
    min_similarity: float = Field(default=0.0, ge=-1.0, le=1.0, description="Ngưỡng tương đồng tối thiểu")


class JobRequirementSearchResultItem(BaseModel):
    jd_id: int = Field(..., description="Mã JD")
    title: str = Field(..., description="Chức danh công việc")
    domain: Optional[str] = Field(None, description="Lĩnh vực chuyên môn")
    expertise: Optional[str] = Field(None, description="Chuyên môn sâu")
    matched_field: str = Field(..., description="Trường vector có độ khớp cao nhất")
    similarity: float = Field(..., description="Điểm tương đồng ngữ nghĩa")


class JobRequirementSearchResponse(BaseModel):
    query: str = Field(..., description="Câu truy vấn gốc")
    model_name: str = Field(..., description="Mô hình embedding sử dụng")
    total_results: int = Field(..., description="Số lượng vị trí việc làm tìm thấy")
    results: List[JobRequirementSearchResultItem] = Field(default_factory=list)