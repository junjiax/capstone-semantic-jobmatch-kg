import errno
import json
from pathlib import Path
from typing import Any, Dict, IO, List

import pytest

from app.data.JDs.transformation import main as transformation
from app.data.JDs.transformation.main import clean_extract


def test_clean_extract_returns_only_original_phrases_and_assigns_sections():
    raw_jd: Dict[str, object] = {
        "job_title": "Kỹ sư Phần mềm",
        "job_skills": ["Python", "SQL"],
        "requirements": (
            "Kinh nghiệm với Python và SQL.\n"
            "Tốt nghiệp ngành Công nghệ thông tin."
        ),
        "responsibilities": "Xây dựng hệ thống phân tán.",
    }

    result = clean_extract({"jd_rawtext": raw_jd})

    assert result["Title"] == "Kỹ sư Phần mềm"
    assert result["JobSkills"] == ["Python", "SQL"]
    qualification = result["Qualification"]
    responsibilities = result["Responsibilities"]
    clean_text = result["Cleantext"]
    assert isinstance(qualification, str)
    assert isinstance(responsibilities, str)
    assert isinstance(clean_text, str)
    assert "Python" in qualification
    assert "Công nghệ thông tin" in qualification
    assert "Xây dựng hệ thống phân tán" in responsibilities
    assert "Python" in clean_text
    assert "Xây dựng hệ thống phân tán" in clean_text

    source_sections: List[str] = [
        "Kỹ sư Phần mềm",
        "Kinh nghiệm với Python và SQL.\nTốt nghiệp ngành Công nghệ thông tin.",
        "Xây dựng hệ thống phân tán.",
        "Python",
        "SQL",
    ]
    raw_text = " ".join(source_sections)
    for phrase in (
        "Kỹ sư Phần mềm",
        "Python",
        "SQL",
        "Công nghệ thông tin",
        "Xây dựng hệ thống phân tán",
    ):
        assert phrase in raw_text
        assert phrase in clean_text


def test_clean_extract_does_not_infer_domain_or_experience():
    raw_jd: Dict[str, object] = {
        "job_title": "Nhân viên văn phòng",
        "job_skills": [],
        "requirements": "Tốt nghiệp Đại học.",
        "responsibilities": "Tiếp nhận hồ sơ.",
    }

    result = clean_extract({"jd_rawtext": raw_jd})

    domain = result["Domain"]
    assert isinstance(domain, str)
    assert domain == ""
    assert result["Experience"] == 0
    assert result["Responsibilities"] == ""


def test_write_cleaned_jds_falls_back_when_output_is_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    output_dir = tmp_path / "readonly"
    fallback_dir = tmp_path / "fallback"
    original_open = transformation.Path.open

    def open_path(
        path: Path,
        mode: str = "r",
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> IO[Any]:
        if path == output_dir / "processed-test.txt":
            raise OSError(errno.EROFS, "Read-only file system")
        return original_open(path, mode, buffering, encoding, errors, newline)

    monkeypatch.setattr(transformation.Path, "open", open_path)
    monkeypatch.setattr(transformation.tempfile, "gettempdir", lambda: str(fallback_dir))

    output_path = transformation.write_cleaned_jds(
        output_dir, [{"Title": "Backend Engineer"}], "test"
    )

    assert output_path == (
        fallback_dir
        / "capstone-semantic-jobmatch-kg"
        / "processed-jds"
        / "processed-test.txt"
    )
    assert json.loads(output_path.read_text(encoding="utf-8")) == {
        "Title": "Backend Engineer"
    }
