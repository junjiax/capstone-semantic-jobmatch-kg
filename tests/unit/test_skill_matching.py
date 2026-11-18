from unittest.mock import MagicMock

import numpy as np
import pytest
from sqlalchemy.orm import Session

from app.models.jd import JD
from app.models.profile import Profile
from app.services.skill_features import skill_matching as sm
from tests.factories import make_jd, make_profile

pytestmark = pytest.mark.unit


# ── compute_cosine_similarity ────────────────────────────────────────────────


def test_cosine_identical_orthogonal_opposite():
    assert sm.compute_cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)
    assert sm.compute_cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)
    assert sm.compute_cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1.0)
    assert sm.compute_cosine_similarity(np.array([2.0, 2.0]), [1, 1]) == pytest.approx(1.0)


@pytest.mark.parametrize(
    "a, b, message",
    [
        ([1, 2], [1, 2, 3], "dimensions"),
        ([float("nan"), 1], [1, 1], "NaN"),
        ([float("inf"), 1], [1, 1], "Inf"),
        ([0, 0], [1, 1], "zero"),
    ],
)
def test_cosine_rejects_invalid_vectors(a, b, message):
    with pytest.raises(ValueError, match=message):
        sm.compute_cosine_similarity(a, b)


# ── _find_cluster_for_skill ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    "skill, cluster",
    [
        ("MySQL", "rdbms"),
        ("  PostgreSQL ", "rdbms"),
        ("FastAPI", "python_web"),
        ("Kubernetes", "containers"),
        ("AWS", "cloud"),
        ("Spring Boot", "java_frameworks"),
        ("React", "frontend_frameworks"),
    ],
)
def test_find_cluster_for_known_skills(skill, cluster):
    assert sm._find_cluster_for_skill(skill)[0] == cluster


def test_find_cluster_returns_none_for_unknown_skill():
    assert sm._find_cluster_for_skill("Photoshop") is None


# ── evaluate_smart_skill_matching ────────────────────────────────────────────


def test_evaluate_direct_transferable_missing_and_bonus():
    profile = make_profile(skills=["python", "MySQL", "Kubernetes", "Figma"])
    jd = make_jd(skills=["Python", "PostgreSQL", "Docker", "AWS"])

    result = sm.evaluate_smart_skill_matching(profile, jd)

    assert result["total_required_skills"] == 4
    assert result["matched_core_skills"] == ["Python"]
    assert result["matched_tool_skills"] == []
    assert {(t["required_skill"], t["candidate_skill"]) for t in result["transferable_skills"]} == {
        ("PostgreSQL", "MySQL"),
        ("Docker", "Kubernetes"),
    }
    assert result["missing_skills"] == ["AWS"]
    assert result["bonus_skills"] == ["Figma"]
    # (1.0 core + 2 * 0.75 transferable) / 4 required
    assert result["base_skill_ratio"] == pytest.approx(0.625)


def test_evaluate_transferable_candidate_skill_is_consumed_once():
    profile = make_profile(skills=["MySQL"])
    jd = make_jd(skills=["PostgreSQL", "Oracle"])
    result = sm.evaluate_smart_skill_matching(profile, jd)
    assert len(result["transferable_skills"]) == 1
    assert len(result["missing_skills"]) == 1


def test_evaluate_extracts_skills_from_text_when_jd_has_no_skill_rows():
    profile = make_profile(skills=["Python"])
    jd = make_jd(skills=[], CleanText="We need Python and Docker experience")
    result = sm.evaluate_smart_skill_matching(profile, jd)
    assert result["total_required_skills"] == 2
    assert result["matched_core_skills"] == ["Python"]
    assert "Docker" in result["missing_skills"]


def test_evaluate_with_no_requirements_has_zero_ratio():
    result = sm.evaluate_smart_skill_matching(make_profile(skills=["Python"]), make_jd(skills=[]))
    # the JD title alone ("Backend Engineer") contains no dictionary skill
    assert result["total_required_skills"] == 0
    assert result["base_skill_ratio"] == 0.0
    assert result["bonus_skills"] == ["Python"]


