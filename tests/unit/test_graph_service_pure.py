from datetime import date
from types import SimpleNamespace

import pytest

from app.services.graph import graph_service as gs

pytestmark = pytest.mark.unit


def test_compute_cosine_similarity_basic_and_clamped():
    assert gs.compute_cosine_similarity([1, 0], [1, 0]) == 1.0
    assert gs.compute_cosine_similarity([1, 0], [0, 1]) == 0.0
    assert gs.compute_cosine_similarity([1, 0], [-1, 0]) == 0.0  # negatives clamp to 0
    assert gs.compute_cosine_similarity([1, 1], [1, 0]) == pytest.approx(0.7071, abs=1e-4)


@pytest.mark.parametrize("a, b", [(None, [1]), ([1], None), ([], [1]), ([1, 2], [1]), ([0, 0], [1, 1])])
def test_compute_cosine_similarity_degenerate_inputs_return_zero(a, b):
    assert gs.compute_cosine_similarity(a, b) == 0.0


@pytest.mark.parametrize(
    "title, expected",
    [
        ("Senior Software Engineer", ("Backend Development", "Software & Backend Engineering")),
        ("DevOps Engineer II", ("Cloud & DevOps Engineering", "CI/CD & Cloud Infrastructure")),
        ("  BACKEND developer ", ("Backend Development", "Backend Web Engineering")),
        ("Barista", ("Information Technology", "General IT")),
        (None, ("Information Technology", "General IT")),
        ("", ("Information Technology", "General IT")),
    ],
)
def test_get_domain_expertise_for_title(title, expected):
    assert gs.get_domain_expertise_for_title(title) == expected


def test_mean_vector():
    assert gs._mean_vector([[1.0, 3.0], [3.0, 5.0]]) == [2.0, 4.0]
    assert gs._mean_vector([[1.0, 2.0], None]) == [1.0, 2.0]
    assert gs._mean_vector([]) is None
    assert gs._mean_vector([None]) is None


def _exp(start, end):
    return SimpleNamespace(StartDate=start, EndDate=end)


def test_experience_years_merges_overlaps_and_handles_ongoing():
    today = date(2024, 1, 1)
    experiences = [
        _exp(date(2020, 1, 1), date(2021, 1, 1)),
        _exp(date(2020, 7, 1), date(2021, 7, 1)),  # overlaps the first job
        _exp(date(2023, 1, 1), None),  # ongoing until `today`
    ]
    expected_days = (date(2021, 7, 1) - date(2020, 1, 1)).days + (today - date(2023, 1, 1)).days
    assert gs._experience_years(experiences, today) == pytest.approx(expected_days / 365.25)


def test_experience_years_ignores_future_and_invalid_ranges():
    today = date(2024, 1, 1)
    experiences = [
        _exp(date(2025, 1, 1), None),  # starts in the future
        _exp(date(2022, 1, 1), date(2021, 1, 1)),  # end before start
        _exp(None, date(2022, 1, 1)),  # no start date
    ]
    assert gs._experience_years(experiences, today) == 0
    assert gs._experience_years([], today) == 0


def test_skill_payload_is_deterministic_and_case_insensitive():
    a = gs._skill_payload("Python")
    b = gs._skill_payload("  python ")
    assert a["skillId"] == b["skillId"]
    assert a["skillName"] == "Python"
    assert a["skillId"] != gs._skill_payload("Java")["skillId"]
    assert 0 < a["skillId"] < 2**56
