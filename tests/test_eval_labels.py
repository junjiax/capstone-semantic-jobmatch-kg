"""Validate the labeled evaluation set in data/eval against the real corpus.

No model and no services are needed.
"""
import copy

import pytest

from scripts.eval import data_loading as dl
from scripts.eval.validate_labels import validate


@pytest.fixture(scope="module")
def real():
    return {
        "pairs": dl.load_pairs(),
        "skills": dl.load_skills_gold(),
        "gaps": dl.load_gap_gold(),
        "cvs": dl.load_cvs(),
        "jds": dl.load_jds(),
    }


def _validate(d):
    return validate(d["pairs"], d["skills"], d["gaps"], d["cvs"], d["jds"])


def test_real_labels_are_valid(real):
    assert _validate(real) == []


def test_label_set_shape(real):
    assert len(real["pairs"]) == 40
    assert len({p["jd_id"] for p in real["pairs"]}) == 8
    assert {p["relevance"] for p in real["pairs"]} == {0, 1, 2}
    assert {p["jd_lang"] for p in real["pairs"]} == {"en", "vi"}


def test_labels_are_never_claimed_human_verified(real):
    assert all(p["annotator"] == "ai-agent" and p["human_verified"] is False for p in real["pairs"])
    assert all(s["annotator"] == "ai-agent" and s["human_verified"] is False for s in real["skills"])
    assert all(g["annotator"] == "ai-agent" and g["human_verified"] is False for g in real["gaps"])


@pytest.mark.parametrize(
    "mutate,expected",
    [
        (lambda d: d["pairs"].pop(), "expected 40 pairs"),
        (lambda d: d["pairs"][0].update(relevance=3), "relevance must be 0, 1 or 2"),
        (lambda d: d["pairs"][0].update(cv_id="does-not-exist"), "unknown cv_id"),
        (lambda d: d["pairs"][0].update(annotator="human"), "annotator must be 'ai-agent'"),
        (lambda d: d["pairs"][0].update(human_verified="yes"), "human_verified must be boolean"),
        (lambda d: d["skills"][0].update(text_sha1="0" * 40), "text_sha1 mismatch"),
        (lambda d: d["skills"][0]["skills"].append("Python"), "lowercase"),
        (lambda d: d["gaps"][0]["missing"].append(d["gaps"][0]["matched"][0]), "overlap"),
        (lambda d: d["gaps"][0]["missing"].pop(), "must equal the JD gold skills"),
    ],
)
def test_validator_detects_errors(real, mutate, expected):
    d = copy.deepcopy(real)
    mutate(d)
    errors = _validate(d)
    assert any(expected in e for e in errors), errors


def test_validator_requires_positive_and_negative_per_jd(real):
    d = copy.deepcopy(real)
    jd = d["pairs"][0]["jd_id"]
    for p in d["pairs"]:
        if p["jd_id"] == jd:
            p["relevance"] = 0
    assert any("no CV with relevance >= 1" in e for e in _validate(d))
