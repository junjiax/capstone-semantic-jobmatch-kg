"""Endpoint tests for /api/v1/skill-gap (ported from the old tests/test_skill_gap_api.py)."""

import pytest

pytestmark = pytest.mark.api


def test_analyze_with_direct_skills(client):
    payload = {
        "candidate_skills": ["Python", "FastAPI", "Pandas"],
        "required_skills": ["Python", "PyTorch", "Docker"],
        "match_threshold": 0.82,
        "partial_threshold": 0.60,
    }
    response = client.post("/api/v1/skill-gap/analyze", json=payload)
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["summary"]["total_required_skills"] == 3
    assert len(data["matched_skills"]) >= 1
    assert len(data["recommendations"]) > 0


def test_analyze_without_any_input_returns_400(client):
    response = client.post("/api/v1/skill-gap/analyze", json={})
    assert response.status_code == 400


def test_health_endpoint(client):
    response = client.get("/api/v1/skill-gap/health")
    assert response.status_code == 200
    assert response.json()["status"] == "active"
