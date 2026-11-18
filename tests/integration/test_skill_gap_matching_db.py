"""Skill gap và CV-JD matching dùng dữ liệu từ PostgreSQL thật (Neo4j được patch)."""
from unittest.mock import MagicMock

import pytest

from app.schemas.skill_gap import SkillGapAnalysisRequest
from app.services.skill_features import skill_matching
from app.services.skill_features.skill_gap_analysis import analyze_skill_gap_service
from tests.factories import make_jd, make_profile

pytestmark = pytest.mark.integration

MATCHING = "app.services.skill_features.skill_matching"


@pytest.fixture
def cv_and_jd(db_session, seed_user):
    profile = make_profile(
        user_id=seed_user.Id, skills=["Python", "FastAPI", "MySQL", "Git"],
        clean_text="backend developer python fastapi mysql",
    )
    jd = make_jd(title="Backend Engineer", skills=["Python", "PostgreSQL", "Docker"], CleanText="python backend")
    db_session.add_all([profile, jd])
    db_session.flush()
    return profile, jd


@pytest.fixture
def graph_ok(monkeypatch):
    mocks = {n: MagicMock() for n in ("sync_cv_to_graph", "sync_job_to_graph", "save_cv_jd_match_result_graph")}
    for name, mock in mocks.items():
        monkeypatch.setattr(f"{MATCHING}.{name}", mock)
    return mocks


def test_skill_gap_by_ids_from_db(db_session, cv_and_jd):
    profile, jd = cv_and_jd
    result = analyze_skill_gap_service(db_session, SkillGapAnalysisRequest(profile_id=profile.Id, jd_id=jd.Id))
    assert result.summary.total_required_skills == 3
    assert [m.skill_name for m in result.matched_skills] == ["Python"]
    assert [p.skill_name for p in result.partially_matched_skills] == ["PostgreSQL"]
    assert [m.skill_name for m in result.missing_skills] == ["Docker"]


def test_skill_gap_endpoint_by_ids_over_db(db_client, cv_and_jd):
    profile, jd = cv_and_jd
    r = db_client.get(f"/api/v1/skill-gap/profile/{profile.Id}/jd/{jd.Id}")
    assert r.status_code == 200
    assert r.json()["data"]["summary"]["total_required_skills"] == 3


def test_skill_gap_endpoint_unknown_ids_404(db_client, db_session):
    assert db_client.get("/api/v1/skill-gap/profile/999999/jd/999999").status_code == 404


def test_matching_computes_score_and_syncs_graph(db_session, cv_and_jd, graph_ok):
    profile, jd = cv_and_jd
    out = skill_matching.calculate_cv_jd_matching(db_session, profile.Id, jd.Id)
    assert out["profile_id"] == profile.Id and out["jd_id"] == jd.Id
    assert 0.0 <= out["match_score"] <= 1.0
    assert "Python" in [s for s in out["matched_skills"]] or "python" in [s.lower() for s in out["matched_skills"]]
    assert out["fit_level"] in {"HIGHLY_SUITABLE", "MODERATE_SUITABLE", "LOW_SUITABLE"}
    assert out["graph_synced"] is True
    graph_ok["save_cv_jd_match_result_graph"].assert_called_once()


def test_matching_graph_failure_sets_flag_without_raising(db_session, cv_and_jd, graph_ok):
    profile, jd = cv_and_jd
    graph_ok["sync_cv_to_graph"].side_effect = RuntimeError("neo4j down")
    out = skill_matching.calculate_cv_jd_matching(db_session, profile.Id, jd.Id)
    assert out["graph_synced"] is False


def test_matching_unknown_ids_raise_not_found(db_session, cv_and_jd, graph_ok):
    profile, jd = cv_and_jd
    with pytest.raises(ValueError, match="not found"):
        skill_matching.calculate_cv_jd_matching(db_session, 999999, jd.Id)
    with pytest.raises(ValueError, match="not found"):
        skill_matching.calculate_cv_jd_matching(db_session, profile.Id, 999999)


def test_match_similarity_endpoint_over_db(db_client, cv_and_jd, graph_ok):
    profile, jd = cv_and_jd
    r = db_client.get("/api/v1/graph/match-similarity", params={"profile_id": profile.Id, "jd_id": jd.Id})
    assert r.status_code == 200
    assert r.json()["data"]["jd_id"] == jd.Id


def test_match_similarity_endpoint_not_found_over_db(db_client, db_session, graph_ok):
    r = db_client.get("/api/v1/graph/match-similarity", params={"profile_id": 999999, "jd_id": 999999})
    assert r.status_code == 404
