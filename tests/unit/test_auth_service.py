from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core import security
from app.models.enum import UserRole
from app.schemas.user import PasswordChange, UserRegister, UserUpdate
from app.services.auth import auth as svc
from tests.factories import make_user

pytestmark = pytest.mark.unit


@pytest.fixture
def db():
    return MagicMock(spec=Session)


@pytest.fixture
def persist(monkeypatch):
    """Replace the UserPersist repository module used by the auth service."""
    fake = MagicMock()
    monkeypatch.setattr(svc, "UserPersist", fake)
    return fake


def _register_payload(**kw):
    data = dict(
        email="a@example.com",
        full_name="Nguyen Van A",
        password="password123",
        confirm_password="password123",
    )
    data.update(kw)
    return UserRegister(**data)


# ── register ────────────────────────────────────────────────────────────────


def test_register_creates_candidate_with_hashed_password(db, persist):
    persist.get_user_by_email.return_value = None
    svc.register_user(db, _register_payload())

    kwargs = persist.create_user.call_args.kwargs
    assert kwargs["Email"] == "a@example.com"
    assert kwargs["Role"] == UserRole.CANDIDATE
    assert kwargs["HashedPassword"] != "password123"
    assert security.verify_password("password123", kwargs["HashedPassword"])


def test_register_duplicate_email_is_409(db, persist):
    persist.get_user_by_email.return_value = make_user()
    with pytest.raises(HTTPException) as exc:
        svc.register_user(db, _register_payload())
    assert exc.value.status_code == 409
    persist.create_user.assert_not_called()


@pytest.mark.xfail(
    reason="App bug: register_user ignores UserRegister.is_verified (default True), so new "
    "users get IsVerified=False and cannot use /auth/refresh",
    strict=False,
)
def test_register_passes_is_verified_from_schema(db, persist):
    persist.get_user_by_email.return_value = None
    svc.register_user(db, _register_payload())
    assert persist.create_user.call_args.kwargs.get("IsVerified") is True

# ── login ───────────────────────────────────────────────────────────────────


def _user_with_password(password="password123", **kw):
    user = make_user(hashed_password=security.hash_password(password), id=7, **kw)
    return user


def test_login_success_returns_usable_tokens(db, persist):
    persist.get_user_by_email.return_value = _user_with_password()
    tokens = svc.login_user(db, "user@example.com", "password123")

    access = security.verify_token(tokens.access_token)
    assert access["sub"] == "7" and access["role"] == "candidate"
    assert security.decode_token(tokens.refresh_token, "refresh")["sub"] == "7"
    assert tokens.token_type == "bearer"


@pytest.mark.parametrize("user_exists", [True, False])
def test_login_wrong_credentials_is_401(db, persist, user_exists):
    persist.get_user_by_email.return_value = _user_with_password() if user_exists else None
    with pytest.raises(HTTPException) as exc:
        svc.login_user(db, "user@example.com", "wrong-password")
    assert exc.value.status_code == 401


def test_login_inactive_user_is_403(db, persist):
    persist.get_user_by_email.return_value = _user_with_password(is_active=False)
    with pytest.raises(HTTPException) as exc:
        svc.login_user(db, "user@example.com", "password123")
    assert exc.value.status_code == 403


# ── refresh ─────────────────────────────────────────────────────────────────


def test_refresh_success(db, persist):
    persist.get_user_by_id.return_value = _user_with_password()
    tokens = svc.refresh_user_tokens(db, security.create_refresh_token(7))
    assert security.verify_token(tokens.access_token)["sub"] == "7"


def test_refresh_rejects_access_token_and_garbage(db, persist):
    for bad in (security.create_access_token(7, "a@b.com", "candidate"), "garbage"):
        with pytest.raises(HTTPException) as exc:
            svc.refresh_user_tokens(db, bad)
        assert exc.value.status_code == 401


@pytest.mark.parametrize(
    "user",
    [None, make_user(id=7, is_active=False), make_user(id=7, is_verified=False)],
)
def test_refresh_rejects_missing_inactive_or_unverified_user(db, persist, user):
    persist.get_user_by_id.return_value = user
    with pytest.raises(HTTPException) as exc:
        svc.refresh_user_tokens(db, security.create_refresh_token(7))
    assert exc.value.status_code == 401


