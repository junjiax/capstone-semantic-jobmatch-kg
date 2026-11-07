from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.v1.schemas.response import ResponseSchema
from app.services.skill_features.skill_matching import calculate_cv_jd_matching

router = APIRouter(tags=["Job"])


class TransferableSkillItem(BaseModel):
    required_skill: str = Field(..., description="Kỹ năng JD yêu cầu")
    candidate_skill: str = Field(..., description="Kỹ năng tương đương ứng viên có")
    cluster_name: str = Field(..., description="Nhóm chuyên môn chung trên Knowledge Graph")
    note: str = Field(..., description="Mô tả mức độ chuyển đổi")


class MatchEvaluationResponse(BaseModel):
    profile_id: int = Field(..., description="ID của hồ sơ ứng viên")
    jd_id: int = Field(..., description="ID của tin tuyển dụng")
    is_suitable: bool = Field(..., description="Có phù hợp để nộp đơn (apply) hay không")
    fit_level: str = Field(..., description="Cấp độ phù hợp (HIGHLY_SUITABLE, MODERATE_SUITABLE, LOW_SUITABLE)")
    match_score: float = Field(..., description="Điểm đánh giá phù hợp tổng hợp (0.0 đến 1.0)")
    verdict: str = Field(..., description="Kết luận đánh giá chi tiết mức độ phù hợp")
    matched_skills: List[str] = Field(default_factory=list, description="Kỹ năng CV đã có (khớp chính xác với JD)")
    transferable_skills: List[TransferableSkillItem] = Field(
        default_factory=list,
        description="Kỹ năng tương đương trên Knowledge Graph (dễ dàng chuyển đổi)",
    )
    missing_skills: List[str] = Field(default_factory=list, description="Kỹ năng CV còn thiếu so với JD")
    bonus_skills: List[str] = Field(default_factory=list, description="Kỹ năng thế mạnh cộng thêm của ứng viên")
    semantic_similarity: float = Field(..., description="Điểm tương đồng ngữ nghĩa câu từ (Cosine Similarity)")
    graph_synced: bool = Field(default=False, description="Trạng thái đồng bộ và lưu kết quả lên Neo4j Knowledge Graph")


@router.get("/")
def health_check():
    return {"status": "activate", "message": "API is running successfully."}


@router.get(
    "/match-similarity",
    response_model=ResponseSchema[MatchEvaluationResponse],
    status_code=status.HTTP_200_OK,
    summary="Đánh giá CV có phù hợp để apply Job hay không (Smart & Knowledge Graph Match)",
    description="Kiểm tra mức độ phù hợp toàn diện giữa CV của ứng viên (profile_id) và Job Description (jd_id). "
                "Tự động đồng bộ thực thể lên Neo4j và lưu quan hệ MATCHES_JD trực tiếp trên Đồ thị tri thức.",
)
def match_cv_jd_similarity(
    profile_id: int = Query(..., description="ID của hồ sơ ứng viên (Profile ID)", ge=1),
    jd_id: int = Query(..., description="ID của tin tuyển dụng (JD ID)", ge=1),
    db: Session = Depends(get_db),
):
    try:
        evaluation = calculate_cv_jd_matching(db=db, profile_id=profile_id, jd_id=jd_id)
    except ValueError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(exc)
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(exc))

    return ResponseSchema[MatchEvaluationResponse](
        success=True,
        message="Đánh giá mức độ phù hợp CV - JD thành công (Đã đồng bộ Knowledge Graph)",
        data=MatchEvaluationResponse(**evaluation),
    )
