import pytest
from pydantic import ValidationError

from app.schemas.semantic_search import JobRequirementSearchRequest, SkillSearchRequest
from app.schemas.user import (
    ForgotPasswordRequest,
    PasswordChange,
    ResetPasswordRequest,
    TokenResponse,
    UserRegister,
)

pytestmark = pytest.mark.unit


def _register(**overrides):
    data = {
        "email": "a@example.com",
        "full_name": "Nguyen Van A",
        "password": "password123",
        "confirm_password": "password123",
    }
    data.update(overrides)
    return UserRegister(**data)


def test_user_register_valid_defaults():
    user = _register()
    assert user.phone is None
    assert user.is_verified is True


@pytest.mark.parametrize(
    "overrides",
    [
        {"confirm_password": "different1"},
        {"password": "short", "confirm_password": "short"},
        {"email": "not-an-email"},
        {"full_name": "A"},
        {"phone": "1" * 21},
    ],
)
def test_user_register_rejects_invalid_input(overrides):
    with pytest.raises(ValidationError):
        _register(**overrides)


def test_password_change_requires_matching_and_long_enough_password():
    PasswordChange(current_password="x", new_password="newpass123", confirm_new_password="newpass123")
    with pytest.raises(ValidationError):
        PasswordChange(current_password="x", new_password="newpass123", confirm_new_password="nope")
    with pytest.raises(ValidationError):
        PasswordChange(current_password="x", new_password="short", confirm_new_password="short")


def test_reset_password_request_mismatch_rejected():
    with pytest.raises(ValidationError):
        ResetPasswordRequest(token="t", new_password="newpass123", confirm_new_password="other123")


def test_forgot_password_requires_valid_email():
    assert ForgotPasswordRequest(email="a@example.com").email == "a@example.com"
    with pytest.raises(ValidationError):
        ForgotPasswordRequest(email="nope")


def test_token_response_default_type_is_bearer():
    assert TokenResponse(access_token="a", refresh_token="r").token_type == "bearer"


def test_skill_search_request_defaults_and_bounds():
    req = SkillSearchRequest(query="python")
    assert (req.top_k, req.min_similarity, req.source) == (5, 0.0, "all")
    for bad in (
        {"query": ""},
        {"query": "x" * 501},
        {"query": "x", "top_k": 0},
        {"query": "x", "top_k": 51},
        {"query": "x", "min_similarity": 1.5},
        {"query": "x", "source": "other"},
    ):
        with pytest.raises(ValidationError):
            SkillSearchRequest(**bad)


def test_job_requirement_request_bounds():
    assert JobRequirementSearchRequest(query="x" * 1000).top_k == 5
    with pytest.raises(ValidationError):
        JobRequirementSearchRequest(query="x" * 1001)
    with pytest.raises(ValidationError):
        JobRequirementSearchRequest(query="x", top_k=0)