# ── profile helpers ─────────────────────────────────────────────────────────


def test_get_user_not_found_is_404(db, persist):
    persist.get_user_by_id.return_value = None
    with pytest.raises(HTTPException) as exc:
        svc.get_user(db, 99)
    assert exc.value.status_code == 404


def test_update_profile_maps_schema_fields_to_model_columns(db, persist):
    user = make_user()
    svc.update_profile(db, user, UserUpdate(full_name="New Name"))
    persist.update_user.assert_called_once_with(db, user, FullName="New Name")


def test_list_users_computes_offset_and_role_value(db, persist):
    svc.list_users(db, page=3, page_size=10, role=UserRole.ADMIN, is_active=True)
    persist.get_users.assert_called_once_with(
        db=db, skip=20, limit=10, role="admin", is_active=True
    )


# ── passwords ───────────────────────────────────────────────────────────────


def test_change_password_wrong_current_is_400(db, persist):
    user = _user_with_password()
    data = PasswordChange(
        current_password="nope", new_password="newpass123", confirm_new_password="newpass123"
    )
    with pytest.raises(HTTPException) as exc:
        svc.change_password(db, user, data)
    assert exc.value.status_code == 400
    persist.save_user.assert_not_called()


def test_change_password_updates_hash(db, persist):
    user = _user_with_password()
    data = PasswordChange(
        current_password="password123", new_password="newpass123", confirm_new_password="newpass123"
    )
    svc.change_password(db, user, data)
    assert security.verify_password("newpass123", user.HashedPassword)
    persist.save_user.assert_called_once_with(db, user)


async def test_forgot_password_unknown_email_is_silent(db, persist):
    persist.get_user_by_email.return_value = None
    assert await svc.forgot_password(db, "ghost@example.com") is None
    persist.save_user.assert_not_called()


async def test_forgot_password_stores_reset_token_with_expiry(db, persist):
    user = make_user()
    persist.get_user_by_email.return_value = user
    await svc.forgot_password(db, user.Email)
    assert security.decode_token(user.ResetToken, "reset")["sub"] == user.Email
    assert user.ResetTokenExpires > datetime.now(timezone.utc)
    persist.save_user.assert_called_once_with(db, user)


def _reset_user(expires_in=timedelta(minutes=10)):
    user = make_user(hashed_password="old")
    user.ResetToken = security.create_reset_token(user.Email)
    user.ResetTokenExpires = datetime.now(timezone.utc) + expires_in
    return user


def test_reset_password_success_clears_token(db, persist):
    user = _reset_user()
    persist.get_user_by_reset_token.return_value = user
    svc.reset_password(db, user.ResetToken, "brandnew123")
    assert security.verify_password("brandnew123", user.HashedPassword)
    assert user.ResetToken is None and user.ResetTokenExpires is None


def test_reset_password_expired_is_400(db, persist):
    user = _reset_user(expires_in=timedelta(minutes=-1))
    persist.get_user_by_reset_token.return_value = user
    with pytest.raises(HTTPException) as exc:
        svc.reset_password(db, user.ResetToken, "brandnew123")
    assert exc.value.status_code == 400
    assert "hết hạn" in exc.value.detail


def test_reset_password_rejects_wrong_token_type_and_unknown_token(db, persist):
    access = security.create_access_token(1, "a@b.com", "candidate")
    with pytest.raises(HTTPException) as exc:
        svc.reset_password(db, access, "brandnew123")
    assert exc.value.status_code == 400

    persist.get_user_by_reset_token.return_value = None
    with pytest.raises(HTTPException) as exc:
        svc.reset_password(db, security.create_reset_token("a@b.com"), "brandnew123")
    assert exc.value.status_code == 400


@pytest.mark.parametrize("password", ["short", "x" * 129])
def test_reset_password_validates_length(db, persist, password):
    with pytest.raises(HTTPException) as exc:
        svc.reset_password(db, "any", password)
    assert exc.value.status_code == 400
