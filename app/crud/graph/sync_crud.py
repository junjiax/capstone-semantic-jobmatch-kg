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


def upsert_skill_node(
    skill_id: int,
    name: str,
    category: Optional[str] = None,
    description: Optional[str] = None,
    expertise_name: Optional[str] = None,
) -> Dict[str, Any]:
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
    WITH s
    FOREACH (_ IN CASE WHEN $expertiseName IS NOT NULL AND $expertiseName <> '' THEN [1] ELSE [] END |
        MERGE (e:Expertise {name: $expertiseName})
        MERGE (s)-[:BELONGS_TO_EXPERTISE]->(e)
    )
    RETURN s.skillId AS skillId, s.name AS name, s.normalizedName AS normalizedName
    """
    client = get_neo4j_client()
    res = client.execute_write(query, {
        "skillId": skill_id,
        "name": name.strip(),
        "normalizedName": normalized,
        "category": category or "",
        "description": description or "",
        "expertiseName": expertise_name.strip() if expertise_name else None
    })
    return res[0] if res else {}


def link_skill_to_expertise(skill_name: str, expertise_name: str) -> bool:
    """Tạo quan hệ (s:Skill)-[:BELONGS_TO_EXPERTISE]->(e:Expertise) an toàn, idempotent."""
    if not skill_name or not expertise_name:
        return False
    query = """
    MERGE (s:Skill {normalizedName: $normalizedSkill})
    ON CREATE SET s.name = $skillName, s.createdAt = datetime()
    MERGE (e:Expertise {name: $expertiseName})
    ON CREATE SET e.normalizedName = toLower($expertiseName), e.createdAt = datetime()
    MERGE (s)-[:BELONGS_TO_EXPERTISE]->(e)
    RETURN count(*) AS cnt
    """
    client = get_neo4j_client()
    res = client.execute_write(query, {
        "skillName": skill_name.strip(),
        "normalizedSkill": normalize_skill_name(skill_name),
        "expertiseName": expertise_name.strip()
    })
    return bool(res and res[0].get("cnt", 0) > 0)


def link_expertise_to_domain(expertise_name: str, domain_name: str) -> bool:
    """Tạo quan hệ (e:Expertise)-[:UNDER_DOMAIN]->(d:Domain) an toàn, idempotent."""
    if not expertise_name or not domain_name:
        return False
    query = """
    MERGE (e:Expertise {name: $expertiseName})
    ON CREATE SET e.normalizedName = toLower($expertiseName), e.createdAt = datetime()
    MERGE (d:Domain {name: $domainName})
    ON CREATE SET d.normalizedName = toLower($domainName), d.createdAt = datetime()
    MERGE (e)-[:UNDER_DOMAIN]->(d)
    RETURN count(*) AS cnt
    """
    client = get_neo4j_client()
    res = client.execute_write(query, {
        "expertiseName": expertise_name.strip(),
        "domainName": domain_name.strip()
    })
    return bool(res and res[0].get("cnt", 0) > 0)



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


def upsert_domain_node(name: str, description: Optional[str] = None) -> Dict[str, Any]:
    """Tạo hoặc cập nhật node Domain (Lĩnh vực CNTT như Backend, Frontend, AI/ML, DevOps...)."""
    if not name or not name.strip():
        return {}
    normalized = name.strip().lower()
    query = """
    MERGE (d:Domain {name: $name})
    ON CREATE SET 
        d.normalizedName = $normalizedName,
        d.description = $description,
        d.createdAt = datetime()
    ON MATCH SET
        d.description = coalesce($description, d.description),
        d.updatedAt = datetime()
    RETURN d.name AS name
    """
    client = get_neo4j_client()
    res = client.execute_write(query, {
        "name": name.strip(),
        "normalizedName": normalized,
        "description": description or ""
    })
    return res[0] if res else {}


def upsert_expertise_node(name: str, domain_name: Optional[str] = None) -> Dict[str, Any]:
    """Tạo hoặc cập nhật node Expertise (Chuyên môn sâu)."""
    if not name or not name.strip():
        return {}
    normalized = name.strip().lower()
    query = """
    MERGE (e:Expertise {name: $name})
    ON CREATE SET 
        e.normalizedName = $normalizedName,
        e.createdAt = datetime()
    ON MATCH SET 
        e.updatedAt = datetime()
    WITH e
    FOREACH (_ IN CASE WHEN $domainName IS NOT NULL AND $domainName <> '' THEN [1] ELSE [] END |
        MERGE (d:Domain {name: $domainName})
        MERGE (e)-[:UNDER_DOMAIN]->(d)
    )
    RETURN e.name AS name
    """
    client = get_neo4j_client()
    res = client.execute_write(query, {
        "name": name.strip(),
        "normalizedName": normalized,
        "domainName": domain_name.strip() if domain_name else None
    })
    return res[0] if res else {}


def upsert_jd_node(
    jd_id: int,
    title: str,
    domain: Optional[str] = None,
    expertise: Optional[str] = None,
    qualification: Optional[str] = None,
    responsibility: Optional[str] = None,
    experience_years: Optional[int] = None,
    raw_text: Optional[str] = None,
    clean_text: Optional[str] = None,
    embedding: Optional[List[float]] = None,
    vector_title: Optional[List[float]] = None,
    vector_domain: Optional[List[float]] = None,
    vector_expertise: Optional[List[float]] = None,
    vector_qualification: Optional[List[float]] = None,
    vector_responsibility: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """
    Tạo hoặc cập nhật node JD (Job Description) và kết nối với Domain, Expertise, JobPosition.
    """
    query = """
    MERGE (j:JD {jdId: $jdId})
    ON CREATE SET
        j.title = $title,
        j.domain = $domain,
        j.expertise = $expertise,
        j.qualification = $qualification,
        j.responsibility = $responsibility,
        j.experienceYears = $experienceYears,
        j.rawText = $rawText,
        j.cleanText = $cleanText,
        j.createdAt = datetime()
    ON MATCH SET
        j.title = $title,
        j.domain = $domain,
        j.expertise = $expertise,
        j.qualification = $qualification,
        j.responsibility = $responsibility,
        j.experienceYears = $experienceYears,
        j.rawText = $rawText,
        j.cleanText = $cleanText,
        j.updatedAt = datetime()
    WITH j
    // Gán embedding vector nếu có
    FOREACH (_ IN CASE WHEN $embedding IS NOT NULL THEN [1] ELSE [] END |
        SET j.embedding = $embedding
    )
    FOREACH (_ IN CASE WHEN $vectorDomain IS NOT NULL THEN [1] ELSE [] END |
        SET j.vectorDomain = $vectorDomain
    )
    FOREACH (_ IN CASE WHEN $vectorExpertise IS NOT NULL THEN [1] ELSE [] END |
        SET j.vectorExpertise = $vectorExpertise
    )
    FOREACH (_ IN CASE WHEN $vectorTitle IS NOT NULL THEN [1] ELSE [] END |
        SET j.vectorTitle = $vectorTitle
    )
    FOREACH (_ IN CASE WHEN $vectorQualification IS NOT NULL THEN [1] ELSE [] END |
        SET j.vectorQualification = $vectorQualification
    )
    FOREACH (_ IN CASE WHEN $vectorResponsibility IS NOT NULL THEN [1] ELSE [] END |
        SET j.vectorResponsibility = $vectorResponsibility
    )

    // Liên kết với JobPosition (đảm bảo tính tương thích hai chiều)
    MERGE (jp:JobPosition {jobId: $jdId})
    ON CREATE SET jp.title = $title, jp.status = 'OPEN', jp.createdAt = datetime()
    MERGE (jp)-[:DEFINED_IN_JD]->(j)
    MERGE (j)-[:FOR_POSITION]->(jp)

    // Liên kết với Domain
    WITH j
    FOREACH (_ IN CASE WHEN $domain IS NOT NULL AND $domain <> '' THEN [1] ELSE [] END |
        MERGE (d:Domain {name: $domain})
        MERGE (j)-[:BELONGS_TO_DOMAIN]->(d)
    )

    // Liên kết với Expertise
    WITH j
    FOREACH (_ IN CASE WHEN $expertise IS NOT NULL AND $expertise <> '' THEN [1] ELSE [] END |
        MERGE (e:Expertise {name: $expertise})
        MERGE (j)-[:REQUIRES_EXPERTISE]->(e)
    )

    RETURN j.jdId AS jdId
    """
    client = get_neo4j_client()
    res = client.execute_write(query, {
        "jdId": jd_id,
        "title": title.strip(),
        "domain": domain.strip() if domain else None,
        "expertise": expertise.strip() if expertise else None,
        "qualification": qualification.strip() if qualification else None,
        "responsibility": responsibility.strip() if responsibility else None,
        "experienceYears": int(experience_years) if experience_years is not None else 0,
        "rawText": raw_text or "",
        "cleanText": clean_text or "",
        "embedding": embedding,
        "vectorTitle": vector_title,
        "vectorDomain": vector_domain,
        "vectorExpertise": vector_expertise,
        "vectorQualification": vector_qualification,
        "vectorResponsibility": vector_responsibility,
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


def sync_jd_skill_requirements_graph(
    jd_id: int,
    skills: List[Dict[str, Any]],
    expertise_name: Optional[str] = None
) -> int:
    """
    Đồng bộ danh sách yêu cầu kỹ năng của JD lên Neo4j:
    - Tạo các node (:SkillRequirement) gắn với (:JD) qua [:REQUIRES]
    - Ánh xạ (:SkillRequirement) sang (:Skill) qua [:REFERS_TO_SKILL]
    - Đồng thời duy trì [:REQUIRES_SKILL] trực tiếp từ (:JD) và (:JobPosition) tới (:Skill) để tương thích ngược.
    - Liên kết (:Skill)-[:BELONGS_TO_EXPERTISE]->(:Expertise) nếu có expertise.
    """
    clean_skills = []
    for idx, item in enumerate(skills):
        s_name = item.get("skillName") or item.get("title") or item.get("name")
        if not s_name:
            continue
        req_id = item.get("requirementId") or item.get("id") or int(f"{jd_id}{idx:03d}")
        exp_for_skill = item.get("expertise") or expertise_name
        clean_skills.append({
            "requirementId": req_id,
            "skillId": item.get("skillId"),
            "skillName": s_name.strip(),
            "normalizedName": normalize_skill_name(s_name),
            "importance": float(item.get("importance", 1.0) or 1.0),
            "minYears": float(item.get("minYears", 0.0) or 0.0),
            "vector": item.get("vector"),
            "expertise": exp_for_skill.strip() if exp_for_skill else None
        })

    query = """
    MERGE (jd:JD {jdId: $jdId})
    MERGE (jp:JobPosition {jobId: $jdId})
    WITH jd, jp

    // Xóa các liên kết SkillRequirement cũ của JD
    OPTIONAL MATCH (jd)-[:REQUIRES]->(old_sr:SkillRequirement)
    DETACH DELETE old_sr
    WITH jd, jp

    // Xóa các quan hệ REQUIRES_SKILL cũ
    OPTIONAL MATCH (jd)-[old_r1:REQUIRES_SKILL]->()
    DELETE old_r1
    WITH jd, jp
    OPTIONAL MATCH (jp)-[old_r2:REQUIRES_SKILL]->()
    DELETE old_r2
    WITH jd, jp

    UNWIND $skills AS req
    // 1. Tạo node Skill chuẩn hóa
    MERGE (s:Skill {normalizedName: req.normalizedName})
    ON CREATE SET 
        s.skillId = req.skillId,
        s.name = req.skillName,
        s.createdAt = datetime()

    // 2. Tạo node SkillRequirement cụ thể cho JD
    MERGE (sr:SkillRequirement {requirementId: req.requirementId})
    SET sr.title = req.skillName,
        sr.importance = req.importance,
        sr.minYears = req.minYears,
        sr.updatedAt = datetime()
    WITH jd, jp, s, sr, req
    FOREACH (_ IN CASE WHEN req.vector IS NOT NULL THEN [1] ELSE [] END |
        SET sr.vector = req.vector
    )

    // 3. Liên kết JD -> SkillRequirement -> Skill
    MERGE (jd)-[:REQUIRES]->(sr)
    MERGE (sr)-[:REFERS_TO_SKILL]->(s)

    // 4. Liên kết tắt trực tiếp để tương thích ngược
    MERGE (jd)-[r1:REQUIRES_SKILL]->(s)
    SET r1.importance = req.importance, r1.minYears = req.minYears
    MERGE (jp)-[r2:REQUIRES_SKILL]->(s)
    SET r2.importance = req.importance, r2.minYears = req.minYears

    // 5. Liên kết Skill -> Expertise nếu có
    WITH jd, jp, s, sr, req
    FOREACH (_ IN CASE WHEN req.expertise IS NOT NULL AND req.expertise <> '' THEN [1] ELSE [] END |
        MERGE (e:Expertise {name: req.expertise})
        MERGE (s)-[:BELONGS_TO_EXPERTISE]->(e)
    )

    RETURN count(sr) AS syncedCount
    """
    client = get_neo4j_client()
    res = client.execute_write(query, {
        "jdId": jd_id,
        "skills": clean_skills
    })
    return res[0]["syncedCount"] if res else 0


def sync_job_skills_graph(
    job_id: int,
    skills: List[Dict[str, Any]],
    expertise_name: Optional[str] = None
) -> int:
    """
    Đồng bộ danh sách kỹ năng yêu cầu của JobPosition/JD lên Neo4j theo lô (UNWIND).
    Ủy quyền cho sync_jd_skill_requirements_graph để đồng bộ cả JD, JobPosition, SkillRequirement và Skill.
    """
    return sync_jd_skill_requirements_graph(jd_id=job_id, skills=skills, expertise_name=expertise_name)

