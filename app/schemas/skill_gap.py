from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class MatchStatus(str, Enum):
    MATCHED = "MATCHED"                      # Đáp ứng hoàn toàn
    PARTIALLY_MATCHED = "PARTIALLY_MATCHED"  # Đáp ứng một phần
    MISSING = "MISSING"                      # Còn thiếu (Skill Gap)


# ─── REQUEST SCHEMAS ──────────────────────────────────────────

class SkillGapAnalysisRequest(BaseModel):
    """
    Yêu cầu phân tích Skill Gap:
    Hỗ trợ 2 chế độ:
    1. Truyền profile_id và jd_id đã lưu trong cơ sở dữ liệu.
    2. HOẶC truyền trực tiếp danh sách kỹ năng tự do (để test nhanh / simulate).
    """
    profile_id: Optional[int] = Field(None, description="ID của hồ sơ ứng viên trong DB", example=1)
    jd_id: Optional[int] = Field(None, description="ID của tin tuyển dụng JD trong DB", example=1)
    
    # Dành cho chế độ phân tích ad-hoc (không bắt buộc có trong DB)
    candidate_skills: Optional[List[str]] = Field(
        None, 
        description="Danh sách kỹ năng ứng viên (dùng khi không có profile_id)",
        example=["Python", "FastAPI", "MySQL", "Git"]
    )
    required_skills: Optional[List[str]] = Field(
        None, 
        description="Danh sách kỹ năng yêu cầu của JD (dùng khi không có jd_id)",
        example=["Python", "PostgreSQL", "Docker", "AWS"]
    )
    
    # Tham số tùy chỉnh ngưỡng (tùy chọn)
    match_threshold: float = Field(0.82, ge=0.5, le=1.0, description="Ngưỡng coi là khớp hoàn toàn")
    partial_threshold: float = Field(0.60, ge=0.3, le=0.9, description="Ngưỡng coi là khớp một phần")


# ─── COMPONENT SCHEMAS ────────────────────────────────────────

class BaseSkillItem(BaseModel):
    skill_name: str = Field(..., description="Tên kỹ năng")
    category: Optional[str] = Field(None, description="Phân loại (Backend, Database, DevOps, v.v.)")
    importance: float = Field(1.0, description="Hệ số quan trọng đối với công việc (1.0 - 2.0)")


class MatchedSkillItem(BaseSkillItem):
    matched_with: str = Field(..., description="Kỹ năng tương ứng của ứng viên")
    similarity_score: float = Field(..., description="Điểm tương đồng ngữ nghĩa (0.0 -> 1.0)")
    is_exact_match: bool = Field(False, description="Khớp chính xác tên hay khớp ngữ nghĩa")


class PartialSkillItem(BaseSkillItem):
    closest_candidate_skill: str = Field(..., description="Kỹ năng gần nhất mà ứng viên sở hữu")
    similarity_score: float = Field(..., description="Độ tương đồng ngữ nghĩa")
    gap_reason: str = Field(..., description="Lý do đánh giá là đáp ứng một phần và gợi ý chuyển đổi")


class MissingSkillItem(BaseSkillItem):
    min_years: Optional[float] = Field(0.0, description="Số năm kinh nghiệm tối thiểu yêu cầu nếu có")
    urgency_level: str = Field("HIGH", description="Mức độ cấp thiết cần bổ sung (HIGH, MEDIUM, LOW)")
    learning_recommendation: Optional[str] = Field(None, description="Khuyến nghị khóa học / lộ trình tự học")


class ExtraSkillItem(BaseModel):
    skill_name: str = Field(..., description="Kỹ năng ứng viên có nhưng JD không bắt buộc")
    potential_value: str = Field("Lợi thế cạnh tranh bổ sung", description="Giá trị đóng góp")


class SkillGapSummary(BaseModel):
    total_required_skills: int = Field(..., description="Tổng số kỹ năng JD yêu cầu")
    total_matched_skills: int = Field(..., description="Số kỹ năng đáp ứng hoàn toàn")
    total_partial_skills: int = Field(..., description="Số kỹ năng đáp ứng một phần")
    total_missing_skills: int = Field(..., description="Số kỹ năng còn thiếu (khoảng trống)")
    total_extra_skills: int = Field(..., description="Số kỹ năng bổ trợ riêng của ứng viên")
    
    # Chỉ số phần trăm bao phủ kỹ năng
    skill_coverage_ratio: float = Field(..., description="Tỷ lệ đáp ứng kỹ năng có trọng số (0.0 -> 1.0)")
    skill_coverage_percentage: float = Field(..., description="Phần trăm đáp ứng (0% -> 100%)")
    fit_level: str = Field(..., description="Đánh giá tổng quan (EXCELLENT, GOOD, MODERATE, LOW)")


# ─── RESPONSE SCHEMA ──────────────────────────────────────────

class SkillGapResponse(BaseModel):
    profile_id: Optional[int] = None
    jd_id: Optional[int] = None
    summary: SkillGapSummary
    matched_skills: List[MatchedSkillItem] = Field(default_factory=list)
    partially_matched_skills: List[PartialSkillItem] = Field(default_factory=list)
    missing_skills: List[MissingSkillItem] = Field(default_factory=list)
    extra_skills: List[ExtraSkillItem] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list, description="Lời khuyên phát triển nghề nghiệp cụ thể")

    model_config = ConfigDict(from_attributes=True)