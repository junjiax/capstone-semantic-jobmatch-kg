import logging
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.response import ResponseSchema
from app.schemas.skill_gap import (
    SkillGapAnalysisRequest,
    SkillGapResponse,
)
from app.services.skill_features.skill_gap_analysis import analyze_skill_gap_service
from app.repositories.postgres import profile as profile_repo
from app.repositories.postgres import jd as jd_repo

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    summary="Kiểm tra trạng thái Service Skill Gap",
    tags=["Skill Gap Analysis"]
)
def health_check():
    """Kiểm tra router Skill Gap đã hoạt động hay chưa."""
    return {"status": "active", "module": "Skill Gap Analysis Service"}


@router.post(
    "/analyze",
    response_model=ResponseSchema[SkillGapResponse],
    status_code=status.HTTP_200_OK,
    summary="Phân tích Skill Gap giữa Ứng viên và Công việc",
    description="""
    Thực hiện phân tích đối sánh kỹ năng chi tiết:
    - **MATCHED**: Kỹ năng đáp ứng đầy đủ (Exact match hoặc tương đồng ngữ nghĩa >= 0.82)
    - **PARTIALLY_MATCHED**: Kỹ năng đáp ứng một phần (0.60 <= tương đồng < 0.82)
    - **MISSING**: Kỹ năng còn thiếu trong CV ứng viên (< 0.60)
    - **EXTRA**: Kỹ năng bổ trợ riêng của ứng viên
    
    Hỗ trợ truyền `profile_id` & `jd_id`, hoặc truyền trực tiếp mảng `candidate_skills` & `required_skills`.
    """,
    tags=["Skill Gap Analysis"]
)
def analyze_skill_gap_endpoint(
    request: SkillGapAnalysisRequest,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # Bật khi cần xác thực người dùng
):
    # Kiểm tra tính hợp lệ của đầu vào
    if request.profile_id is None and not request.candidate_skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng cung cấp 'profile_id' hoặc danh sách 'candidate_skills'."
        )
    if request.jd_id is None and not request.required_skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vui lòng cung cấp 'jd_id' hoặc danh sách 'required_skills'."
        )

    # Nếu truyền profile_id, xác thực tồn tại trong DB
    if request.profile_id is not None:
        p = profile_repo.get_profile_by_id(db, request.profile_id)
        if not p:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy Profile với ID = {request.profile_id}"
            )

    # Nếu truyền jd_id, xác thực tồn tại trong DB
    if request.jd_id is not None:
        j = jd_repo.get_jd_by_id(db, request.jd_id)
        if not j:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy JD tuyển dụng với ID = {request.jd_id}"
            )

    try:
        result = analyze_skill_gap_service(db=db, request=request)
        return ResponseSchema[SkillGapResponse](
            success=True,
            message="Phân tích khoảng trống kỹ năng (Skill Gap) thành công",
            data=result,
        )
    except Exception as e:
        logger.exception(f"Lỗi khi thực hiện Skill Gap Analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi xử lý nội bộ trong quá trình phân tích Skill Gap: {str(e)}"
        )


@router.get(
    "/profile/{profile_id}/jd/{jd_id}",
    response_model=ResponseSchema[SkillGapResponse],
    status_code=status.HTTP_200_OK,
    summary="Phân tích nhanh Skill Gap qua Profile ID và JD ID",
    tags=["Skill Gap Analysis"]
)
def analyze_skill_gap_by_ids(
    profile_id: int = Path(..., description="ID của hồ sơ ứng viên", example=1),
    jd_id: int = Path(..., description="ID của tin tuyển dụng", example=1),
    db: Session = Depends(get_db),
):
    """
    Tiện ích phân tích nhanh giữa một Profile và JD cụ thể qua URL Path.
    """
    req = SkillGapAnalysisRequest(profile_id=profile_id, jd_id=jd_id)
    return analyze_skill_gap_endpoint(request=req, db=db)