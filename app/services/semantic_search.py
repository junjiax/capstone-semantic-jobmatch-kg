from typing import List
from sqlalchemy.orm import Session
from app.clients.sentence_transformer import get_sentence_transformer
from app.services.text_embedding import normalize_text
from app.crud import semantic_search as crud
from app.api.v1.schemas.semantic_search import ( SkillSearchRequest, SkillSearchResponse, SkillSearchResultItem, JobRequirementSearchRequest, JobRequirementSearchResponse, JobRequirementSearchResultItem,
)


def search_skills_semantic(db: Session, request: SkillSearchRequest) -> SkillSearchResponse:
    """Xử lý tìm kiếm kỹ năng tương đồng ngữ nghĩa."""
    cleaned_query = normalize_text(request.query)
    client = get_sentence_transformer()
  
    # Mã hóa chuỗi truy vấn thành vector 384 chiều
    query_vector = client.encode(cleaned_query, normalize=True)

    items: List[SkillSearchResultItem] = []

    # Lấy từ PROFILE_SKILL nếu được yêu cầu
    if request.source in ("all", "profile_skill"):
        profile_skills = crud.search_profile_skills_vector(
            db, query_vector, top_k=request.top_k, min_similarity=request.min_similarity
        )
        for skill, sim in profile_skills:
            items.append(
                SkillSearchResultItem(
                    id=skill.id,
                    title=skill.SkillTitle,
                    similarity=sim,
                    source="PROFILE_SKILL",
                    entity_id=skill.ProfileId,
                )
            )

    # Lấy từ JD_SKILL nếu được yêu cầu
    if request.source in ("all", "jd_skill"):
        jd_skills = crud.search_jd_skills_vector(
            db, query_vector, top_k=request.top_k, min_similarity=request.min_similarity
        )
        for skill, sim in jd_skills:
            items.append(
                SkillSearchResultItem(
                    id=skill.id,
                    title=skill.Title,
                    similarity=sim,
                    source="JD_SKILL",
                    entity_id=skill.JDId,
                )
            )

    # Sắp xếp toàn bộ kết quả theo độ tương đồng giảm dần
    items.sort(key=lambda x: x.similarity, reverse=True)
    top_items = items[: request.top_k]

    return SkillSearchResponse(
        query=cleaned_query,
        model_name=client.model_name,
        total_results=len(top_items),
        results=top_items,
    )


def search_job_requirements_semantic(
    db: Session, request: JobRequirementSearchRequest
    ) -> JobRequirementSearchResponse:
    
    """Xử lý tìm kiếm tin tuyển dụng tương đồng ngữ nghĩa."""
    cleaned_query = normalize_text(request.query)
    client = get_sentence_transformer()
  
    query_vector = client.encode(cleaned_query, normalize=True)
    job_matches = crud.search_job_requirements_vector(
        db, query_vector, top_k=request.top_k, min_similarity=request.min_similarity
    )

    items = [
        JobRequirementSearchResultItem(
            jd_id=jd.id,
            title=jd.Title,
            domain=jd.Domain,
            expertise=jd.Expertise,
            matched_field=matched_field,
            similarity=sim,
        )
        for jd, matched_field, sim in job_matches
    ]

    return JobRequirementSearchResponse(
        query=cleaned_query,
        model_name=client.model_name,
        total_results=len(items),
        results=items,
    )