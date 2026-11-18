"""Luồng đầy đủ qua TestClient trên PostgreSQL thật: register -> login -> me -> upload CV -> skill gap -> match."""
from unittest.mock import MagicMock

import pytest

from app.models.enum import UserRole
from app.models.user import User
from tests.factories import make_jd

pytestmark = pytest.mark.integration

EMAIL = "flow@example.com"
PASSWORD = "password123"


@pytest.fixture
def no_graph(monkeypatch):
    monkeypatch.setattr("app.api.v1.routers.router.profile.graph_service", MagicMock())
    for name in ("sync_cv_to_graph", "sync_job_to_graph", "save_cv_jd_match_result_graph"):
        monkeypatch.setattr(f"app.services.skill_features.skill_matching.{name}", MagicMock())


def test_register_login_me(db_client, db_session):
    r = db_client.post("/api/v1/auth/register", json={
        "email": EMAIL, "full_name": "Flow User", "password": PASSWORD, "confirm_password": PASSWORD})
    assert r.status_code == 201
    assert db_client.post("/api/v1/auth/register", json={
        "email": EMAIL, "full_name": "Flow User", "password": PASSWORD, "confirm_password": PASSWORD}).status_code == 409
    login = db_client.post("/api/v1/auth/login", data={"username": EMAIL, "password": PASSWORD})
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    me = db_client.get("/api/v1/user/me", headers=headers)
    assert me.status_code == 200 and me.json()["email"] == EMAIL
    assert db_client.post("/api/v1/auth/login", data={"username": EMAIL, "password": "wrong-pass"}).status_code == 401


def test_refresh_after_register_is_rejected_until_verified(db_client, db_session):
    """Lỗi ứng dụng đã biết: register_user không set IsVerified nên refresh bị 401."""
    db_client.post("/api/v1/auth/register", json={
        "email": EMAIL, "full_name": "Flow User", "password": PASSWORD, "confirm_password": PASSWORD})
    tokens = db_client.post("/api/v1/auth/login", data={"username": EMAIL, "password": PASSWORD}).json()
    assert db_client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    user = db_session.query(User).filter(User.Email == EMAIL).one()
    user.IsVerified = True
    db_session.flush()
    assert db_client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 200


def test_full_flow_upload_cv_then_gap_and_match(db_client, db_session, no_graph, monkeypatch, tmp_path):
    monkeypatch.setattr("app.api.v1.routers.router.profile.UPLOAD_ROOT", tmp_path)
    db_client.post("/api/v1/auth/register", json={
        "email": EMAIL, "full_name": "Flow User", "password": PASSWORD, "confirm_password": PASSWORD})
    token = db_client.post("/api/v1/auth/login", data={"username": EMAIL, "password": PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    cv = b"Flow User\nBackend developer. Skills: Python, FastAPI, Docker, PostgreSQL."
    up = db_client.post("/api/v1/profile/upload", headers=headers, files={"file": ("cv.txt", cv, "text/plain")})
    assert up.status_code == 201
    profile_id = up.json()["data"]["id"]

    mine = db_client.get("/api/v1/profile/mine", headers=headers).json()["data"]
    assert [p["id"] for p in mine] == [profile_id]
    assert {"python", "fastapi", "docker", "postgresql"} <= set(mine[0]["skills"])

    jd = make_jd(title="Backend Engineer", skills=["Python", "Docker", "Kubernetes"], CleanText="python backend")
    db_session.add(jd)
    db_session.flush()
    jobs = db_client.get("/api/v1/jd/available", headers=headers).json()["data"]
    assert jd.Id in [j["id"] for j in jobs]

    gap = db_client.post("/api/v1/skill-gap/analyze", json={"profile_id": profile_id, "jd_id": jd.Id})
    assert gap.status_code == 200
    assert [m["skill_name"] for m in gap.json()["data"]["missing_skills"]] == ["Kubernetes"]

    match = db_client.get("/api/v1/graph/match-similarity", params={"profile_id": profile_id, "jd_id": jd.Id})
    assert match.status_code == 200
    assert match.json()["data"]["is_suitable"] is True


def test_candidate_cannot_use_admin_routes_and_cannot_patch_others_cv(db_client, db_session, no_graph):
    from app.core.security import hash_password
    from tests.factories import make_profile, make_user

    owner = make_user(email="owner@example.com", hashed_password=hash_password(PASSWORD))
    other = make_user(email="other@example.com", hashed_password=hash_password(PASSWORD), role=UserRole.CANDIDATE)
    db_session.add_all([owner, other])
    db_session.flush()
    profile = make_profile(user_id=owner.Id, skills=["python"])
    db_session.add(profile)
    db_session.flush()
    token = db_client.post("/api/v1/auth/login", data={"username": "other@example.com", "password": PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert db_client.get("/api/v1/graph/stats", headers=headers).status_code == 403
    assert db_client.patch(f"/api/v1/profile/{profile.Id}", headers=headers, json={"title": "hack"}).status_code == 404
    assert db_client.post(f"/api/v1/graph/match/{profile.Id}/1", headers=headers).status_code == 403


def test_admin_stats_over_real_db(db_client, db_session):
    from app.core.security import hash_password
    from tests.factories import make_user

    admin = make_user(email="admin@example.com", hashed_password=hash_password(PASSWORD), role=UserRole.ADMIN)
    db_session.add(admin)
    db_session.flush()
    token = db_client.post("/api/v1/auth/login", data={"username": "admin@example.com", "password": PASSWORD}).json()["access_token"]
    r = db_client.get("/api/v1/graph/stats", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["data"]["users"] >= 1
