from types import SimpleNamespace

import pytest

from app.services.semantic_search.text_embedding import (
    build_job_text,
    build_requirement_text,
    build_skill_text,
    compute_content_hash,
    normalize_text,
    text_hash,
)

pytestmark = pytest.mark.unit


def test_normalize_text_collapses_whitespace_and_handles_none():
    assert normalize_text("  a \n\t b   c ") == "a b c"
    assert normalize_text(None) == ""
    assert normalize_text("") == ""


def test_build_skill_text_with_and_without_category():
    assert build_skill_text("  FastAPI ") == "FastAPI"
    assert build_skill_text("FastAPI", " Backend   Framework ") == "FastAPI - Backend Framework"


def test_build_job_text_skips_empty_fields_and_joins_with_pipe():
    job = SimpleNamespace(
        Title="Backend Engineer",
        Domain="Software",
        Expertise=None,
        Qualification="BSc",
        Responsibility="Build  APIs",
    )
    assert build_job_text(job) == "Backend Engineer | Software | BSc | Build APIs"


def test_build_job_text_tolerates_missing_attributes():
    assert build_job_text(SimpleNamespace(Title="Only title")) == "Only title"
    assert build_job_text(SimpleNamespace()) == ""


def test_build_requirement_text_order_and_normalization():
    job = SimpleNamespace(Responsibility="Do  X", Qualification="Know Y", Expertise="Z")
    # normalize_text flattens the newline separator into a single space
    assert build_requirement_text(job) == "Do X Know Y Z"
    assert build_requirement_text(SimpleNamespace()) == ""


def test_content_hash_is_sha256_hex_and_depends_on_model_and_text():
    h = compute_content_hash("hello", "m1")
    assert len(h) == 64 and int(h, 16) >= 0
    assert h == compute_content_hash("hello", "m1")
    assert h != compute_content_hash("hello", "m2")
    assert h != compute_content_hash("hello!", "m1")


def test_text_hash_matches_compute_content_hash():
    assert text_hash("abc", "model") == compute_content_hash("abc", "model")
