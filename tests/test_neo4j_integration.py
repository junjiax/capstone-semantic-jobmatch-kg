"""
Bộ kiểm thử tích hợp Neo4j Knowledge Graph & Skill Gap Analysis.
Chạy bằng lệnh:
  python -m pytest tests/test_neo4j_integration.py -v
"""
import pytest
from app.clients.neo4j_client import get_neo4j_client
from app.crud.graph.schema import init_graph_schema
from app.crud.graph.sync_crud import (
    upsert_user_node,
    upsert_skill_node,
    upsert_job_position_node,
    upsert_cv_node,
    upsert_domain_node,
    upsert_expertise_node,
    upsert_jd_node,
    sync_cv_skills_graph,
    sync_job_skills_graph,
    sync_jd_skill_requirements_graph,
)
from app.crud.graph.match_crud import (
    get_job_required_skills_graph,
    get_cv_skills_graph,
    analyze_skill_gap_graph,
    save_cv_jd_match_result_graph,
    get_domain_skill_gap_matrix_graph,
)


@pytest.fixture(scope="module")
def neo4j_client():
    client = get_neo4j_client()
    try:
        client.driver.verify_connectivity()
    except Exception as e:
        pytest.skip(f"Neo4j chưa khởi động hoặc không khả dụng: {e}")
    # Khởi tạo schema
    init_graph_schema()
    yield client


def test_neo4j_connectivity(neo4j_client):
    """Test 1: Kết nối tới Neo4j thành công."""
    res = neo4j_client.execute_read("RETURN 1 AS num")
    assert res is not None
    assert len(res) == 1
    assert res[0]["num"] == 1


def test_idempotent_skill_creation(neo4j_client):
    """Test 2: Tạo node Skill hai lần (kể cả khác chữ hoa/thường) không sinh trùng lặp."""
    # Lần 1: Python
    res1 = upsert_skill_node(skill_id=9991, name="Python", category="Backend")
    # Lần 2: pYtHoN (khác case)
    res2 = upsert_skill_node(skill_id=9991, name="pYtHoN", category="Backend")

    # Kiểm tra chỉ có đúng 1 node trên đồ thị với normalizedName 'python'
    query = "MATCH (s:Skill {normalizedName: 'python'}) RETURN count(s) AS total"
    records = neo4j_client.execute_read(query)
    assert records[0]["total"] == 1


def test_idempotent_cv_and_job_sync(neo4j_client):
    """Test 3: Đồng bộ CV và JobPosition kèm kỹ năng không nhân đôi quan hệ khi chạy lại."""
    # 1. Tạo User & CV
    upsert_user_node(user_id=888, email="candidate_test@example.com", full_name="Candidate Test", role="applicant")
    upsert_cv_node(cv_id=888, user_id=888, language="vi", summary="Backend Developer")

    # 2. Tạo Job
    upsert_job_position_node(job_id=777, title="Python Backend Engineer", min_experience=2.0)

    # 3. Đồng bộ kỹ năng cho CV lần 1
    cv_skills_1 = [
        {"skillId": 101, "skillName": "Python", "confidence": 0.95},
        {"skillId": 102, "skillName": "FastAPI", "confidence": 0.90},
        {"skillId": 103, "skillName": "React", "confidence": 0.70},  # Kỹ năng bổ trợ không yêu cầu
    ]
    sync_cv_skills_graph(cv_id=888, skills=cv_skills_1)

    # 4. Đồng bộ lại lần 2 (idempotency check)
    sync_cv_skills_graph(cv_id=888, skills=cv_skills_1)

    # Kiểm tra số quan hệ HAS_SKILL của CV 888 đúng bằng 3
    q_cv = "MATCH (c:CV {cvId: 888})-[r:HAS_SKILL]->() RETURN count(r) AS total"
    assert neo4j_client.execute_read(q_cv)[0]["total"] == 3

    # 5. Đồng bộ kỹ năng yêu cầu cho Job 777
    job_skills_1 = [
        {"skillId": 101, "skillName": "Python", "importance": 2.0, "minYears": 2.0},
        {"skillId": 102, "skillName": "FastAPI", "importance": 1.5, "minYears": 1.0},
        {"skillId": 104, "skillName": "Docker", "importance": 1.0, "minYears": 1.0},     # Thiếu
        {"skillId": 105, "skillName": "PostgreSQL", "importance": 1.5, "minYears": 1.0}, # Thiếu
    ]
    sync_job_skills_graph(job_id=777, skills=job_skills_1)
    sync_job_skills_graph(job_id=777, skills=job_skills_1) # Chạy lại

    # Kiểm tra số quan hệ REQUIRES_SKILL của Job 777 đúng bằng 4
    q_job = "MATCH (j:JobPosition {jobId: 777})-[r:REQUIRES_SKILL]->() RETURN count(r) AS total"
    assert neo4j_client.execute_read(q_job)[0]["total"] == 4


