import logging
from typing import List, Dict, Any, Optional
from app.clients.neo4j_client import get_neo4j_client

logger = logging.getLogger(__name__)


def get_job_required_skills_graph(job_id: int) -> List[Dict[str, Any]]:
    query = """
    MATCH (j:JobPosition {jobId: $jobId})-[r:REQUIRES_SKILL]->(s:Skill)
    RETURN 
        s.skillId AS skillId,
        s.name AS name,
        s.category AS category,
        r.importance AS importance,
        r.minYears AS minYears
    ORDER BY r.importance DESC, s.name ASC
    """
    client = get_neo4j_client()
    return client.execute_read(query, {"jobId": job_id})


def get_cv_skills_graph(cv_id: int) -> List[Dict[str, Any]]:
    query = """
    MATCH (c:CV {cvId: $cvId})-[r:HAS_SKILL]->(s:Skill)
    RETURN 
        s.skillId AS skillId,
        s.name AS name,
        s.category AS category,
        r.confidence AS confidence,
        r.source AS source
    ORDER BY r.confidence DESC, s.name ASC
    """
    client = get_neo4j_client()
    return client.execute_read(query, {"cvId": cv_id})


def get_cv_educations_graph(cv_id: int) -> List[Dict[str, Any]]:
    query = """
    MATCH (c:CV {cvId: $cvId})-[:HAS_EDUCATION]->(e:Education)
    OPTIONAL MATCH (e)-[:OF_LEVEL]->(el:EducationLevel)
    RETURN
        e.educationId AS educationId,
        e.school AS school,
        e.major AS major,
        e.degree AS degree,
        coalesce(el.name, e.level) AS level,
        e.graduationYear AS graduationYear,
        e.gpa AS gpa
    ORDER BY e.graduationYear DESC
    """
    client = get_neo4j_client()
    return client.execute_read(query, {"cvId": cv_id})


def get_cv_work_experiences_graph(cv_id: int) -> List[Dict[str, Any]]:
    query = """
    MATCH (c:CV {cvId: $cvId})-[:HAS_EXPERIENCE]->(w:WorkExperience)
    OPTIONAL MATCH (w)-[:IN_DOMAIN]->(d:Domain)
    OPTIONAL MATCH (w)-[:IN_EXPERTISE]->(ex:Expertise)
    RETURN
        w.experienceId AS experienceId,
        coalesce(d.name, w.domain) AS domain,
        coalesce(ex.name, w.expertise) AS expertise,
        w.responsibility AS responsibility,
        w.years AS years
    ORDER BY w.years DESC
    """
    client = get_neo4j_client()
    return client.execute_read(query, {"cvId": cv_id})


def get_job_education_requirements_graph(job_id: int) -> List[Dict[str, Any]]:
    query = """
    MATCH (j:JD {jdId: $jobId})
    OPTIONAL MATCH (j)-[:REQUIRES_EDUCATION_LEVEL]->(el:EducationLevel)
    RETURN
        j.jdId AS jobId,
        j.qualification AS qualification,
        el.name AS requiredLevel,
        j.experienceYears AS minExperienceYears
    """
    client = get_neo4j_client()
    return client.execute_read(query, {"jobId": job_id})


