from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.core import TokenType, security

pytestmark = pytest.mark.unit


def test_hash_password_is_salted_and_verifiable():
    h1 = security.hash_password("S3cret-pass")
    h2 = security.hash_password("S3cret-pass")
    assert h1 != h2
    assert security.verify_password("S3cret-pass", h1)
    assert security.verify_password("S3cret-pass", h2)
    assert not security.verify_password("wrong", h1)


def test_verify_password_returns_false_for_malformed_hash():
    assert security.verify_password("x", "not-a-bcrypt-hash") is False


def test_long_password_is_supported_via_sha256_prehash():
    long_password = "a" * 200  # bcrypt alone rejects > 72 bytes
    assert security.verify_password(long_password, security.hash_password(long_password))


def test_access_token_payload():
    token = security.create_access_token(5, "a@b.com", "admin")
    payload = security.decode_token(token)
    assert payload["sub"] == "5"
    assert payload["email"] == "a@b.com"
    assert payload["role"] == "admin"
    assert payload["type"] == TokenType.ACCESS.value
    assert payload["exp"] > payload["iat"]


def test_token_types_are_enforced():
    access = security.create_access_token(1, "a@b.com", "candidate")
    refresh = security.create_refresh_token(1)
    reset = security.create_reset_token("a@b.com")

    assert security.verify_token(access) is not None  # default expected type is access
    assert security.verify_token(refresh) is None
    assert security.verify_token(reset) is None
    assert security.decode_token(refresh, "refresh")["sub"] == "1"
    assert security.decode_token(reset, "reset")["sub"] == "a@b.com"
    assert security.decode_token(access, "refresh") is None


def test_token_lifetimes():
    def lifetime(token):
        p = security.decode_token(token)
        return p["exp"] - p["iat"]

    assert lifetime(security.create_refresh_token(1)) == security.REFRESH_TOKEN_EXPIRE_SECONDS
    assert lifetime(security.create_reset_token("a@b.com")) == security.RESET_TOKEN_EXPIRE_SECONDS == 900
    assert lifetime(security.create_access_token(1, "a@b.com", "candidate")) == (
        security.ACCESS_TOKEN_EXPIRE_SECONDS
    )


def test_expired_token_is_rejected():
    token = security._create_token_base(1, -10, TokenType.ACCESS)
    assert security.decode_token(token) is None


def test_tampered_or_foreign_tokens_are_rejected():
    assert security.decode_token("garbage") is None
    forged = jwt.encode(
        {"sub": "1", "type": "access", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "another-secret",
        algorithm=security.ALGORITHM,
    )
    assert security.decode_token(forged) is None
    good = security.create_access_token(1, "a@b.com", "candidate")
    assert security.decode_token(good[:-2] + "xx") is None
