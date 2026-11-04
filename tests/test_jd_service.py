import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.jd import JD
from app.models.jd_skill import JDSkill
from app.services import jd as jd_service
from app.services.jd import save_list_of_jds_to_postgresql


def _jd_record() -> str:
    return json.dumps(
        {
            "RawText": {"jd_rawtext": "raw description"},
            "Cleantext": "clean description",
            "Title": "Backend Engineer",
            "JobSkills": ["Python", " PostgreSQL ", ""],
            "Domain": "Software",
            "Expertise": "Backend",
            "Responsibilities": "Build APIs",
            "Qualification": "3 years experience",
            "Experience": 3,
        }
    )


def test_save_list_of_jds_persists_jobs_and_skills():
    db = Mock(spec=Session)

    result = save_list_of_jds_to_postgresql(db, [_jd_record()])

    assert result == {"inserted_count": 1}
    db.add_all.assert_called_once()
    db.commit.assert_called_once_with()
    db.rollback.assert_not_called()

    saved_jd = db.add_all.call_args.args[0][0]
    assert isinstance(saved_jd, JD)
    assert saved_jd.Title == "Backend Engineer"
    assert saved_jd.RawText is not None
    assert json.loads(saved_jd.RawText) == {"jd_rawtext": "raw description"}
    assert [skill.Title for skill in saved_jd.skills] == ["Python", "PostgreSQL"]
    assert all(isinstance(skill, JDSkill) for skill in saved_jd.skills)


def test_save_list_of_jds_rejects_invalid_record_before_database_write():
    db = Mock(spec=Session)

    with pytest.raises(ValueError, match="valid JSON"):
        save_list_of_jds_to_postgresql(db, ["not json"])

    db.add_all.assert_not_called()
    db.commit.assert_not_called()


def test_save_list_of_jds_rolls_back_when_commit_fails():
    db = Mock(spec=Session)
    db.commit.side_effect = SQLAlchemyError("database unavailable")

    with pytest.raises(SQLAlchemyError, match="database unavailable"):
        save_list_of_jds_to_postgresql(db, [_jd_record()])

    db.rollback.assert_called_once_with()


def test_save_empty_jd_list_does_not_open_transaction():
    db = Mock(spec=Session)

    assert save_list_of_jds_to_postgresql(db, []) == {"inserted_count": 0}
    db.add_all.assert_not_called()
    db.commit.assert_not_called()


def test_main_reads_the_output_file_returned_by_transformation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    output_path = tmp_path / "processed-output.txt"
    output_path.write_text(_jd_record() + "\n", encoding="utf-8")
    saved_records: list[str] = []
    db = Mock(spec=Session)

    def fake_save(db_arg: Session, records: list[str]) -> dict[str, int]:
        assert db_arg is db
        saved_records.extend(records)
        return {"inserted_count": len(records)}

    monkeypatch.setattr(
        jd_service,
        "transformation_main",
        lambda: {"output_path": str(output_path)},
    )
    monkeypatch.setattr(jd_service, "save_list_of_jds_to_postgresql", fake_save)

    result = jd_service.main(db)

    assert result == {"inserted_count": 1}
    assert saved_records == [_jd_record()]
