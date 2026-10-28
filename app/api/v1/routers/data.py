from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.api.v1.schemas.response import ResponseSchema
from app.api.v1.schemas.semantic_search import SkillSearchRequest, SkillSearchResponse
# from app.services.jd import service

router = APIRouter()


@router.get(
    "/data-crawling",
    response_model=ResponseSchema[SkillSearchResponse],
    status_code=status.HTTP_200_OK,
    summary="JD Data Crawling",
    description="Thu thập dữ liệu JD từ các nền tảng tìm việc làm.",
)
def data_crawling_endpoint(
    request: SkillSearchRequest,
    db: Session = Depends(get_db),
):
    pass
    # data = service.search_skills_semantic(db, request)
    # return ResponseSchema[SkillSearchResponse](
    #     success=True,
    #     message="Truy xuất kỹ năng tương đồng ngữ nghĩa thành công",
    #     data=data,
    # )
