import json
from pathlib import Path
from typing import Dict, List, cast

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.jd import JD
from app.models.jd_skill import JDSkill
from app.dataset.JDs.transformation.main import main as transformation_main


def main(db: Session) -> Dict[str, int]:
    transformation_result = transformation_main()

    print("[INFO] Read cleaned data from file...")
    output_path = transformation_result.get("output_path")
    if not isinstance(output_path, str):
        raise RuntimeError("JD transformation did not return its output file path")
    input_path = Path(output_path)
    with input_path.open("r", encoding="utf-8") as file:
        list_of_jds: List[str] = [line.strip() for line in file if line.strip()]

    print("[INFO] Starting sync data to database...")
    result = save_list_of_jds_to_postgresql(db, list_of_jds)

    print(f"[INFO] Inserted {result['inserted_count']} JDs successfully")
    return result


def _parse_jd_record(record: str) -> JD:
    try:
        parsed: object = json.loads(record)
    except json.JSONDecodeError as exc:
        raise ValueError("Each JD record must be valid JSON") from exc

    if not isinstance(parsed, dict):
        raise ValueError("Each JD record must be a JSON object")

    data = cast(Dict[str, object], parsed)

    title = data.get("Title")

    if not isinstance(title, str) or not title.strip():
        raise ValueError("Each JD record must have a non-empty job_title")

    def optional_text(field: str) -> str | None:
        value = data.get(field)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"JD {field} must be a string or null")
        return value

    raw_text = data.get("RawText")
    if isinstance(raw_text, (dict, list)):
        raw_text = json.dumps(raw_text, ensure_ascii=False)
    elif raw_text is not None and not isinstance(raw_text, str):
        raise ValueError("JD rawtext must be a string, object, array, or null")

    raw_skills = data.get("JobSkills", [])
    if not isinstance(raw_skills, list):
        raise ValueError("JD Job_skills must be a list of strings")

    raw_skill_items = cast(List[object], raw_skills)
    skills: List[str] = []
    for raw_skill in raw_skill_items:
        if not isinstance(raw_skill, str):
            raise ValueError("JD Job_skills must be a list of strings")
        if raw_skill.strip():
            skills.append(raw_skill.strip())

    experience = data.get("Experience")
    if experience is not None and (
        isinstance(experience, bool) or not isinstance(experience, int)
    ):
        raise ValueError("JD Experience must be an integer or null")

    return JD(
        RawText=raw_text,
        CleanText=optional_text("Cleantext"),
        Title=title.strip(),
        Domain=optional_text("Domain"),
        Expertise=optional_text("Expertise"),
        Qualification=optional_text("Qualification"),
        Responsibility=optional_text("Responsibilities"),
        Experience=experience,
        skills=[JDSkill(Title=skill) for skill in skills],
    )


def save_list_of_jds_to_postgresql(
    db: Session, list_of_jds: List[str]
) -> Dict[str, int]:
    jds = [_parse_jd_record(record) for record in list_of_jds]
    if not jds:
        return {"inserted_count": 0}

    try:
        db.add_all(jds)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise

    return {"inserted_count": len(jds)}


if __name__ == "__main__":
    with SessionLocal() as db:
        main(db)
