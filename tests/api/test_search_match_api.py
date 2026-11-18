"""Endpoint tests for /semantic-search, /skill-gap (theo id) và /graph/match-similarity."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.schemas.semantic_search import SkillSearchResponse, SkillSearchResultItem

pytestmark = pytest.mark.api


@pytest.fixture(autouse=True)
def _db(override_db, mock_db):
    override_db(mock_db)


# ── semantic search ─────────────────────────────────────────────────────────
def test_search_skills_ok(client, monkeypatch):
    seen = {}

    def fake(db, request):
        seen["request"] = request
        return SkillSearchResponse(
            query=request.query, model_name="fake-minilm", total_results=1,
            results=[SkillSearchResultItem(id=1, title="Python", similarity=0.9,
                                           source="PROFILE_SKILL", entity_id=2)],
        )

    monkeypatch.setattr("app.api.v1.routers.router.semantic_search.service.search_skills_semantic", fake)
    r = client.post("/api/v1/semantic-search/skills", json={"query": "python", "top_k": 3})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True and body["data"]["results"][0]["title"] == "Python"
    assert seen["request"].top_k == 3 and seen["request"].source == "all"


@pytest.mark.parametrize(
    "payload",
    [{}, {"query": ""}, {"query": "x", "top_k": 0}, {"query": "x", "top_k": 51},
     {"query": "x", "min_similarity": 1.5}, {"query": "x", "source": "other"}, {"query": "x" * 501}],
)
def test_search_skills_validation_422(client, payload):
    assert client.post("/api/v1/semantic-search/skills", json=payload).status_code == 422


def test_search_job_requirements_with_empty_db(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.semantic_search.semantic_search.crud.search_job_requirements_vector",
        lambda db, vec, top_k, min_similarity: [],
    )
    r = client.post("/api/v1/semantic-search/job-requirements", json={"query": "backend"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["total_results"] == 0 and data["model_name"] == "fake-minilm"


def test_search_job_requirements_validation_422(client):
    assert client.post("/api/v1/semantic-search/job-requirements", json={"query": "x" * 1001}).status_code == 422


# ── skill gap by ids ────────────────────────────────────────────────────────
def _skill_gap_repos(monkeypatch, profile=True, jd=True):
    monkeypatch.setattr("app.api.v1.routers.router.skill_gap.profile_repo.get_profile_by_id",
                        lambda db, pid: object() if profile else None)
    monkeypatch.setattr("app.api.v1.routers.router.skill_gap.jd_repo.get_jd_by_id",
                        lambda db, jid: [object()] if jd else [])
    monkeypatch.setattr("app.services.skill_features.skill_gap_analysis.profile_skill_repo.get_skills_by_profile_id",
                        lambda db, pid: [SimpleNamespace(SkillTitle="Python", Vector=None),
                                         SimpleNamespace(SkillTitle="Docker", Vector=None)])
    monkeypatch.setattr("app.services.skill_features.skill_gap_analysis.jd_skill_repo.get_jd_skills",
                        lambda db, jid: [SimpleNamespace(Title="python", Vector=None),
                                         SimpleNamespace(Title="Kubernetes", Vector=None)])


def test_skill_gap_by_ids_ok(client, monkeypatch):
    _skill_gap_repos(monkeypatch)
    r = client.get("/api/v1/skill-gap/profile/1/jd/2")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["summary"]["total_required_skills"] == 2
    assert data["matched_skills"][0]["skill_name"].lower() == "python"
    assert [m["skill_name"] for m in data["missing_skills"]] == ["Kubernetes"]


def test_skill_gap_unknown_profile_404(client, monkeypatch):
    _skill_gap_repos(monkeypatch, profile=False)
    assert client.get("/api/v1/skill-gap/profile/1/jd/2").status_code == 404


def test_skill_gap_unknown_jd_404(client, monkeypatch):
    _skill_gap_repos(monkeypatch, jd=False)
    assert client.get("/api/v1/skill-gap/profile/1/jd/2").status_code == 404


def test_skill_gap_non_numeric_id_422(client):
    assert client.get("/api/v1/skill-gap/profile/abc/jd/1").status_code == 422


def test_skill_gap_missing_required_side_400(client):
    r = client.post("/api/v1/skill-gap/analyze", json={"candidate_skills": ["python"]})
    assert r.status_code == 400


def test_skill_gap_threshold_bounds_422(client):
    base = {"candidate_skills": ["python"], "required_skills": ["python"]}
    assert client.post("/api/v1/skill-gap/analyze", json={**base, "match_threshold": 0.4}).status_code == 422
    assert client.post("/api/v1/skill-gap/analyze", json={**base, "partial_threshold": 0.95}).status_code == 422


def test_skill_gap_exact_and_semantic_results(client):
    payload = {"candidate_skills": ["Python", "FastAPI", "MySQL"],
               "required_skills": ["python", "PostgreSQL", "Docker"]}
    data = client.post("/api/v1/skill-gap/analyze", json=payload).json()["data"]
    assert data["matched_skills"][0]["is_exact_match"] is True
    assert [p["skill_name"] for p in data["partially_matched_skills"]] == ["PostgreSQL"]
    assert [m["skill_name"] for m in data["missing_skills"]] == ["Docker"]


def test_skill_gap_empty_required_list_returns_400(client):
    r = client.post("/api/v1/skill-gap/analyze", json={"candidate_skills": ["python"], "required_skills": []})
    # required_skills rỗng bị coi như không truyền -> 400
    assert r.status_code == 400


# ── match-similarity ────────────────────────────────────────────────────────
MATCH_RESULT = {
    "profile_id": 1, "jd_id": 2, "is_suitable": True, "fit_level": "HIGHLY_SUITABLE",
    "match_score": 0.8, "verdict": "ok", "matched_skills": ["python"],
    "transferable_skills": [], "missing_skills": [], "bonus_skills": [],
    "semantic_similarity": 0.5, "graph_synced": False,
}


def test_match_health(client):
    assert client.get("/api/v1/graph/").status_code == 200


def test_match_similarity_ok(client, monkeypatch):
    monkeypatch.setattr("app.api.v1.routers.router.skill_match.calculate_cv_jd_matching",
                        lambda db, profile_id, jd_id: MATCH_RESULT)
    r = client.get("/api/v1/graph/match-similarity", params={"profile_id": 1, "jd_id": 2})
    assert r.status_code == 200
    assert r.json()["data"]["fit_level"] == "HIGHLY_SUITABLE"


@pytest.mark.parametrize("message,status", [("Profile with id 1 not found", 404),
                                            ("Profile with id 1 has no valid text content", 400)])
def test_match_similarity_value_errors(client, monkeypatch, message, status):
    def boom(db, profile_id, jd_id):
        raise ValueError(message)

    monkeypatch.setattr("app.api.v1.routers.router.skill_match.calculate_cv_jd_matching", boom)
    assert client.get("/api/v1/graph/match-similarity", params={"profile_id": 1, "jd_id": 2}).status_code == status


@pytest.mark.parametrize("params", [{}, {"profile_id": 1}, {"profile_id": 0, "jd_id": 1},
                                    {"profile_id": 1, "jd_id": 0}, {"profile_id": "a", "jd_id": 1}])
def test_match_similarity_validation_422(client, params):
    assert client.get("/api/v1/graph/match-similarity", params=params).status_code == 422


def test_match_similarity_real_service_not_found(client, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    r = client.get("/api/v1/graph/match-similarity", params={"profile_id": 1, "jd_id": 2})
    assert r.status_code == 404
