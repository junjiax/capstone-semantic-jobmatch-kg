"""Endpoint tests for /api/v1/auth và /api/v1/user (DB giả)."""
import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
    hash_password,
)
from app.models.enum import UserRole
from tests.api.conftest import make_api_user

pytestmark = pytest.mark.api

REGISTER = {
    "email": "new@example.com",
    "full_name": "New User",
    "password": "password123",
    "confirm_password": "password123",
}


@pytest.fixture
def repo(monkeypatch):
    """Patch UserPersist trong service auth bằng dict in-memory."""
    users: dict = {}

    def get_by_email(db, email):
        return users.get(email)

    def create_user(db, **kw):
        user = make_api_user(
            email=kw["Email"], full_name=kw["FullName"], hashed_password=kw["HashedPassword"],
            role=kw["Role"], is_verified=False, id=len(users) + 1,
        )
        users[user.Email] = user
        return user

    monkeypatch.setattr("app.services.auth.auth.UserPersist.get_user_by_email", get_by_email)
    monkeypatch.setattr("app.services.auth.auth.UserPersist.create_user", create_user)
    monkeypatch.setattr("app.services.auth.auth.UserPersist.save_user", lambda db, u: u)
    monkeypatch.setattr(
        "app.services.auth.auth.UserPersist.get_user_by_id",
        lambda db, uid: next((u for u in users.values() if u.Id == uid), None),
    )
    monkeypatch.setattr(
        "app.services.auth.auth.UserPersist.get_user_by_reset_token",
        lambda db, token: next((u for u in users.values() if u.ResetToken == token), None),
    )
    return users


@pytest.fixture(autouse=True)
def _db(override_db, mock_db):
    override_db(mock_db)


def test_register_success(client, repo):
    r = client.post("/api/v1/auth/register", json=REGISTER)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "new@example.com"
    assert body["role"] == UserRole.CANDIDATE.value
    assert "HashedPassword" not in body and "password" not in body


def test_register_duplicate_email_409(client, repo):
    assert client.post("/api/v1/auth/register", json=REGISTER).status_code == 201
    assert client.post("/api/v1/auth/register", json=REGISTER).status_code == 409


@pytest.mark.parametrize(
    "patch",
    [
        {"confirm_password": "different123"},
        {"password": "short", "confirm_password": "short"},
        {"email": "not-an-email"},
        {"full_name": "A"},
    ],
)
def test_register_validation_422(client, repo, patch):
    assert client.post("/api/v1/auth/register", json={**REGISTER, **patch}).status_code == 422


def test_login_success_returns_token_pair(client, repo):
    repo["a@example.com"] = make_api_user(
        email="a@example.com", hashed_password=hash_password("password123"), id=7
    )
    r = client.post("/api/v1/auth/login", data={"username": "a@example.com", "password": "password123"})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]


def test_login_wrong_password_401(client, repo):
    repo["a@example.com"] = make_api_user(email="a@example.com", hashed_password=hash_password("password123"))
    r = client.post("/api/v1/auth/login", data={"username": "a@example.com", "password": "wrong-pass"})
    assert r.status_code == 401


def test_login_unknown_user_401(client, repo):
    r = client.post("/api/v1/auth/login", data={"username": "ghost@example.com", "password": "password123"})
    assert r.status_code == 401


def test_login_inactive_user_403(client, repo):
    repo["a@example.com"] = make_api_user(
        email="a@example.com", hashed_password=hash_password("password123"), is_active=False
    )
    r = client.post("/api/v1/auth/login", data={"username": "a@example.com", "password": "password123"})
    assert r.status_code == 403


def test_login_missing_form_fields_422(client, repo):
    assert client.post("/api/v1/auth/login", data={}).status_code == 422


def test_refresh_with_valid_refresh_token(client, repo):
    repo["a@example.com"] = make_api_user(email="a@example.com", id=3, is_verified=True)
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": create_refresh_token(3)})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_refresh_rejects_access_token_401(client, repo):
    repo["a@example.com"] = make_api_user(email="a@example.com", id=3, is_verified=True)
    token = create_access_token(3, "a@example.com", "candidate")
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": token}).status_code == 401


def test_refresh_rejects_garbage_401(client, repo):
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": "nope"}).status_code == 401


def test_refresh_after_register_is_rejected_because_not_verified(client, repo):
    """Hành vi hiện tại (lỗi ứng dụng): register_user không set IsVerified nên refresh trả 401."""
    client.post("/api/v1/auth/register", json=REGISTER)
    user = repo["new@example.com"]
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": create_refresh_token(user.Id)})
    assert r.status_code == 401


def test_forgot_password_always_200(client, repo):
    assert client.post("/api/v1/auth/forgot-password", json={"email": "ghost@example.com"}).status_code == 200


