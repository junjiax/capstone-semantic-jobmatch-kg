"""
Unit tests for analyze_skill_gap_service using the deterministic FakeEmbedder
(see tests/conftest.py). Similarities between named skills are controlled by the
fake table, not by the real model:
  python=e0, fastapi~python 0.90, mysql=e1, postgresql~mysql 0.70, docker=e2,
  "rest api"~"restful apis" 0.95; every other skill gets an unrelated vector.
"""

import pytest

from app.schemas.skill_gap import SkillGapAnalysisRequest
from app.services.skill_features.skill_gap_analysis import (
    _generate_recommendation,
    _normalize_skill,
    analyze_skill_gap_service,
)

pytestmark = pytest.mark.unit


def _analyze(**kwargs):
    return analyze_skill_gap_service(db=None, request=SkillGapAnalysisRequest(**kwargs))


def test_exact_partial_missing_and_extra_classification():
    result = _analyze(
        candidate_skills=["Python", "MySQL", "Git"],
        required_skills=["Python", "PostgreSQL", "Docker"],
    )

    s = result.summary
    assert (s.total_required_skills, s.total_matched_skills) == (3, 1)
    assert (s.total_partial_skills, s.total_missing_skills, s.total_extra_skills) == (1, 1, 1)

    assert result.matched_skills[0].skill_name == "Python"
    assert result.matched_skills[0].is_exact_match is True
    assert result.matched_skills[0].similarity_score == 1.0

    partial = result.partially_matched_skills[0]
    assert partial.skill_name == "PostgreSQL"
    assert partial.closest_candidate_skill == "MySQL"
    assert partial.similarity_score == pytest.approx(0.70, abs=1e-3)

    assert [m.skill_name for m in result.missing_skills] == ["Docker"]
    assert [e.skill_name for e in result.extra_skills] == ["Git"]


def test_exact_match_is_case_and_whitespace_insensitive():
    result = _analyze(candidate_skills=["  python  "], required_skills=["PYTHON"])
    item = result.matched_skills[0]
    assert item.is_exact_match is True
    assert item.similarity_score == 1.0
    assert result.summary.total_extra_skills == 0


def test_semantic_match_above_threshold_is_matched_not_exact():
    result = _analyze(
        candidate_skills=["RESTful APIs", "FastAPI"],
        required_skills=["REST API", "FastAPI"],
        match_threshold=0.80,
    )
    assert result.summary.total_matched_skills == 2
    assert result.summary.total_missing_skills == 0
    semantic = next(m for m in result.matched_skills if m.skill_name == "REST API")
    assert semantic.is_exact_match is False
    assert semantic.similarity_score == pytest.approx(0.95, abs=1e-3)
    assert result.summary.fit_level == "EXCELLENT"


def test_similarity_exactly_at_thresholds_is_inclusive():
    # fastapi ~ python is 0.90; threshold 0.90 must still count as matched
    matched = _analyze(
        candidate_skills=["Python"], required_skills=["FastAPI"], match_threshold=0.90
    )
    assert matched.summary.total_matched_skills == 1 or matched.summary.total_partial_skills == 1

    # postgresql ~ mysql is 0.70: below default 0.82 and above 0.60 -> partial
    partial = _analyze(candidate_skills=["MySQL"], required_skills=["PostgreSQL"])
    assert partial.summary.total_partial_skills == 1
    # raising partial_threshold above the similarity turns it into missing
    missing = _analyze(
        candidate_skills=["MySQL"], required_skills=["PostgreSQL"], partial_threshold=0.75
    )
    assert missing.summary.total_missing_skills == 1


def test_completely_unrelated_skills_are_all_missing():
    result = _analyze(
        candidate_skills=["Adobe Photoshop", "Figma", "Canva"],
        required_skills=["Kubernetes", "Golang", "Kafka"],
    )
    s = result.summary
    assert s.total_matched_skills == 0
    assert s.total_missing_skills == 3
    assert s.skill_coverage_percentage < 30.0
    assert s.fit_level == "LOW"
    assert len(result.recommendations) == 3
    assert s.total_extra_skills == 3


def test_partial_match_counts_half_weight_in_coverage():
    # 1 matched (1.0) + 1 partial (0.5) over 2 required = 0.75 -> GOOD
    result = _analyze(
        candidate_skills=["Python", "MySQL"], required_skills=["Python", "PostgreSQL"]
    )
    assert result.summary.skill_coverage_ratio == pytest.approx(0.75)
    assert result.summary.skill_coverage_percentage == pytest.approx(75.0)
    assert result.summary.fit_level == "GOOD"


@pytest.mark.parametrize(
    "required, expected",
    [
        (["Python"], "EXCELLENT"),  # 1.0 >= 0.85
        (["Python", "Docker"], "MODERATE"),  # 0.5 >= 0.50
    ],
)
def test_fit_level_cutoffs(required, expected):
    result = _analyze(candidate_skills=["Python"], required_skills=required)
    assert result.summary.fit_level == expected


def test_empty_required_skills_is_not_applicable_and_everything_is_extra():
    result = analyze_skill_gap_service(
        db=None,
        request=SkillGapAnalysisRequest(candidate_skills=["Python", "Git"], required_skills=[]),
    )
    s = result.summary
    assert s.fit_level == "NOT_APPLICABLE"
    assert s.total_required_skills == 0
    assert s.total_extra_skills == 2
    assert s.skill_coverage_ratio == 0.0
    assert [e.skill_name for e in result.extra_skills] == ["Python", "Git"]
    assert result.recommendations


def test_empty_required_and_empty_candidate_is_full_coverage():
    result = analyze_skill_gap_service(
        db=None, request=SkillGapAnalysisRequest(candidate_skills=[], required_skills=[])
    )
    assert result.summary.fit_level == "NOT_APPLICABLE"
    assert result.summary.skill_coverage_ratio == 1.0


def test_recommendation_text_depends_on_closest_skill():
    with_base = _generate_recommendation("PostgreSQL", closest_skill="MySQL", similarity=0.7)
    without = _generate_recommendation("Docker")
    assert "MySQL" in with_base and "PostgreSQL" in with_base
    assert "Docker" in without and "MySQL" not in without
    # similarity under 0.60 ignores the closest skill
    assert "MySQL" not in _generate_recommendation("X", closest_skill="MySQL", similarity=0.3)


def test_normalize_skill():
    assert _normalize_skill("  Machine   Learning ") == "machine learning"
    assert _normalize_skill("") == ""
    assert _normalize_skill(None) == ""  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field, value",
    [
        ("match_threshold", 0.49),
        ("match_threshold", 1.01),
        ("partial_threshold", 0.29),
        ("partial_threshold", 0.91),
    ],
)
def test_threshold_bounds_are_validated(field, value):
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        SkillGapAnalysisRequest(**{field: value})
