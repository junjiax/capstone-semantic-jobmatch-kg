"""Fixtures dùng chung cho API tests (không cần DB thật)."""
from datetime import datetime, timezone
from typing import Callable

import pytest

from app.models.enum import UserRole
from tests.factories import make_user


def make_api_user(**kwargs):
    """User có đủ timestamps để serialize qua UserResponse."""
    user = make_user(**kwargs)
    now = datetime.now(timezone.utc)
    user.CreatedAt = now
    user.UpdatedAt = now
    user.Phone = kwargs.get("phone")
    return user


@pytest.fixture
def login_as(monkeypatch: pytest.MonkeyPatch, mock_db, override_db, auth_headers) -> Callable:
    """Trả về header Bearer hợp lệ; get_user_by_id trả về user giả (JWT thật, DB giả)."""

    def _login(role: UserRole = UserRole.CANDIDATE, **kwargs):
        user = make_api_user(id=kwargs.pop("id", 1), role=role, **kwargs)
        monkeypatch.setattr(
            "app.api.deps.user_crud.get_user_by_id",
            lambda db, user_id: user if user_id == user.Id else None,
        )
        override_db(mock_db)
        return auth_headers(role=role, user_id=user.Id, email=user.Email)

    return _login