def test_skill_gap_analysis(neo4j_client):
    """Test 4: Tính toán chính xác Skill Gap, Matched Skills, Missing Skills và Coverage Ratio."""
    res = analyze_skill_gap_graph(cv_id=888, job_id=777)

    assert res["totalRequiredSkills"] == 4
    assert res["totalMatchedSkills"] == 2
    assert res["totalMissingSkills"] == 2
    assert res["totalExtraSkills"] == 1

    matched_names = {s["name"].lower() for s in res["matchedSkills"]}
    missing_names = {s["name"].lower() for s in res["missingSkills"]}
    extra_names = {s["name"].lower() for s in res["extraSkills"]}

    assert "python" in matched_names
    assert "fastapi" in matched_names
    assert "docker" in missing_names
    assert "postgresql" in missing_names
    assert "react" in extra_names

    # Kiểm tra tỷ lệ bao phủ kỹ năng:
    # Matched weight: Python (2.0) + FastAPI (1.5) = 3.5
    # Total required weight: 2.0 + 1.5 + 1.0 + 1.5 = 6.0
    # Ratio = 3.5 / 6.0 ≈ 0.5833
    assert pytest.approx(res["skillCoverageRatio"], 0.001) == 0.5833


def test_empty_cv_skills(neo4j_client):
    """Test 5: Trường hợp CV không có bất kỳ kỹ năng nào."""
    upsert_cv_node(cv_id=999, user_id=888, language="en")
    sync_cv_skills_graph(cv_id=999, skills=[])

    res = analyze_skill_gap_graph(cv_id=999, job_id=777)
    assert res["totalMatchedSkills"] == 0
    assert res["totalMissingSkills"] == 4
    assert res["skillCoverageRatio"] == 0.0


def test_jd_domain_and_skill_requirements(neo4j_client):
    """Test 6: Kiểm tra tạo node JD, Domain, Expertise và SkillRequirement."""
    # 1. Tạo Domain & Expertise
    upsert_domain_node(name="Backend Development", description="Lập trình hệ thống máy chủ")
    upsert_expertise_node(name="Python Engineering", domain_name="Backend Development")

    # 2. Tạo JD liên kết với Domain & Expertise
    upsert_jd_node(
        jd_id=778,
        title="Senior Backend Python Developer",
        domain="Backend Development",
        expertise="Python Engineering",
        qualification="Bachelor of Computer Science",
        experience_years=3
    )

    # 3. Đồng bộ SkillRequirement cho JD
    jd_reqs = [
        {"requirementId": 77801, "skillName": "Python", "importance": 2.0, "minYears": 3.0},
        {"requirementId": 77802, "skillName": "FastAPI", "importance": 1.5, "minYears": 2.0},
    ]
    sync_jd_skill_requirements_graph(jd_id=778, skills=jd_reqs)

    # 4. Kiểm tra trên đồ thị
    q_jd = "MATCH (jd:JD {jdId: 778})-[:BELONGS_TO_DOMAIN]->(d:Domain {name: 'Backend Development'}) RETURN count(jd) AS total"
    assert neo4j_client.execute_read(q_jd)[0]["total"] == 1

    q_req = "MATCH (jd:JD {jdId: 778})-[:REQUIRES]->(sr:SkillRequirement)-[:REFERS_TO_SKILL]->(s:Skill) RETURN count(sr) AS total"
    assert neo4j_client.execute_read(q_req)[0]["total"] == 2


