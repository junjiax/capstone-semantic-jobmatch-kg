"""Fixtures cho integration tests (PostgreSQL + pgvector test DB)."""
import pytest

from tests.factories import make_user


@pytest.fixture
def seed_user(db_session):
    user = make_user(email="seed@example.com", hashed_password="x")
    db_session.add(user)
    db_session.flush()
    return user
