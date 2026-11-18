"""Endpoint tests for /api/v1/graph (graph_service được mock, không dùng Neo4j)."""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.models.enum import UserRole
from tests.factories import make_profile

pytestmark = pytest.mark.api

GRAPH = "app.api.v1.routers.router.graph_router.graph_service"
ADMIN_ONLY = [
    ("get", "/api/v1/graph/stats"),
    ("post", "/api/v1/graph/schema/init"),
    ("post", "/api/v1/graph/sync/all"),
    ("post", "/api/v1/graph/sync/job/1"),
    ("get", "/api/v1/graph/jobs/1/candidates"),
]
CV_ROUTES = [
    ("post", "/api/v1/graph/sync/cv/1"),
    ("get", "/api/v1/graph/cvs/1/skills"),
    ("get", "/api/v1/graph/cvs/1/education"),
    ("get", "/api/v1/graph/cvs/1/experience"),
    ("get", "/api/v1/graph/skill-gap/1/2"),
    ("post", "/api/v1/graph/match/1/2"),
    ("get", "/api/v1/graph/matrix/domain-gap/1"),
]


@pytest.fixture
def gs(monkeypatch):
    m = MagicMock()
    monkeypatch.setattr(GRAPH, m)
    return m


def _owned_profile(mock_db, owner_id=1):
    p = make_profile(user_id=owner_id)
    p.Id = 1
    mock_db.query.return_value.filter.return_value.first.return_value = p
    return p


@pytest.mark.parametrize("method,path", ADMIN_ONLY + CV_ROUTES)
def test_graph_routes_require_auth_401(client, method, path):
    assert getattr(client, method)(path).status_code == 401


@pytest.mark.parametrize("method,path", ADMIN_ONLY)
def test_admin_routes_forbid_candidate_403(client, login_as, gs, method, path):
    assert getattr(client, method)(path, headers=login_as(UserRole.CANDIDATE)).status_code == 403


def test_stats_admin_ok(client, login_as, mock_db):
    headers = login_as(UserRole.ADMIN)
    mock_db.query.return_value.count.return_value = 3
    mock_db.query.return_value.filter.return_value.scalar.return_value = 2
    r = client.get("/api/v1/graph/stats", headers=headers)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["users"] == 3 and data["domains"] == 2


def test_schema_init_and_sync_all_admin(client, login_as, gs):
    headers = login_as(UserRole.ADMIN)
    gs.setup_knowledge_graph_schema.return_value = {"constraints": 1}
    gs.sync_all_from_postgres.return_value = {"cvs": 2}
    assert client.post("/api/v1/graph/schema/init", headers=headers).json()["data"] == {"constraints": 1}
    assert client.post("/api/v1/graph/sync/all", headers=headers).json()["data"] == {"cvs": 2}


@pytest.mark.parametrize("ok,status", [(True, 200), (False, 400)])
def test_sync_job_admin(client, login_as, gs, ok, status):
    gs.sync_job_to_graph.return_value = ok
    assert client.post("/api/v1/graph/sync/job/1", headers=login_as(UserRole.ADMIN)).status_code == status


def test_candidates_admin_and_top_k_bounds(client, login_as, gs):
    headers = login_as(UserRole.ADMIN)
    gs.hybrid_search_candidates_service.return_value = [{"cvId": 1}]
    r = client.get("/api/v1/graph/jobs/1/candidates", headers=headers, params={"top_k": 5})
    assert r.status_code == 200 and r.json()["data"] == [{"cvId": 1}]
    assert client.get("/api/v1/graph/jobs/1/candidates", headers=headers, params={"top_k": 0}).status_code == 422
    assert client.get("/api/v1/graph/jobs/1/candidates", headers=headers, params={"top_k": 51}).status_code == 422


def test_cv_route_owner_ok_and_sync(client, login_as, mock_db, gs):
    headers = login_as(UserRole.CANDIDATE, id=1)
    _owned_profile(mock_db, owner_id=1)
    gs.sync_cv_to_graph.return_value = True
    assert client.post("/api/v1/graph/sync/cv/1", headers=headers).status_code == 200
    gs.sync_cv_to_graph.return_value = False
    assert client.post("/api/v1/graph/sync/cv/1", headers=headers).status_code == 400


def test_cv_route_other_users_cv_403(client, login_as, mock_db, gs):
    headers = login_as(UserRole.CANDIDATE, id=1)
    _owned_profile(mock_db, owner_id=2)
    assert client.post("/api/v1/graph/sync/cv/1", headers=headers).status_code == 403


def test_cv_route_admin_can_access_any_cv(client, login_as, mock_db, gs):
    headers = login_as(UserRole.ADMIN, id=9)
    _owned_profile(mock_db, owner_id=2)
    gs.calculate_cv_jd_matching_service.return_value = {"score": 0.5}
    r = client.post("/api/v1/graph/match/1/2", headers=headers)
    assert r.status_code == 200 and r.json()["data"] == {"score": 0.5}


def test_cv_route_unknown_cv_404(client, login_as, mock_db, gs):
    headers = login_as()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    assert client.post("/api/v1/graph/match/1/2", headers=headers).status_code == 404


def test_match_service_error_maps_to_404(client, login_as, mock_db, gs):
    headers = login_as(UserRole.CANDIDATE, id=1)
    _owned_profile(mock_db)
    gs.calculate_cv_jd_matching_service.return_value = {"error": "JD không tồn tại"}
    assert client.post("/api/v1/graph/match/1/2", headers=headers).status_code == 404


def test_non_numeric_id_422(client, login_as, gs):
    assert client.post("/api/v1/graph/match/a/2", headers=login_as()).status_code == 422


def test_graph_read_routes_use_match_crud(client, login_as, mock_db, monkeypatch):
    headers = login_as(UserRole.CANDIDATE, id=1)
    _owned_profile(mock_db)
    monkeypatch.setattr("app.repositories.graph.match_crud.get_cv_skills_graph", lambda cv_id: ["python"])
    monkeypatch.setattr("app.repositories.graph.match_crud.get_job_required_skills_graph", lambda job_id: ["sql"])
    assert client.get("/api/v1/graph/cvs/1/skills", headers=headers).json()["data"] == ["python"]
    # route này không yêu cầu đăng nhập (hành vi hiện tại)
    assert client.get("/api/v1/graph/jobs/1/skills").json()["data"] == ["sql"]


# ── Lỗi ứng dụng đã biết: graph_service thiếu hàm ───────────────────────────
@pytest.fixture
def lenient_client(app_instance):
    return TestClient(app_instance, raise_server_exceptions=False)


@pytest.mark.xfail(
    reason="graph_router gọi graph_service.get_skill_gap_analysis_service nhưng hàm không tồn tại (AttributeError -> 500)",
    strict=False,
)
def test_graph_skill_gap_endpoint_works(lenient_client, login_as, mock_db):
    headers = login_as(UserRole.CANDIDATE, id=1)
    _owned_profile(mock_db)
    assert lenient_client.get("/api/v1/graph/skill-gap/1/2", headers=headers).status_code == 200


@pytest.mark.xfail(
    reason="graph_router gọi graph_service.calculate_domain_skill_gap_matrix_service nhưng hàm không tồn tại (AttributeError -> 500)",
    strict=False,
)
def test_graph_domain_gap_matrix_endpoint_works(lenient_client, login_as, mock_db):
    headers = login_as(UserRole.CANDIDATE, id=1)
    _owned_profile(mock_db)
    assert lenient_client.get("/api/v1/graph/matrix/domain-gap/1", headers=headers).status_code == 200
