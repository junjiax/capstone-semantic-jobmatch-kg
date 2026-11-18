"""Ràng buộc, quan hệ và cascade của các model trên PostgreSQL thật."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.enum import UserRole
from app.models.jd import JD
from app.models.jd_skill import JDSkill
from app.models.profile import Profile
from app.models.profile_skill import ProfileSkill
from app.models.user import User
from tests.factories import make_jd, make_profile, make_user

pytestmark = pytest.mark.integration


def test_user_defaults(db_session):
    user = User(Email="d@example.com", FullName="D", HashedPassword="h")
    db_session.add(user)
    db_session.flush()
    db_session.refresh(user)
    assert user.Id is not None
    assert user.Role == UserRole.CANDIDATE
    assert user.IsActive is True and user.IsVerified is False
    assert user.CreatedAt is not None


def test_user_email_unique(db_session):
    db_session.add(make_user(email="dup@example.com"))
    db_session.flush()
    db_session.add(make_user(email="dup@example.com"))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_profile_requires_existing_user(db_session):
    db_session.add(make_profile(user_id=999999))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_profile_skills_relationship_and_cascade_from_jd(db_session, seed_user):
    profile = make_profile(user_id=seed_user.Id, skills=["python", "docker"])
    jd = make_jd(skills=["sql", "git"])
    db_session.add_all([profile, jd])
    db_session.flush()
    assert {s.SkillTitle for s in profile.skills} == {"python", "docker"}
    jd_id = jd.Id
    db_session.delete(jd)
    db_session.flush()
    assert db_session.query(JDSkill).filter(JDSkill.JDId == jd_id).count() == 0


def test_jd_title_not_null(db_session):
    db_session.add(JD(Title=None))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_vector_column_round_trip_384_dims(db_session, seed_user, fake_embedder):
    profile = make_profile(user_id=seed_user.Id)
    db_session.add(profile)
    db_session.flush()
    vec = fake_embedder.encode("python")
    db_session.add(ProfileSkill(ProfileId=profile.Id, SkillTitle="python", Vector=vec))
    db_session.flush()
    db_session.expire_all()
    stored = db_session.query(ProfileSkill).one().Vector
    assert len(stored) == 384
    assert stored[0] == pytest.approx(1.0)


def test_vector_wrong_dimension_rejected(db_session, seed_user):
    from sqlalchemy.exc import DBAPIError, StatementError

    profile = make_profile(user_id=seed_user.Id)
    db_session.add(profile)
    db_session.flush()
    db_session.add(ProfileSkill(ProfileId=profile.Id, SkillTitle="x", Vector=[0.1, 0.2]))
    with pytest.raises((DBAPIError, StatementError, ValueError)):
        db_session.flush()
