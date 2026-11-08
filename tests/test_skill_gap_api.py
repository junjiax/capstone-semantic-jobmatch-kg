"""
tests/test_skill_gap_api.py
Bộ kiểm thử tự động cho chức năng Skill Gap Analysis.
Chạy bằng lệnh:
    python -m pytest tests/test_skill_gap_api.py -v
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.skill_features.skill_gap_analysis import analyze_skill_gap_service
from app.schemas.skill_gap import SkillGapAnalysisRequest


@pytest.fixture
def client():
    return TestClient(app)


def test_skill_gap_exact_and_semantic_matching():
    """
    Test 1: Kiểm tra phân loại chính xác 3 nhóm:
    - Python: MATCHED (Exact)
    - MySQL: PARTIALLY_MATCHED với PostgreSQL (Semantic)
    - Docker: MISSING (Ứng viên không có kỹ năng DevOps nào)
    - Git: EXTRA (Ứng viên có nhưng JD không bắt buộc)
    """
    request = SkillGapAnalysisRequest(
        candidate_skills=["Python", "MySQL", "Git"],
        required_skills=["Python", "PostgreSQL", "Docker"],
        match_threshold=0.82,
        partial_threshold=0.60,
    )

    result = analyze_skill_gap_service(db=None, request=request)

    # 1. Kiểm tra thống kê tổng thể
    assert result.summary.total_required_skills == 3
    assert result.summary.total_matched_skills == 1
    assert result.summary.total_partial_skills == 1
    assert result.summary.total_missing_skills == 1
    assert result.summary.total_extra_skills == 1

    # 2. Kiểm tra chi tiết Matched Skill
    matched_names = [s.skill_name.lower() for s in result.matched_skills]
    assert "python" in matched_names
    assert result.matched_skills[0].is_exact_match is True

    # 3. Kiểm tra chi tiết Partial Skill
    partial_names = [s.skill_name.lower() for s in result.partially_matched_skills]
    assert "postgresql" in partial_names
    partial_item = result.partially_matched_skills[0]
    assert partial_item.closest_candidate_skill.lower() == "mysql"
    assert partial_item.similarity_score >= 0.60

    # 4. Kiểm tra chi tiết Missing Skill
    missing_names = [s.skill_name.lower() for s in result.missing_skills]
    assert "docker" in missing_names

    # 5. Kiểm tra Extra Skill
    extra_names = [s.skill_name.lower() for s in result.extra_skills]
    assert "git" in extra_names


def test_skill_gap_near_identical_semantic_match():
    """
    Test 2: Kiểm tra khi tên không giống nhau 100% nhưng ngữ nghĩa tương đương rất cao.
    Ví dụ: 'RESTful API' vs 'REST APIs' -> Phải được coi là MATCHED (do similarity >= 0.82).
    """
    request = SkillGapAnalysisRequest(
        candidate_skills=["RESTful APIs", "FastAPI"],
        required_skills=["REST API", "FastAPI"],
        match_threshold=0.80,
    )

    result = analyze_skill_gap_service(db=None, request=request)
    assert result.summary.total_matched_skills == 2
    assert result.summary.total_missing_skills == 0
    assert result.summary.fit_level in ["EXCELLENT", "GOOD"]


def test_skill_gap_completely_missing_skills():
    """
    Test 3: Ứng viên không có kỹ năng nào liên quan đến JD.
    """
    request = SkillGapAnalysisRequest(
        candidate_skills=["Adobe Photoshop", "Figma", "Canva"],
        required_skills=["Kubernetes", "Golang", "Kafka"],
    )

    result = analyze_skill_gap_service(db=None, request=request)
    assert result.summary.total_matched_skills == 0
    assert result.summary.total_missing_skills == 3
    assert result.summary.skill_coverage_percentage < 30.0
    assert result.summary.fit_level == "LOW"
    assert len(result.recommendations) >= 3


def test_api_endpoint_analyze_with_direct_skills(client):
    """
    Test 4: Gọi trực tiếp Endpoint POST /api/v1/skill-gap/analyze qua TestClient.
    """
    payload = {
        "candidate_skills": ["Python", "FastAPI", "Pandas"],
        "required_skills": ["Python", "PyTorch", "Docker"],
        "match_threshold": 0.82,
        "partial_threshold": 0.60
    }

    response = client.post("/api/v1/skill-gap/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "data" in data

    res_data = data["data"]
    assert res_data["summary"]["total_required_skills"] == 3
    assert len(res_data["matched_skills"]) >= 1
    assert len(res_data["recommendations"]) > 0


def test_api_endpoint_validation_error(client):
    """
    Test 5: Bắt lỗi Validation HTTP 400 khi không truyền bất kỳ thông tin nào.
    """
    payload = {}
    response = client.post("/api/v1/skill-gap/analyze", json=payload)
    assert response.status_code == 400