def analyze_skill_gap_graph(cv_id: int, job_id: int) -> Dict[str, Any]:
    """
    Truy vấn phân tích Skill Gap và giải thích chi tiết mức độ phù hợp giữa một CV và một vị trí việc làm / JD.
    Phân tách rõ ràng:
    1. Kỹ năng khớp (Matched Skills)
    2. Kỹ năng còn thiếu (Missing Skills - Gap)
    3. Kỹ năng bổ trợ (Extra Skills / Strengths)
    4. Tỷ lệ bao phủ kỹ năng có trọng số (Weighted Skill Coverage Ratio)
    Hỗ trợ tìm qua cả node (:JobPosition) và (:JD) cũng như qua (:SkillRequirement).
    """
    query = """
    MATCH (c:CV {cvId: $cvId})
    OPTIONAL MATCH (jp:JobPosition {jobId: $jobId})
    OPTIONAL MATCH (jd:JD {jdId: $jobId})
    WITH c, coalesce(jd, jp) AS j
    WHERE j IS NOT NULL

    // 1. Matched Skills: CV có và Job/JD yêu cầu
    OPTIONAL MATCH (c)-[hc:HAS_SKILL]->(matched:Skill)
    WHERE (j)-[:REQUIRES_SKILL]->(matched) OR (j)-[:REQUIRES]->(:SkillRequirement)-[:REFERS_TO_SKILL]->(matched)
    OPTIONAL MATCH (j)-[rj:REQUIRES_SKILL]->(matched)
    OPTIONAL MATCH (j)-[:REQUIRES]->(sr:SkillRequirement)-[:REFERS_TO_SKILL]->(matched)
    WITH c, j,
         [s IN collect(DISTINCT CASE WHEN matched IS NOT NULL THEN {
             skillId: matched.skillId,
             name: matched.name,
             category: matched.category,
             importance: coalesce(rj.importance, sr.importance, 1.0),
             confidence: coalesce(hc.confidence, 1.0)
         } END) WHERE s IS NOT NULL] AS matchedSkills

    // 2. Missing Skills: Job/JD yêu cầu nhưng CV KHÔNG có
    OPTIONAL MATCH (missing:Skill)
    WHERE ((j)-[:REQUIRES_SKILL]->(missing) OR (j)-[:REQUIRES]->(:SkillRequirement)-[:REFERS_TO_SKILL]->(missing))
      AND NOT (c)-[:HAS_SKILL]->(missing)
    OPTIONAL MATCH (j)-[rj2:REQUIRES_SKILL]->(missing)
    OPTIONAL MATCH (j)-[:REQUIRES]->(sr2:SkillRequirement)-[:REFERS_TO_SKILL]->(missing)
    WITH c, j, matchedSkills,
         [s IN collect(DISTINCT CASE WHEN missing IS NOT NULL THEN {
             skillId: missing.skillId,
             name: missing.name,
             category: missing.category,
             importance: coalesce(rj2.importance, sr2.importance, 1.0),
             minYears: coalesce(rj2.minYears, sr2.minYears, 0.0)
         } END) WHERE s IS NOT NULL] AS missingSkills

    // Tính trọng số an toàn bằng reduce, tránh tính trùng từ Cartesian product
    WITH c, j, matchedSkills, missingSkills,
         reduce(acc = 0.0, s IN matchedSkills | acc + s.importance) AS matchedWeight,
         reduce(acc = 0.0, s IN missingSkills | acc + s.importance) AS missingWeight

    // 3. Extra Skills: CV có nhưng Job/JD KHÔNG yêu cầu
    OPTIONAL MATCH (c)-[hc2:HAS_SKILL]->(extra:Skill)
    WHERE NOT (j)-[:REQUIRES_SKILL]->(extra) AND NOT (j)-[:REQUIRES]->(:SkillRequirement)-[:REFERS_TO_SKILL]->(extra)
    WITH matchedSkills, missingSkills, matchedWeight, missingWeight,
         [s IN collect(DISTINCT CASE WHEN extra IS NOT NULL THEN {
             skillId: extra.skillId,
             name: extra.name,
             category: extra.category,
             confidence: coalesce(hc2.confidence, 1.0)
         } END) WHERE s IS NOT NULL] AS extraSkills

    // 4. Tính toán tỷ lệ bao phủ kỹ năng (Skill Coverage)
    WITH matchedSkills, missingSkills, extraSkills,
         matchedWeight, missingWeight,
         (matchedWeight + missingWeight) AS totalRequiredWeight

    RETURN {
        cvId: $cvId,
        jobId: $jobId,
        totalRequiredSkills: size(matchedSkills) + size(missingSkills),
        totalMatchedSkills: size(matchedSkills),
        totalMissingSkills: size(missingSkills),
        totalExtraSkills: size(extraSkills),
        matchedSkills: matchedSkills,
        missingSkills: missingSkills,
        extraSkills: extraSkills,
        matchedWeight: round(matchedWeight, 4),
        totalRequiredWeight: round(totalRequiredWeight, 4),
        skillCoverageRatio: CASE WHEN totalRequiredWeight > 0.0
                                 THEN round(matchedWeight / totalRequiredWeight, 4)
                                 ELSE 0.0 END
    } AS result
    """
    client = get_neo4j_client()
    res = client.execute_read(query, {"cvId": cv_id, "jobId": job_id})
    if res and "result" in res[0]:
        return res[0]["result"]
    return {
        "cvId": cv_id,
        "jobId": job_id,
        "totalRequiredSkills": 0,
        "totalMatchedSkills": 0,
        "totalMissingSkills": 0,
        "totalExtraSkills": 0,
        "matchedSkills": [],
        "missingSkills": [],
        "extraSkills": [],
        "skillCoverageRatio": 0.0,
    }


