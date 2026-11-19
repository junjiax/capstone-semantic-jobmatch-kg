"""Kiểm tra OpenAPI schema và trang tài liệu."""
import pytest

pytestmark = pytest.mark.api

EXPECTED_PATHS = {
    "/api/v1/auth/register", "/api/v1/auth/login", "/api/v1/auth/logout", "/api/v1/auth/refresh",
    "/api/v1/auth/forgot-password", "/api/v1/auth/reset-password",
    "/api/v1/user/me", "/api/v1/user/me/password",
    "/api/v1/profile/mine", "/api/v1/profile/available", "/api/v1/profile/upload", "/api/v1/profile/{profile_id}",
    "/api/v1/jd/available",
    "/api/v1/graph/stats", "/api/v1/graph/match-similarity",
    "/api/v1/semantic-search/skills", "/api/v1/semantic-search/job-requirements",
    "/api/v1/skill-gap/health", "/api/v1/skill-gap/analyze", "/api/v1/skill-gap/profile/{profile_id}/jd/{jd_id}",
}


@pytest.fixture
def schema(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    return r.json()


def test_openapi_lists_expected_paths(schema):
    assert EXPECTED_PATHS <= set(schema["paths"])


def test_every_operation_has_tag_and_unique_operation_id(schema):
    ids = []
    for path, item in schema["paths"].items():
        for method, op in item.items():
            assert op.get("tags"), f"{method} {path} thiếu tags"
            ids.append(op["operationId"])
    assert len(ids) == len(set(ids))


def test_bearer_oauth2_security_scheme_declared(schema):
    schemes = schema["components"]["securitySchemes"]
    assert any(s.get("type") == "oauth2" for s in schemes.values())


def test_protected_and_public_operations_declare_security(schema):
    assert schema["paths"]["/api/v1/user/me"]["get"].get("security")
    assert not schema["paths"]["/api/v1/semantic-search/skills"]["post"].get("security")


def test_login_documented_as_form_data(schema):
    content = schema["paths"]["/api/v1/auth/login"]["post"]["requestBody"]["content"]
    assert "application/x-www-form-urlencoded" in content


@pytest.mark.parametrize("path", ["/docs", "/redoc"])
def test_docs_pages_render(client, path):
    r = client.get(path)
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]


def test_unknown_route_404(client):
    assert client.get("/api/v1/does-not-exist").status_code == 404


def test_exported_openapi_json_matches_app(schema):
    """docs/openapi.json phải khớp app.openapi(); chạy `python -m scripts.export_openapi` nếu lệch."""
    import json
    from pathlib import Path

    exported = json.loads((Path(__file__).resolve().parents[2] / "docs" / "openapi.json").read_text(encoding="utf-8"))
    assert set(exported["paths"]) == set(schema["paths"])
    for path, item in schema["paths"].items():
        assert set(exported["paths"][path]) == set(item), path
    assert exported == json.loads(json.dumps(schema))
