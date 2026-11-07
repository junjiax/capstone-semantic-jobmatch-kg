import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Sequence, cast

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.enum import EducationLevel, ProfileFileType
from app.models.profile import Profile
from app.models.profile_edu import ProfileEdu
from app.models.profile_skill import ProfileSkill
from app.models.profile_work_exp import ProfileWorkExp
from app.models.enum import (
    EducationLevel,
    ProfileFileType,
    JobStatus,
    UserStatus,
    UserRole,
    CVFileType,
)
from app.repositories.postgres.profile import sync_list_of_profiles
from app.repositories.postgres.profile_edu import sync_profile_edu
from app.repositories.postgres.profile_skill import sync_profile_skills
from app.repositories.postgres.profile_work_exp import sync_profile_work_exp

"""
    DEFINE URL FOR LIST OF OBJECT PROFILES FILE READING
"""

FILE_INPUT_URL = "app/dataset/CVs/ready/processed-2026-11-06-17-55-00.txt"

"""
    NORMALIZE OBJECT PROFILE
"""


def _coerce_int(value: Any, default: int = 1) -> int:
    if value is None or value == "":
        return default
    return int(value)


def _normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, str):
        return value.strip() or None
    raise ValueError(f"Expected text or null, got {type(value).__name__}")


def _normalize_string_list(value: Any, field_name: str) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of strings")

    result: List[str] = []
    for item in cast(List[Any], value):
        if not isinstance(item, str):
            raise ValueError(f"{field_name} must contain only strings")
        item = item.strip()
        if item:
            result.append(item)
    return result


"""
    PARSE DATA TYPE FROM PROFILE OBJECT TO PROFILE ENTITY
"""


def _parse_profile_record(record: str | Dict[str, Any] | Any) -> Profile:
    if isinstance(record, str):
        try:
            payload: Dict[Any, Any] = json.loads(record)
        except json.JSONDecodeError as exc:
            raise ValueError("Each profile record must be valid JSON") from exc
    else:
        payload = record

    data: Dict[Any, Any] = payload

    user_id = _coerce_int(data.get("UserId", data.get("user_id", 1)))
    file_url = _normalize_optional_text(data.get("file_url", data.get("FileUrl")))
    title = _normalize_optional_text(data.get("title", data.get("Title")))
    raw_text = _normalize_optional_text(data.get("rawtext", data.get("RawText")))
    clean_text = _normalize_optional_text(data.get("cleantext", data.get("CleanText")))

    file_type_raw = str(data.get("file_type", data.get("FileType", "pdf"))).lower()
    try:
        file_type = ProfileFileType(file_type_raw)
    except ValueError as exc:
        raise ValueError(f"Unsupported profile file type: {file_type_raw}") from exc

    profile = Profile(
        UserId=user_id,
        FileUrl=file_url,
        FileType=file_type,
        Title=title,
        RawText=raw_text,
        CleanText=clean_text,
    )

    skill_titles = _normalize_string_list(
        data.get("skilltitle", data.get("SkillTitle", data.get("skills", []))),
        "skilltitle",
    )
    if skill_titles:
        profile.skills = [
            ProfileSkill(SkillTitle=skill_title) for skill_title in skill_titles
        ]

    degree = _normalize_optional_text(data.get("degree", data.get("Degree")))
    major = _normalize_optional_text(data.get("major", data.get("Major")))
    school = _normalize_optional_text(data.get("school", data.get("School")))
    level_value = _normalize_optional_text(data.get("level", data.get("Level")))
    graduation_year = data.get("graduation_year", data.get("GraduationYear"))
    gpa = data.get("GPA", data.get("gpa"))

    if (
        degree
        or major
        or school
        or level_value
        or graduation_year is not None
        or gpa is not None
    ):
        if graduation_year is not None:
            graduation_year = int(graduation_year)
        if gpa is not None:
            gpa = Decimal(str(gpa))

        level = None
        if level_value:
            try:
                if level_value:
                    level = EducationLevel(EducationLevel.BACHELOR)
            except ValueError as exc:
                raise ValueError(f"Unsupported education level: {level_value}") from exc

        profile.educations = [
            ProfileEdu(
                Degree=degree,
                Major=major,
                School=school,
                Level=level,
                GraduationYear=graduation_year,
                GPA=gpa,
            )
        ]

    domain = _normalize_string_list(
        data.get("domain", data.get("Domain", [])), "domain"
    )
    expertise = _normalize_string_list(
        data.get("expertise", data.get("Expertise", [])),
        "expertise",
    )
    responsibility = _normalize_optional_text(
        data.get("responsibility", data.get("Responsibility"))
    )
    start_date_value = data.get("start_date", data.get("StartDate"))
    end_date_value = data.get("end_date", data.get("EndDate"))

    if (
        domain
        or expertise
        or responsibility
        or start_date_value is not None
        or end_date_value is not None
    ):
        start_date = (
            date.fromisoformat(start_date_value)
            if isinstance(start_date_value, str) and start_date_value
            else None
        )
        end_date = (
            date.fromisoformat(end_date_value)
            if isinstance(end_date_value, str) and end_date_value
            else None
        )

        profile.work_experiences = [
            ProfileWorkExp(
                Domain=domain[0] if domain else None,
                Expertise=expertise[0] if expertise else None,
                Responsibility=responsibility,
                StartDate=start_date,
                EndDate=end_date,
            )
        ]

    return profile


