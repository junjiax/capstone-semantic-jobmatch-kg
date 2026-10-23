from typing import Any, List, Optional, Type

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.jd import JD
from app.models.jd_skill import JDSkill
from app.models.profile_skill import ProfileSkill


def _base_vector_search(
    db: Session,
    model: Type[Any],
    vector_column: Any,
    query_vector: List[float],
    top_k: int = 5,
    min_similarity: float = 0.0,
    label_text: Optional[str] = None,
) -> List[Any]:
    """Tìm các bản ghi gần query vector bằng cosine similarity."""
    if top_k < 1:
        raise ValueError("top_k must be greater than 0")

    # pgvector trả về cosine distance, distance càng nhỏ thì vector càng gần.
    distance = vector_column.cosine_distance(query_vector).label("distance")
    statement = (
        select(model, distance)
        .where(vector_column.is_not(None))
        .order_by(distance.asc())
        # Lấy dư kết quả để sau khi lọc min_similarity vẫn đủ top_k bản ghi.
        .limit(top_k * 2)
    )
    rows = db.execute(statement).all()

    results = []
    for entity, raw_distance in rows:
        # Với cosine distance, similarity = 1 - distance.
        similarity = 1.0 - float(raw_distance)
        if similarity < min_similarity:
            continue

        rounded_similarity = round(similarity, 4)
        if label_text:
            # Requirement dùng tuple riêng để API biết kết quả thuộc trường nào của JD.
            results.append((entity, label_text, rounded_similarity))
        else:
            results.append((entity, rounded_similarity))

        # Dừng sớm khi đã đủ số lượng kết quả hợp lệ.
        if len(results) >= top_k:
            break

    return results


def search_profile_skills_vector(
    db: Session,
    query_vector: List[float],
    top_k: int = 5,
    min_similarity: float = 0.0,
) -> List[Any]:
    return _base_vector_search(
        db,
        ProfileSkill,
        ProfileSkill.Vector,
        query_vector,
        top_k,
        min_similarity,
    )


def search_jd_skills_vector(
    db: Session,
    query_vector: List[float],
    top_k: int = 5,
    min_similarity: float = 0.0,
) -> List[Any]:
    return _base_vector_search(
        db,
        JDSkill,
        JDSkill.Vector,
        query_vector,
        top_k,
        min_similarity,
    )


def search_job_requirements_vector(
    db: Session,
    query_vector: List[float],
    top_k: int = 5,
    min_similarity: float = 0.0,
) -> List[Any]:
    return _base_vector_search(
        db,
        JD,
        JD.VectorResponsibility,
        query_vector,
        top_k,
        min_similarity,
        label_text="Responsibility",
    )