def save_cv_jd_match_result_graph(cv_id: int, jd_id: int, scores: Dict[str, Any]) -> Dict[str, Any]:
    """
    Lưu kết quả so khớp 1 vs 1 giữa CV và JD:
    - Tạo node (:MatchResult) lưu điểm số mới nhất cho mỗi cặp CV–JD
    - Tạo cạnh (:CV)-[:HAS_MATCH_RESULT]->(:MatchResult)-[:FOR_JD]->(:JD)
    - Tạo cạnh tắt trực tiếp (:CV)-[:MATCHES_JD]->(:JD)
    """
    query = """
    MATCH (c:CV {cvId: $cvId})
    MERGE (jd:JD {jdId: $jdId})

    // 1. Lưu quan hệ MATCHES_JD trực tiếp giữa CV và JD
    MERGE (c)-[r:MATCHES_JD]->(jd)
    SET r.totalResult = $totalResult,
        r.domainScore = $domainScore,
        r.expertiseScore = $expertiseScore,
        r.skillScore = $skillScore,
        r.experienceScore = $experienceScore,
        r.qualificationScore = $qualificationScore,
        r.matchedAt = datetime()

    // 2. Tạo Node MatchResult đại diện cho thực thể kết quả đánh giá
    MERGE (m:MatchResult {matchResultId: $matchResultId})
    SET m.cvId = $cvId,
        m.jdId = $jdId,
        m.totalResult = $totalResult,
        m.domainScore = $domainScore,
        m.expertiseScore = $expertiseScore,
        m.skillScore = $skillScore,
        m.experienceScore = $experienceScore,
        m.qualificationScore = $qualificationScore,
        m.matchedAt = datetime()

    MERGE (c)-[:HAS_MATCH_RESULT]->(m)
    MERGE (m)-[:FOR_JD]->(jd)

    RETURN r.totalResult AS totalResult, m.matchResultId AS matchResultId
    """
    client = get_neo4j_client()
    match_result_id = f"{cv_id}:{jd_id}"
    res = client.execute_write(query, {
        "cvId": cv_id,
        "jdId": jd_id,
        "matchResultId": match_result_id,
        "totalResult": float(scores.get("totalResult", 0.0)),
        "domainScore": float(scores.get("domainScore", 0.0)),
        "expertiseScore": float(scores.get("expertiseScore", 0.0)),
        "skillScore": float(scores.get("skillScore", 0.0)),
        "experienceScore": float(scores.get("experienceScore", 0.0)),
        "qualificationScore": float(scores.get("qualificationScore", 0.0)),
    })
    return res[0] if res else {}