def test_forgot_password_invalid_email_422(client, repo):
    assert client.post("/api/v1/auth/forgot-password", json={"email": "bad"}).status_code == 422


def test_reset_password_flow(client, repo):
    user = make_api_user(email="a@example.com", hashed_password=hash_password("oldpassword1"))
    repo["a@example.com"] = user
    assert client.post("/api/v1/auth/forgot-password", json={"email": "a@example.com"}).status_code == 200
    assert user.ResetToken
    body = {"token": user.ResetToken, "new_password": "newpassword1", "confirm_new_password": "newpassword1"}
    assert client.post("/api/v1/auth/reset-password", json=body).status_code == 200
    assert user.ResetToken is None


def test_reset_password_rejects_wrong_token_type_400(client, repo):
    token = create_access_token(1, "a@example.com", "candidate")
    body = {"token": token, "new_password": "newpassword1", "confirm_new_password": "newpassword1"}
    assert client.post("/api/v1/auth/reset-password", json=body).status_code == 400


def test_reset_password_unknown_token_400(client, repo):
    body = {"token": create_reset_token("a@example.com"), "new_password": "newpassword1",
            "confirm_new_password": "newpassword1"}
    assert client.post("/api/v1/auth/reset-password", json=body).status_code == 400


def test_reset_password_mismatch_422(client, repo):
    body = {"token": "t", "new_password": "newpassword1", "confirm_new_password": "other-pass-1"}
    assert client.post("/api/v1/auth/reset-password", json=body).status_code == 422


# ── logout + /user ───────────────────────────────────────────────────────────
def test_logout_requires_token_401(client):
    assert client.post("/api/v1/auth/logout").status_code == 401


def test_logout_ok(client, login_as):
    assert client.post("/api/v1/auth/logout", headers=login_as()).status_code == 200


def test_me_without_token_401(client):
    assert client.get("/api/v1/user/me").status_code == 401


def test_me_with_invalid_token_401(client):
    r = client.get("/api/v1/user/me", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401


def test_me_rejects_refresh_token_401(client, login_as):
    login_as(id=5)
    r = client.get("/api/v1/user/me", headers={"Authorization": f"Bearer {create_refresh_token(5)}"})
    assert r.status_code == 401


def test_me_returns_current_user(client, login_as):
    r = client.get("/api/v1/user/me", headers=login_as(email="me@example.com", full_name="Me Myself"))
    assert r.status_code == 200
    assert r.json()["email"] == "me@example.com"
    assert r.json()["full_name"] == "Me Myself"


def test_me_token_for_missing_user_401(client, login_as, auth_headers):
    login_as(id=1)
    assert client.get("/api/v1/user/me", headers=auth_headers(user_id=999)).status_code == 401


def test_me_inactive_user_403(client, login_as):
    assert client.get("/api/v1/user/me", headers=login_as(is_active=False)).status_code == 403


def test_update_me(client, login_as, monkeypatch):
    monkeypatch.setattr("app.services.auth.auth.UserPersist.update_user", lambda db, u, **kw: (
        [setattr(u, k, v) for k, v in kw.items()], u)[1])
    r = client.put("/api/v1/user/me", headers=login_as(), json={"full_name": "Renamed User"})
    assert r.status_code == 200
    assert r.json()["full_name"] == "Renamed User"


def test_update_me_validation_422(client, login_as):
    assert client.put("/api/v1/user/me", headers=login_as(), json={"full_name": "A"}).status_code == 422


def test_change_password_success_and_wrong_current(client, login_as, monkeypatch):
    monkeypatch.setattr("app.services.auth.auth.UserPersist.save_user", lambda db, u: u)
    headers = login_as(hashed_password=hash_password("currentpass1"))
    ok = {"current_password": "currentpass1", "new_password": "newpassword1", "confirm_new_password": "newpassword1"}
    assert client.put("/api/v1/user/me/password", headers=headers, json=ok).status_code == 200
    bad = {**ok, "current_password": "wrong-current"}
    # sau lần đổi đầu hash đã đổi, current cũ không còn đúng
    assert client.put("/api/v1/user/me/password", headers=headers, json=bad).status_code == 400


def test_change_password_mismatch_422(client, login_as):
    body = {"current_password": "x", "new_password": "newpassword1", "confirm_new_password": "different1"}
    assert client.put("/api/v1/user/me/password", headers=login_as(), json=body).status_code == 422


def test_change_password_requires_auth_401(client):
    body = {"current_password": "x", "new_password": "newpassword1", "confirm_new_password": "newpassword1"}
    assert client.put("/api/v1/user/me/password", json=body).status_code == 401