def test_problem1_skill_matching_score(neo4j_client):
    """
    Test 7: BÀI TOÁN 1: Skill Matching (1 CV vs 1 JD).
    Trả lời: 'CV của tôi có phù hợp với JD này không?'
    Kiểm tra điểm số trả về là float [0, 1] và lưu cạnh MATCHES_JD.
    """
    scores = {
        "totalResult": 0.8250,
        "skillScore": 0.8500,
        "domainScore": 0.8000,
        "expertiseScore": 0.8500,
        "experienceScore": 0.8000,
        "qualificationScore": 0.8000
    }
    save_cv_jd_match_result_graph(cv_id=888, jd_id=778, scores=scores)

    # Kiểm tra cạnh MATCHES_JD
    q_match = "MATCH (c:CV {cvId: 888})-[r:MATCHES_JD]->(jd:JD {jdId: 778}) RETURN r.totalResult AS totalResult, r.skillScore AS skillScore"
    records = neo4j_client.execute_read(q_match)
    assert len(records) == 1
    total_score = records[0]["totalResult"]
    assert 0.0 <= total_score <= 1.0
    assert pytest.approx(total_score, 0.001) == 0.8250


def test_problem2_domain_gap_matrix(neo4j_client):
    """
    Test 8: BÀI TOÁN 2: Skill Gap Analysis & Domain Orientation (1 CV vs Many Domains).
    Trả lời: 'CV của tôi có thể apply vào những domain nào trong CNTT?'
    Kiểm tra ma trận tương quan và tỷ lệ bao phủ theo domain.
    """
    # CV 888 có kỹ năng Python, FastAPI, React (đã sync ở test 3)
    domain_gaps = get_domain_skill_gap_matrix_graph(cv_id=888, target_domains=["Backend Development"])
    assert len(domain_gaps) == 1
    backend_gap = domain_gaps[0]
    assert backend_gap["domainName"] == "Backend Development"
    assert backend_gap["totalDomainSkills"] >= 2
    # Tỷ lệ bao phủ phải nằm trong khoảng [0.0, 1.0]
    assert 0.0 <= backend_gap["skillCoverageRatio"] <= 1.0
    assert backend_gap["totalMatchedSkills"] >= 1


def test_cleanup_test_data(neo4j_client):
    """Dọn dẹp dữ liệu test."""
    cleanup_query = """
    MATCH (u:User) WHERE u.userId IN [888] DETACH DELETE u
    WITH count(*) AS dummy
    MATCH (c:CV) WHERE c.cvId IN [888, 999] DETACH DELETE c
    WITH count(*) AS dummy
    MATCH (j:JobPosition) WHERE j.jobId IN [777, 778] DETACH DELETE j
    WITH count(*) AS dummy
    MATCH (jd:JD) WHERE jd.jdId IN [777, 778] DETACH DELETE jd
    WITH count(*) AS dummy
    MATCH (sr:SkillRequirement) WHERE sr.requirementId IN [77801, 77802] DETACH DELETE sr
    WITH count(*) AS dummy
    MATCH (d:Domain) WHERE d.name IN ['Backend Development'] DETACH DELETE d
    WITH count(*) AS dummy
    MATCH (e:Expertise) WHERE e.name IN ['Python Engineering'] DETACH DELETE e
    WITH count(*) AS dummy
    MATCH (s:Skill) WHERE s.skillId IN [9991, 101, 102, 103, 104, 105] DETACH DELETE s
    """
    neo4j_client.execute_write(cleanup_query)

