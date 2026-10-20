import logging
from typing import List, Dict, Any, Optional
from app.clients.neo4j_client import get_neo4j_client

logger = logging.getLogger(__name__)


def normalize_skill_name(name: str) -> str:
    """Chuẩn hóa tên kỹ năng để chống trùng lặp do viết hoa/thường hoặc khoảng trắng thừa."""
    if not name:
        return ""
    return name.strip().lower()


def upsert_user_node(user_id: int, email: str, full_name: str, role: str) -> Dict[str, Any]:
    query = """
    MERGE (u:User {userId: $userId})
    SET u.email = $email,
        u.fullName = $fullName,
        u.role = $role,
        u.updatedAt = datetime()
    RETURN u.userId AS userId
    """
    client = get_neo4j_client()
    res = client.execute_write(query, {
        "userId": user_id,
        "email": email,
        "fullName": full_name or "",
        "role": str(role).lower() if role else "applicant"
    })
    return res[0] if res else {}


def upsert_skill_node(skill_id: int, name: str, category: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
    normalized = normalize_skill_name(name)
    query = """
    MERGE (s:Skill {normalizedName: $normalizedName})
    ON CREATE SET
        s.skillId = $skillId,
        s.name = $name,
        s.category = $category,
        s.description = $description,
        s.createdAt = datetime()
    ON MATCH SET
        s.skillId = coalesce(s.skillId, $skillId),
        s.name = $name,
        s.category = coalesce($category, s.category),
        s.description = coalesce($description, s.description),
        s.updatedAt = datetime()
    RETURN s.skillId AS skillId, s.name AS name, s.normalizedName AS normalizedName
    """
    client = get_neo4j_client()
    res = client.execute_write(query, {
        "skillId": skill_id,
        "name": name.strip(),
        "normalizedName": normalized,
        "category": category or "",
        "description": description or ""
    })
    return res[0] if res else {}


def upsert_job_position_node(
    job_id: int,
    title: str,
    min_experience: Optional[float] = None,
    education_level: Optional[str] = None,
    status: Optional[str] = None,
    embedding: Optional[List[float]] = None
) -> Dict[str, Any]:
    query = """
    MERGE (j:JobPosition {jobId: $jobId})
    SET j.title = $title,
        j.minExperience = $minExperience,
        j.educationLevel = $educationLevel,
        j.status = $status,
        j.updatedAt = datetime()
    WITH j
    CALL apoc.do.when(
        $hasEmbedding,
        'SET j.embedding = $embedding RETURN j',
        'RETURN j',
        {j: j, embedding: $embedding}
    ) YIELD value
    RETURN value.j.jobId AS jobId
    """
    # Neo4j fallback without APOC if apoc not loaded
    fallback_query = """
    MERGE (j:JobPosition {jobId: $jobId})
    SET j.title = $title,
        j.minExperience = $minExperience,
        j.educationLevel = $educationLevel,
        j.status = $status,
        j.updatedAt = datetime()
    WITH j
    FOREACH (_ IN CASE WHEN $embedding IS NOT NULL THEN [1] ELSE [] END |
        SET j.embedding = $embedding
    )
    RETURN j.jobId AS jobId
    """
    client = get_neo4j_client()
    res = client.execute_write(fallback_query, {
        "jobId": job_id,
        "title": title.strip(),
        "minExperience": float(min_experience) if min_experience is not None else 0.0,
        "educationLevel": str(education_level) if education_level else "BACHELOR",
        "status": str(status) if status else "OPEN",
        "embedding": embedding
    })
    return res[0] if res else {}


def upsert_cv_node(
    cv_id: int,
    user_id: int,
    language: Optional[str] = "en",
    summary: Optional[str] = None,
    embedding: Optional[List[float]] = None
) -> Dict[str, Any]:
    query = """
    MERGE (u:User {userId: $userId})
    MERGE (c:CV {cvId: $cvId})
    ON CREATE SET
        c.userId = $userId,
        c.language = $language,
        c.summary = $summary,
        c.createdAt = datetime()
    ON MATCH SET
        c.language = $language,
        c.summary = $summary,
        c.updatedAt = datetime()
    MERGE (u)-[:OWNS_CV]->(c)
    WITH c
    FOREACH (_ IN CASE WHEN $embedding IS NOT NULL THEN [1] ELSE [] END |
        SET c.embedding = $embedding
    )
    RETURN c.cvId AS cvId
    """
    client = get_neo4j_client()
    res = client.execute_write(query, {
        "cvId": cv_id,
        "userId": user_id,
        "language": language or "en",
        "summary": summary or "",
        "embedding": embedding
    })
    return res[0] if res else {}


def sync_cv_skills_graph(cv_id: int, skills: List[Dict[str, Any]]) -> int:
    """
    Đồng bộ danh sách kỹ năng của CV lên Neo4j theo lô (UNWIND).
    Xóa bỏ các quan hệ HAS_SKILL cũ không còn trong đợt parse mới để bảo đảm tính nhất quán (Idempotent).
    """
    clean_skills = []
    for item in skills:
        s_name = item.get("skillName") or item.get("name")
        if not s_name:
            continue
        clean_skills.append({
            "skillId": item.get("skillId"),
            "skillName": s_name.strip(),
            "normalizedName": normalize_skill_name(s_name),
            "confidence": float(item.get("confidence", 1.0) or 1.0),
            "source": str(item.get("source", "parsed"))
        })

    query = """
    MATCH (c:CV {cvId: $cvId})
    // Xóa quan hệ HAS_SKILL cũ trước khi ghi lại danh sách mới
    OPTIONAL MATCH (c)-[old_r:HAS_SKILL]->()
    DELETE old_r
    WITH c
    UNWIND $skills AS item
    MERGE (s:Skill {normalizedName: item.normalizedName})
    ON CREATE SET 
        s.skillId = item.skillId,
        s.name = item.skillName,
        s.createdAt = datetime()
    MERGE (c)-[r:HAS_SKILL]->(s)
    SET r.confidence = item.confidence,
        r.source = item.source,
        r.updatedAt = datetime()
    RETURN count(r) AS syncedCount
    """
    client = get_neo4j_client()
    res = client.execute_write(query, {
        "cvId": cv_id,
        "skills": clean_skills
    })
    return res[0]["syncedCount"] if res else 0


def sync_job_skills_graph(job_id: int, skills: List[Dict[str, Any]]) -> int:
    """
    Đồng bộ danh sách kỹ năng yêu cầu của JobPosition lên Neo4j theo lô (UNWIND).
    """
    clean_skills = []
    for item in skills:
        s_name = item.get("skillName") or item.get("name")
        if not s_name:
            continue
        clean_skills.append({
            "skillId": item.get("skillId"),
            "skillName": s_name.strip(),
            "normalizedName": normalize_skill_name(s_name),
            "importance": float(item.get("importance", 1.0) or 1.0),
            "minYears": float(item.get("minYears", 0.0) or 0.0)
        })

    query = """
    MATCH (j:JobPosition {jobId: $jobId})
    OPTIONAL MATCH (j)-[old_r:REQUIRES_SKILL]->()
    DELETE old_r
    WITH j
    UNWIND $skills AS req
    MERGE (s:Skill {normalizedName: req.normalizedName})
    ON CREATE SET 
        s.skillId = req.skillId,
        s.name = req.skillName,
        s.createdAt = datetime()
    MERGE (j)-[r:REQUIRES_SKILL]->(s)
    SET r.importance = req.importance,
        r.minYears = req.minYears,
        r.updatedAt = datetime()
    RETURN count(r) AS syncedCount
    """
    client = get_neo4j_client()
    res = client.execute_write(query, {
        "jobId": job_id,
        "skills": clean_skills
    })
    return res[0]["syncedCount"] if res else 0