def hybrid_match_cvs_for_job_graph(
    job_id: int,
    job_vector: Optional[List[float]] = None,
    top_k: int = 10,
    min_score: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Tìm kiếm và xếp hạng ứng viên phù hợp nhất cho một vị trí công việc:
    - Nếu có vector: Sử dụng Vector Index lấy ứng viên tiềm năng + duyệt đồ thị tính điểm kỹ năng.
    - Nếu chưa có vector: Duyệt trực tiếp đồ thị tính điểm Skill Coverage của tất cả CV đang có.
    """
    client = get_neo4j_client()

    if job_vector and len(job_vector) == 384:
        query = """
        CALL db.index.vector.queryNodes('cv_vector_idx', $top_k, $job_vector)
        YIELD node AS c, score AS vectorScore
        WHERE vectorScore >= $min_score
        MATCH (j:JobPosition {jobId: $jobId})
        MATCH (u:User)-[:OWNS_CV]->(c)

        OPTIONAL MATCH (c)-[hc:HAS_SKILL]->(s:Skill)<-[rj:REQUIRES_SKILL]-(j)
        WITH c, u, j, vectorScore,
             collect(DISTINCT CASE WHEN s IS NOT NULL THEN {name: s.name, importance: coalesce(rj.importance, 1.0)} END) AS matchedSkills,
             sum(CASE WHEN s IS NOT NULL THEN coalesce(rj.importance, 1.0) ELSE 0.0 END) AS matchedWeight

        OPTIONAL MATCH (j)-[rj2:REQUIRES_SKILL]->(missing:Skill)
        WHERE NOT (c)-[:HAS_SKILL]->(missing)
        WITH c, u, vectorScore, matchedSkills, matchedWeight,
             collect(DISTINCT CASE WHEN missing IS NOT NULL THEN {name: missing.name, importance: coalesce(rj2.importance, 1.0)} END) AS missingSkills,
             sum(CASE WHEN missing IS NOT NULL THEN coalesce(rj2.importance, 1.0) ELSE 0.0 END) AS missingWeight

        WITH c, u, vectorScore, matchedSkills, missingSkills,
             CASE WHEN (matchedWeight + missingWeight) > 0.0 
                  THEN matchedWeight / (matchedWeight + missingWeight)
                  ELSE 0.0 END AS graphSkillScore

        // Trọng số: 45% ngữ nghĩa tổng thể (Vector), 35% kỹ năng đồ thị (Graph), còn lại kinh nghiệm/học vấn
        WITH c, u, vectorScore, graphSkillScore, matchedSkills, missingSkills,
             round(0.50 * vectorScore + 0.50 * graphSkillScore, 4) AS hybridScore

        RETURN 
            c.cvId AS cvId,
            c.title AS candidateTitle,
            u.email AS candidateEmail,
            vectorScore,
            graphSkillScore,
            hybridScore,
            matchedSkills,
            missingSkills
        ORDER BY hybridScore DESC
        LIMIT $top_k
        """
        return client.execute_read(query, {
            "jobId": job_id,
            "job_vector": job_vector,
            "top_k": top_k,
            "min_score": min_score
        })
    else:
        # Fallback graph-only matching khi không có vector
        query = """
        MATCH (j:JobPosition {jobId: $jobId})
        MATCH (c:CV)
        MATCH (u:User)-[:OWNS_CV]->(c)

        OPTIONAL MATCH (c)-[hc:HAS_SKILL]->(s:Skill)<-[rj:REQUIRES_SKILL]-(j)
        WITH c, u, j,
             collect(DISTINCT CASE WHEN s IS NOT NULL THEN {name: s.name, importance: coalesce(rj.importance, 1.0)} END) AS matchedSkills,
             sum(CASE WHEN s IS NOT NULL THEN coalesce(rj.importance, 1.0) ELSE 0.0 END) AS matchedWeight

        OPTIONAL MATCH (j)-[rj2:REQUIRES_SKILL]->(missing:Skill)
        WHERE NOT (c)-[:HAS_SKILL]->(missing)
        WITH c, u, matchedSkills, matchedWeight,
             collect(DISTINCT CASE WHEN missing IS NOT NULL THEN {name: missing.name, importance: coalesce(rj2.importance, 1.0)} END) AS missingSkills,
             sum(CASE WHEN missing IS NOT NULL THEN coalesce(rj2.importance, 1.0) ELSE 0.0 END) AS missingWeight

        WITH c, u, matchedSkills, missingSkills,
             CASE WHEN (matchedWeight + missingWeight) > 0.0 
                  THEN round(matchedWeight / (matchedWeight + missingWeight), 4)
                  ELSE 0.0 END AS graphSkillScore

        RETURN 
            c.cvId AS cvId,
            c.title AS candidateTitle,
            u.email AS candidateEmail,
            0.0 AS vectorScore,
            graphSkillScore,
            graphSkillScore AS hybridScore,
            matchedSkills,
            missingSkills
        ORDER BY hybridScore DESC
        LIMIT $top_k
        """
        return client.execute_read(query, {
            "jobId": job_id,
            "top_k": top_k
        })
