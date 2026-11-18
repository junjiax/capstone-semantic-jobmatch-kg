"""Endpoint tests for /api/v1/profile và /api/v1/jd (DB giả)."""
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.models.enum import UserRole
from tests.factories import make_jd, make_profile

pytestmark = pytest.mark.api


def _profile(pid=1, user_id=1, skills=("python",)):
    p = make_profile(user_id=user_id, skills=skills)
    p.Id = pid
    p.CreatedAt = datetime.now(timezone.utc)
    p.FileUrl = "uploads/x.txt"
    return p


@pytest.fixture
def graph_mock(monkeypatch):
    m = MagicMock()
    monkeypatch.setattr("app.api.v1.routers.router.profile.graph_service", m)
    return m


# ── /profile ────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "method,path",
    [("get", "/api/v1/profile/mine"), ("get", "/api/v1/profile/available"),
     ("post", "/api/v1/profile/upload"), ("patch", "/api/v1/profile/1")],
)
def test_profile_endpoints_require_auth_401(client, method, path):
    assert getattr(client, method)(path).status_code == 401


def test_list_my_profiles(client, login_as, mock_db):
    headers = login_as()
    mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
        _profile(pid=4, skills=("python", "docker"))
    ]
    r = client.get("/api/v1/profile/mine", headers=headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data[0]["id"] == 4 and data[0]["skills"] == ["python", "docker"]


def test_available_profiles_candidate_is_filtered_admin_is_not(client, login_as, mock_db):
    headers = login_as(UserRole.CANDIDATE)
    q = mock_db.query.return_value
    q.filter.return_value.order_by.return_value.all.return_value = [_profile(pid=1)]
    q.order_by.return_value.all.return_value = [_profile(pid=1), _profile(pid=2, user_id=9)]
    assert len(client.get("/api/v1/profile/available", headers=headers).json()["data"]) == 1
    admin = login_as(UserRole.ADMIN, id=2, email="admin@example.com")
    assert len(client.get("/api/v1/profile/available", headers=admin).json()["data"]) == 2


def test_upload_txt_extracts_skills(client, login_as, mock_db, graph_mock, monkeypatch, tmp_path):
    monkeypatch.setattr("app.api.v1.routers.router.profile.UPLOAD_ROOT", tmp_path)
    cv = b"Nguyen Van A\nBackend dev with Python, FastAPI and Docker. a@b.com"
    r = client.post("/api/v1/profile/upload", headers=login_as(), files={"file": ("cv.txt", cv, "text/plain")})
    assert r.status_code == 201
    data = r.json()["data"]
    assert {"python", "fastapi", "docker"} <= set(data["skills"])
    assert data["email"] == "a@b.com"
    assert mock_db.commit.called
    graph_mock.sync_cv_to_graph.assert_called_once()


def test_upload_survives_graph_sync_failure(client, login_as, graph_mock, monkeypatch, tmp_path):
    monkeypatch.setattr("app.api.v1.routers.router.profile.UPLOAD_ROOT", tmp_path)
    graph_mock.sync_cv_to_graph.side_effect = RuntimeError("neo4j down")
    r = client.post("/api/v1/profile/upload", headers=login_as(),
                    files={"file": ("cv.txt", b"python dev", "text/plain")})
    assert r.status_code == 201


def test_upload_rejects_bad_extension_400(client, login_as, graph_mock, monkeypatch, tmp_path):
    monkeypatch.setattr("app.api.v1.routers.router.profile.UPLOAD_ROOT", tmp_path)
    r = client.post("/api/v1/profile/upload", headers=login_as(),
                    files={"file": ("cv.exe", b"MZ", "application/octet-stream")})
    assert r.status_code == 400
    assert list(tmp_path.iterdir()) == []


def test_upload_empty_text_422_and_file_removed(client, login_as, graph_mock, monkeypatch, tmp_path):
    monkeypatch.setattr("app.api.v1.routers.router.profile.UPLOAD_ROOT", tmp_path)
    r = client.post("/api/v1/profile/upload", headers=login_as(),
                    files={"file": ("cv.txt", b"   \n", "text/plain")})
    assert r.status_code == 422
    assert list(tmp_path.iterdir()) == []


def test_upload_without_file_422(client, login_as):
    assert client.post("/api/v1/profile/upload", headers=login_as()).status_code == 422


def test_patch_profile_updates_title_and_skills(client, login_as, mock_db, graph_mock):
    headers = login_as()
    profile = _profile(pid=3, skills=("old",))
    mock_db.query.return_value.filter.return_value.first.return_value = profile
    r = client.patch("/api/v1/profile/3", headers=headers, json={"title": " New CV ", "skills": ["Go", "Go", " "]})
    assert r.status_code == 200
    assert profile.Title == "New CV"
    assert [s.SkillTitle for s in profile.skills] == ["Go"]


def test_patch_profile_not_found_404(client, login_as, mock_db):
    headers = login_as()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    assert client.patch("/api/v1/profile/99", headers=headers, json={"title": "x"}).status_code == 404


def test_patch_profile_invalid_id_422(client, login_as):
    assert client.patch("/api/v1/profile/abc", headers=login_as(), json={}).status_code == 422


# ── /jd ─────────────────────────────────────────────────────────────────────
def test_jd_available_requires_auth_401(client):
    assert client.get("/api/v1/jd/available").status_code == 401


def test_jd_available_lists_jobs(client, login_as, mock_db):
    headers = login_as()
    jd = make_jd(title="Backend", Domain="IT", Expertise="Backend", Experience=2)
    jd.Id = 5
    jd.CreatedAt = datetime.now(timezone.utc)
    mock_db.query.return_value.order_by.return_value.all.return_value = [jd]
    r = client.get("/api/v1/jd/available", headers=headers)
    assert r.status_code == 200
    item = r.json()["data"][0]
    assert item["id"] == 5 and item["title"] == "Backend" and item["experience"] == 2


def test_jd_available_empty(client, login_as, mock_db):
    headers = login_as()
    mock_db.query.return_value.order_by.return_value.all.return_value = []
    assert client.get("/api/v1/jd/available", headers=headers).json()["data"] == []
