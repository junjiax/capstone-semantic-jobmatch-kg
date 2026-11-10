import logging
import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.enum import ProfileFileType
from app.models.profile import Profile
from app.models.profile_skill import ProfileSkill
from app.models.user import User, UserRole
from app.services.graph import graph_service
from app.utils.file_handling import (
    check_file_extension,
    extract_text_from_pdf,
    generate_unique_filename,
    save_file_to_disk,
)

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_ROOT = Path("uploads") / "profiles"
ALLOWED_EXTENSIONS = ["pdf", "docx", "txt"]
KNOWN_SKILLS = (
    "python", "java", "javascript", "typescript", "react", "next.js", "node.js",
    "fastapi", "django", "spring", "sql", "postgresql", "mysql", "mongodb",
    "docker", "kubernetes", "git", "graphql", "rest api", "machine learning",
    "pytorch", "tensorflow", "aws", "azure", "gcp", "ci/cd", "neo4j",
)


class ProfileUpdateRequest(BaseModel):
    title: str | None = None
    skills: list[str] | None = None


def _extract_text(file_path: Path, extension: str) -> str:
    if extension == "pdf":
        return extract_text_from_pdf(str(file_path))
    if extension == "docx":
        from docx import Document

        document = Document(str(file_path))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    return file_path.read_text(encoding="utf-8", errors="ignore")


def _extract_contact(text: str, fallback_name: str, user: User) -> tuple[str, str, str]:
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone_match = re.search(r"(?<!\d)(?:\+84|0)[\d .-]{8,12}\d", text)
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    name = first_line[:255] if first_line and "@" not in first_line else fallback_name
    return name or user.FullName, email_match.group(0) if email_match else user.Email, phone_match.group(0) if phone_match else (user.Phone or "")


def _extract_skills(text: str) -> list[str]:
    lowered = text.lower()
    return [skill for skill in KNOWN_SKILLS if skill in lowered]


def _profile_list_item(profile: Profile) -> dict:
    return {
        "id": profile.Id,
        "userId": profile.UserId,
        "title": profile.Title,
        "fileUrl": profile.FileUrl,
        "createdAt": profile.CreatedAt,
        "skills": [skill.SkillTitle for skill in profile.skills],
    }


@router.get("/mine")
def list_my_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    profiles = (
        db.query(Profile)
        .filter(Profile.UserId == current_user.Id)
        .order_by(Profile.CreatedAt.desc())
        .all()
    )
    return {"success": True, "data": [_profile_list_item(profile) for profile in profiles]}


@router.get("/available")
def list_available_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return selectable CVs for the current role.

    Candidates are restricted to their own CVs. Admins need the full candidate
    pool for matching and graph inspection.
    """
    query = db.query(Profile)
    if current_user.Role != UserRole.ADMIN:
        query = query.filter(Profile.UserId == current_user.Id)
    profiles = query.order_by(Profile.CreatedAt.desc(), Profile.Id.desc()).all()
    return {"success": True, "data": [_profile_list_item(profile) for profile in profiles]}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_profile(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    original_name = file.filename or ""
    extension = Path(original_name).suffix.lower().lstrip(".")
    if not check_file_extension(original_name, ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file PDF, DOCX hoặc TXT.")

    filename = generate_unique_filename(current_user.Id, original_name)
    file_path = Path(save_file_to_disk(file, str(UPLOAD_ROOT), filename))
    try:
        raw_text = _extract_text(file_path, extension)
        if not raw_text.strip():
            raise HTTPException(status_code=422, detail="Không đọc được nội dung CV. File có thể là bản scan.")

        name, _, _ = _extract_contact(raw_text, Path(original_name).stem, current_user)
        skills = _extract_skills(raw_text)
        profile = Profile(
            UserId=current_user.Id,
            FileUrl=str(file_path),
            FileType=ProfileFileType.PDF if extension == "pdf" else ProfileFileType.OTHER,
            Title=name,
            RawText=raw_text,
            CleanText=" ".join(raw_text.split()),
        )
        db.add(profile)
        db.flush()
        db.add_all([ProfileSkill(ProfileId=profile.Id, SkillTitle=skill) for skill in skills])
        db.commit()
        db.refresh(profile)

        try:
            graph_service.sync_cv_to_graph(db, profile.Id)
        except Exception:
            logger.exception("CV %s saved to PostgreSQL but graph sync failed", profile.Id)

        return {
            "success": True,
            "message": "Bóc tách CV thành công",
            "data": {
                "id": profile.Id,
                "fullName": name,
                "email": _extract_contact(raw_text, Path(original_name).stem, current_user)[1],
                "phone": _extract_contact(raw_text, Path(original_name).stem, current_user)[2],
                "domain": "Information Technology",
                "expertise": "General IT",
                "experienceYears": 0,
                "educationLevel": "Chưa xác định",
                "skills": skills,
            },
        }
    except HTTPException:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        db.rollback()
        file_path.unlink(missing_ok=True)
        logger.exception("CV upload failed")
        raise HTTPException(status_code=422, detail=f"Không thể xử lý CV: {exc}") from exc


@router.patch("/{profile_id}")
def update_profile_review(
    profile_id: int,
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    profile = (
        db.query(Profile)
        .filter(Profile.Id == profile_id, Profile.UserId == current_user.Id)
        .first()
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="CV không tồn tại hoặc bạn không có quyền truy cập.")
    if payload.title is not None:
        profile.Title = payload.title.strip() or profile.Title
    if payload.skills is not None:
        unique_skills = list(dict.fromkeys(skill.strip() for skill in payload.skills if skill.strip()))
        profile.skills.clear()
        profile.skills.extend(ProfileSkill(ProfileId=profile.Id, SkillTitle=skill) for skill in unique_skills)
    db.commit()
    try:
        graph_service.sync_cv_to_graph(db, profile.Id)
    except Exception:
        logger.exception("CV %s updated in PostgreSQL but graph sync failed", profile.Id)
    return {"success": True, "message": "Đã cập nhật hồ sơ", "data": {"id": profile.Id}}
