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


def analyze_skill_gap_graph(cv_id: int, job_id: int) -> Dict[str, Any]:
    """
    Truy vấn phân tích Skill Gap và giải thích chi tiết mức độ phù hợp giữa một CV và một vị trí việc làm.
    Phân tách rõ ràng:
    1. Kỹ năng khớp (Matched Skills)
    2. Kỹ năng còn thiếu (Missing Skills - Gap)
    3. Kỹ năng bổ trợ (Extra Skills / Strengths)
    4. Tỷ lệ bao phủ kỹ năng có trọng số (Weighted Skill Coverage Ratio)
    """
    query = """
    MATCH (c:CV {cvId: $cvId})
    MATCH (j:JobPosition {jobId: $jobId})

    // 1. Matched Skills: CV có và Job yêu cầu
    OPTIONAL MATCH (c)-[hc:HAS_SKILL]->(matched:Skill)<-[rj:REQUIRES_SKILL]-(j)
    WITH c, j, collect(DISTINCT CASE WHEN matched IS NOT NULL THEN {
        skillId: matched.skillId,
        name: matched.name,
        category: matched.category,
        importance: coalesce(rj.importance, 1.0),
        confidence: coalesce(hc.confidence, 1.0)
    } END) AS matchedSkills, sum(coalesce(rj.importance, 0.0)) AS matchedWeight

    // 2. Missing Skills: Job yêu cầu nhưng CV KHÔNG có
    OPTIONAL MATCH (j)-[rj2:REQUIRES_SKILL]->(missing:Skill)
    WHERE NOT (c)-[:HAS_SKILL]->(missing)
    WITH c, j, matchedSkills, matchedWeight, collect(DISTINCT CASE WHEN missing IS NOT NULL THEN {
        skillId: missing.skillId,
        name: missing.name,
        category: missing.category,
        importance: coalesce(rj2.importance, 1.0),
        minYears: coalesce(rj2.minYears, 0.0)
    } END) AS missingSkills, sum(coalesce(rj2.importance, 0.0)) AS missingWeight

    // 3. Extra Skills: CV có nhưng Job KHÔNG yêu cầu
    OPTIONAL MATCH (c)-[hc2:HAS_SKILL]->(extra:Skill)
    WHERE NOT (j)-[:REQUIRES_SKILL]->(extra)
    WITH matchedSkills, matchedWeight, missingSkills, missingWeight, collect(DISTINCT CASE WHEN extra IS NOT NULL THEN {
        skillId: extra.skillId,
        name: extra.name,
        category: extra.category,
        confidence: coalesce(hc2.confidence, 1.0)
    } END) AS extraSkills

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
        matchedWeight: matchedWeight,
        totalRequiredWeight: totalRequiredWeight,
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
             collect(DISTINCT {name: s.name, importance: coalesce(rj.importance, 1.0)}) AS matchedSkills,
             sum(coalesce(rj.importance, 1.0)) AS matchedWeight

        OPTIONAL MATCH (j)-[rj2:REQUIRES_SKILL]->(missing:Skill)
        WHERE NOT (c)-[:HAS_SKILL]->(missing)
        WITH c, u, vectorScore, matchedSkills, matchedWeight,
             collect(DISTINCT {name: missing.name, importance: coalesce(rj2.importance, 1.0)}) AS missingSkills,
             sum(coalesce(rj2.importance, 1.0)) AS missingWeight

        WITH c, u, vectorScore, matchedSkills, missingSkills,
             CASE WHEN (matchedWeight + missingWeight) > 0.0 
                  THEN matchedWeight / (matchedWeight + missingWeight)
                  ELSE 0.0 END AS graphSkillScore

        // Trọng số: 45% ngữ nghĩa tổng thể (Vector), 35% kỹ năng đồ thị (Graph), còn lại kinh nghiệm/học vấn
        WITH c, u, vectorScore, graphSkillScore, matchedSkills, missingSkills,
             round(0.50 * vectorScore + 0.50 * graphSkillScore, 4) AS hybridScore

        RETURN 
            c.cvId AS cvId,
            u.fullName AS candidateName,
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
             collect(DISTINCT {name: s.name, importance: coalesce(rj.importance, 1.0)}) AS matchedSkills,
             sum(coalesce(rj.importance, 1.0)) AS matchedWeight

        OPTIONAL MATCH (j)-[rj2:REQUIRES_SKILL]->(missing:Skill)
        WHERE NOT (c)-[:HAS_SKILL]->(missing)
        WITH c, u, matchedSkills, matchedWeight,
             collect(DISTINCT {name: missing.name, importance: coalesce(rj2.importance, 1.0)}) AS missingSkills,
             sum(coalesce(rj2.importance, 1.0)) AS missingWeight

        WITH c, u, matchedSkills, missingSkills,
             CASE WHEN (matchedWeight + missingWeight) > 0.0 
                  THEN round(matchedWeight / (matchedWeight + missingWeight), 4)
                  ELSE 0.0 END AS graphSkillScore

        RETURN 
            c.cvId AS cvId,
            u.fullName AS candidateName,
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
