"""Plain helper functions that build ORM objects for tests."""

from typing import Iterable, Optional

from app.models.enum import UserRole
from app.models.jd import JD
from app.models.jd_skill import JDSkill
from app.models.profile import Profile
from app.models.profile_skill import ProfileSkill
from app.models.user import User


def make_user(
    email: str = "user@example.com",
    full_name: str = "Test User",
    role: UserRole = UserRole.CANDIDATE,
    hashed_password: str = "hashed",
    is_active: bool = True,
    is_verified: bool = True,
    id: Optional[int] = None,
) -> User:
    user = User(
        Email=email,
        FullName=full_name,
        HashedPassword=hashed_password,
        Role=role,
        IsActive=is_active,
        IsVerified=is_verified,
    )
    if id is not None:
        user.Id = id
    return user


def make_profile(
    user_id: int = 1,
    skills: Iterable[str] = (),
    clean_text: Optional[str] = "Backend developer",
    raw_text: Optional[str] = None,
    title: str = "CV",
) -> Profile:
    return Profile(
        UserId=user_id,
        Title=title,
        CleanText=clean_text,
        RawText=raw_text,
        skills=[ProfileSkill(SkillTitle=s) for s in skills],
    )


def make_jd(
    title: str = "Backend Engineer",
    skills: Iterable[str] = (),
    **fields,
) -> JD:
    return JD(Title=title, skills=[JDSkill(Title=s) for s in skills], **fields)
