from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.api.v1.schemas.response import ResponseSchema
from app.api.v1.schemas.semantic_search import ( SkillSearchRequest, SkillSearchResponse, JobRequirementSearchRequest, JobRequirementSearchResponse,
)
from app.services import semantic_search as service

router = APIRouter()


@router.post(
    "/skills",
    response_model=ResponseSchema[SkillSearchResponse],
    status_code=status.HTTP_200_OK,
    summary="Semantic Search Skills",
    description="Tìm kiếm các kỹ năng có ý nghĩa ngữ nghĩa gần với chuỗi văn bản.",
)
def search_skills_endpoint(
    request: SkillSearchRequest,
    db: Session = Depends(get_db),
):
    data = service.search_skills_semantic(db, request)
    return ResponseSchema[SkillSearchResponse](
        success=True,
        message="Truy xuất kỹ năng tương đồng ngữ nghĩa thành công",
        data=data,
    )


@router.post(
    "/job-requirements",
    response_model=ResponseSchema[JobRequirementSearchResponse],
    status_code=status.HTTP_200_OK,
    summary="Semantic Search Job Requirements",
    description="Tìm kiếm các vị trí công việc có nội dung yêu cầu tuyển dụng gần nghĩa nhất với đầu vào.",
)
def search_job_requirements_endpoint(
    request: JobRequirementSearchRequest,
    db: Session = Depends(get_db),
):
    data = service.search_job_requirements_semantic(db, request)
    return ResponseSchema[JobRequirementSearchResponse](
        success=True,
        message="Truy xuất vị trí công việc tương đồng ngữ nghĩa thành công",
        data=data,
    )