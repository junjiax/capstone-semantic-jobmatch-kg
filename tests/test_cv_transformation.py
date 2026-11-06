import json
from datetime import date
from pathlib import Path

import pytest

from app.data.CVs.transformation.main import (
    chunk_text,
    parse_profiles,
    transform_file,
)


def test_chunk_text_normalizes_and_limits_chunks():
    chunks = chunk_text(
        "  Python   developer\x00. " + "x" * 410,
        max_chunk_length=100,
    )

    assert chunks[0] == "Python developer."
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_parse_profiles_removes_non_text_characters_and_keeps_unicode():
    raw_text = (
        "===== profile.pdf =====\n"
        "Nguyễn Văn A\x00\n"
        "✓ Python  and café.\n"
    )

    assert parse_profiles(raw_text) == [
        {"filename": "profile.pdf", "text": "Nguyễn Văn A\nPython and café."}
    ]


def test_parse_profiles_requires_content_and_headers():
    with pytest.raises(ValueError, match="text before the first"):
        parse_profiles("No profile data")

    with pytest.raises(ValueError, match="No PDF profile headers"):
        parse_profiles("")

    with pytest.raises(ValueError, match="No text found"):
        parse_profiles("===== empty.pdf =====\n")


def test_transform_file_writes_a_json_array(tmp_path: Path):
    source_file = tmp_path / "crawled.txt"
    output_dir = tmp_path / "saving"
    source_file.write_text(
        "===== first.pdf =====\n"
        "Jane Doe\n"
        "Software Engineer\n"
        "Skills: Python, SQL\n"
        "EDUCATION\n"
        "Degree: Bachelor of Science\n"
        "Major: Computer Science\n"
        "School: Example University\n"
        "Graduation Year: 2020\n"
        "GPA: 3.8\n"
        "WORK EXPERIENCE\n"
        "04/2021 - Present\n"
        "Responsibilities: Build reliable services\n"
        "Domain: FinTech\n"
        "Expertise: APIs, Cloud\n",
        encoding="utf-8",
    )

    profiles = transform_file(source_file, output_dir, "test")
    output_path = output_dir / "processed-test.txt"
    expected_profile = {
        "rawtext": (
            "Jane Doe\n"
            "Software Engineer\n"
            "Skills: Python, SQL\n"
            "EDUCATION\n"
            "Degree: Bachelor of Science\n"
            "Major: Computer Science\n"
            "School: Example University\n"
            "Graduation Year: 2020\n"
            "GPA: 3.8\n"
            "WORK EXPERIENCE\n"
            "04/2021 - Present\n"
            "Responsibilities: Build reliable services\n"
            "Domain: FinTech\n"
            "Expertise: APIs, Cloud"
        ),
        "cleantext": (
            "Jane Doe\n"
            "Software Engineer\n"
            "Skills: Python, SQL\n"
            "EDUCATION\n"
            "Degree: Bachelor of Science\n"
            "Major: Computer Science\n"
            "School: Example University\n"
            "Graduation Year: 2020\n"
            "GPA: 3.8\n"
            "WORK EXPERIENCE\n"
            "04/2021 - Present\n"
            "Responsibilities: Build reliable services\n"
            "Domain: FinTech\n"
            "Expertise: APIs, Cloud"
        ),
        "file_url": "app/data/CVs/uploads/raw-resumes/first.pdf",
        "file_type": "pdf",
        "title": "Software Engineer",
        "skilltitle": ["Python", "SQL"],
        "degree": "Bachelor of Science",
        "major": "Computer Science",
        "school": "Example University",
        "level": "bachelor",
        "graduation_year": 2020,
        "GPA": 3.8,
        "domain": ["FinTech"],
        "expertise": ["APIs", "Cloud"],
        "responsibility": "Build reliable services",
        "start_date": date(2021, 4, 1),
        "end_date": None,
    }

    assert profiles == [expected_profile]
    saved_profiles = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved_profiles == [
        {**expected_profile, "start_date": "2021-04-01"}
    ]


def test_transform_extracts_field_phrases_from_normalized_chunks(tmp_path: Path):
    source_file = tmp_path / "crawled.txt"
    source_file.write_text(
        "===== profile.pdf =====\n"
        "Jane Doe\n"
        "Data Engineer\n"
        "SKILLS\n"
        "Python, SQL, Data Pipelines\n"
        "EDUCATION\n"
        "Bachelor of Science\n"
        "Major: Computer Science\n"
        "Example University\n"
        "EXPERIENCE\n"
        "04/2021 - 03/2024\n"
        "Expertise: Cloud Architecture, Distributed Systems\n"
        "Responsibilities\n"
        "Design scalable data platforms and services.\n"
        "DOMAINS\n"
        "Healthcare, FinTech\n",
        encoding="utf-8",
    )

    profile = transform_file(source_file, tmp_path / "saving", "phrases")[0]

    assert profile["cleantext"].startswith("Jane Doe\nData Engineer\nSKILLS")
    assert profile["skilltitle"] == ["Python", "SQL", "Data Pipelines"]
    assert profile["degree"] == "Bachelor of Science"
    assert profile["major"] == "Computer Science"
    assert profile["school"] == "Example University"
    assert profile["expertise"] == ["Cloud Architecture", "Distributed Systems"]
    assert profile["domain"] == ["Healthcare", "FinTech"]
    assert profile["responsibility"] == (
        "Design scalable data platforms and services."
    )