# ── calculate_cv_jd_matching ─────────────────────────────────────────────────


def _db_returning(profile, jd) -> MagicMock:
    db = MagicMock(spec=Session)

    def query(model):
        q = MagicMock()
        q.filter.return_value.first.return_value = profile if model is Profile else jd
        return q

    db.query.side_effect = query
    return db


@pytest.fixture
def graph_calls(monkeypatch):
    calls = {
        "cv": MagicMock(),
        "job": MagicMock(),
        "save": MagicMock(),
    }
    monkeypatch.setattr(sm, "sync_cv_to_graph", calls["cv"])
    monkeypatch.setattr(sm, "sync_job_to_graph", calls["job"])
    monkeypatch.setattr(sm, "save_cv_jd_match_result_graph", calls["save"])
    return calls


def test_core_skill_floor_gives_at_least_075(graph_calls):
    # Python matched (core), Docker transferable, AWS missing: missing(1) <= matched_core(1)
    profile = make_profile(skills=["Python", "Kubernetes"])
    jd = make_jd(skills=["Python", "Docker", "AWS"])
    result = sm.calculate_cv_jd_matching(_db_returning(profile, jd), 1, 1)

    assert result["match_score"] >= 0.75
    assert result["fit_level"] == "HIGHLY_SUITABLE"
    assert result["is_suitable"] is True
    assert result["graph_synced"] is True
    graph_calls["save"].assert_called_once()
    assert graph_calls["save"].call_args.kwargs["scores"]["totalResult"] == result["match_score"]


def test_floor_not_applied_when_more_missing_than_core_matches(graph_calls):
    profile = make_profile(skills=["Python"])
    jd = make_jd(skills=["Python", "Docker", "AWS", "Kafka"])
    result = sm.calculate_cv_jd_matching(_db_returning(profile, jd), 1, 1)
    assert result["match_score"] < 0.40
    assert result["fit_level"] == "LOW_SUITABLE"
    assert result["is_suitable"] is False


def test_moderate_band_between_040_and_070(graph_calls):
    profile = make_profile(skills=["Git"])
    jd = make_jd(skills=["Git", "Linux"])  # one tool skill matched of two: 0.5 * 0.8 = 0.40
    result = sm.calculate_cv_jd_matching(_db_returning(profile, jd), 1, 1)
    assert 0.40 <= result["match_score"] < 0.70
    assert result["fit_level"] == "MODERATE_SUITABLE"
    assert result["is_suitable"] is True


def test_neo4j_failure_sets_graph_synced_false_without_raising(graph_calls):
    graph_calls["cv"].side_effect = RuntimeError("neo4j down")
    profile = make_profile(skills=["Python"])
    jd = make_jd(skills=["Python"])
    result = sm.calculate_cv_jd_matching(_db_returning(profile, jd), 1, 1)
    assert result["graph_synced"] is False
    assert result["match_score"] > 0


def test_missing_profile_or_jd_raises_not_found(graph_calls):
    with pytest.raises(ValueError, match="Profile with id 1 not found"):
        sm.calculate_cv_jd_matching(_db_returning(None, make_jd()), 1, 2)
    with pytest.raises(ValueError, match="JD with id 2 not found"):
        sm.calculate_cv_jd_matching(_db_returning(make_profile(), None), 1, 2)


def test_profile_without_text_raises(graph_calls):
    profile = make_profile(clean_text=None, raw_text=None)
    with pytest.raises(ValueError, match="no valid text"):
        sm.calculate_cv_jd_matching(_db_returning(profile, make_jd()), 1, 2)


def test_jd_model_type_sanity():
    # guards the `model is Profile` dispatch used by _db_returning
    assert Profile is not JD