"""
    SYNC LIST OF PROFILES
"""


def save_list_of_profiles_to_postgresql(
    db: Session, list_of_profiles: Sequence[str | Dict[str, Any]]
) -> Dict[str, int]:
    profiles = [_parse_profile_record(record) for record in list_of_profiles]
    if not profiles:
        return {"inserted_count": 0}

    profile_data: Any = [
        {
            "UserId": profile.UserId,
            "FileUrl": profile.FileUrl,
            "FileType": profile.FileType,
            "Title": profile.Title,
            "RawText": profile.RawText,
            "CleanText": profile.CleanText,
            "skills": profile.skills,
            "educations": profile.educations,
            "work_experiences": profile.work_experiences,
        }
        for profile in profiles
    ]
    saved_profiles = sync_list_of_profiles(db, profile_data)

    for profile in saved_profiles:
        for skill in profile.skills or []:
            sync_profile_skills(
                db,
                ProfileId=profile.Id,
                SkillTitle=skill.SkillTitle,
            )

        for education in profile.educations or []:
            sync_profile_edu(
                db,
                ProfileId=profile.Id,
                Degree=education.Degree,
                Major=education.Major,
                School=education.School,
                Level=education.Level,
                GraduationYear=education.GraduationYear,
                GPA=education.GPA,
            )

        for work_exp in profile.work_experiences or []:
            sync_profile_work_exp(
                db,
                ProfileId=profile.Id,
                Domain=work_exp.Domain,
                Expertise=work_exp.Expertise,
                Responsibility=work_exp.Responsibility,
                StartDate=work_exp.StartDate,
                EndDate=work_exp.EndDate,
            )

    return {"inserted_count": len(saved_profiles)}


"""
    GET LIST OF PROFILES
"""


def get_list_of_profiles_by_reading_file() -> List[Dict[str, Any]]:
    project_root = Path(__file__).resolve().parents[3]
    input_path = project_root / FILE_INPUT_URL

    if not input_path.exists():
        raise FileNotFoundError(f"Profile input file not found: {input_path}")

    with input_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        raise ValueError("Profile input file must contain a JSON list")

    return cast(List[Dict[str, Any]], payload)


def main(db: Session) -> Dict[str, int]:
    """
    READ FILE
    """
    profiles: List[Dict[str, Any]] = get_list_of_profiles_by_reading_file()

    """
    SAVE PROFILE TO DATABASE
    """

    result: Dict[str, int] = save_list_of_profiles_to_postgresql(db, profiles)
    print(f"[INFO] Inserted {result['inserted_count']} profiles successfully")
    return result


if __name__ == "__main__":
    with SessionLocal() as db:
        main(db)
    # result = get_list_of_profiles()
    # print(result)
