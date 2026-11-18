"""
Shared pytest fixtures.

Environment variables are set BEFORE any ``app`` import because
``app.core.security`` reads SECRET_KEY at import time and ``Settings`` reads .env.
The default run is hermetic: no real sentence-transformer model, no Gemini, no Neo4j.
"""

import os
import zlib

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ["GEMINI_API_KEY"] = ""
os.environ["NEO4J_URI"] = "bolt://127.0.0.1:1"  # unreachable on purpose

from typing import Any, Callable, Dict, List, Optional  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

DEFAULT_TEST_DATABASE_URL = (
    "postgresql+psycopg2://postgres:postgres@localhost:55432/jobmatch_test"
)
EMBEDDING_DIM = 384


# ─────────────────────────── Fake embedder ───────────────────────────


def _unit(index: int) -> np.ndarray:
    v = np.zeros(EMBEDDING_DIM)
    v[index] = 1.0
    return v


def _near(base: int, cosine: float, other: int) -> np.ndarray:
    """Unit vector whose cosine with basis vector `base` equals `cosine`."""
    v = np.zeros(EMBEDDING_DIM)
    v[base] = cosine
    v[other] = float(np.sqrt(1.0 - cosine**2))
    return v


def _norm(text_value: str) -> str:
    return " ".join((text_value or "").strip().lower().split())


# Controlled vectors so tests decide the similarity between named skills.
_KNOWN_VECTORS: Dict[str, np.ndarray] = {
    "python": _unit(0),
    "fastapi": _near(0, 0.90, 10),  # cos(python, fastapi) = 0.90 (matched)
    "mysql": _unit(1),
    "postgresql": _near(1, 0.70, 11),  # cos(mysql, postgresql) = 0.70 (partial)
    "docker": _unit(2),
    "rest api": _unit(3),
    "restful apis": _near(3, 0.95, 12),  # near-identical semantic match
}


class FakeEmbedder:
    """Deterministic stand-in for SentenceTransformerClient (384-dim, L2-normalized)."""

    model_name = "fake-minilm"
    embedding_dimension = EMBEDDING_DIM

    def _vector(self, value: str) -> np.ndarray:
        key = _norm(value)
        if key in _KNOWN_VECTORS:
            return _KNOWN_VECTORS[key]
        rng = np.random.default_rng(zlib.crc32(key.encode("utf-8")))
        v = rng.standard_normal(EMBEDDING_DIM)
        return v / np.linalg.norm(v)

    def encode(self, text: str, *, convert_to_tensor: bool = False, normalize: bool = True):
        if not isinstance(text, str):
            raise TypeError("encode() expects a single string")
        return self._vector(text).tolist()

    def encode_batch(self, texts: List[str], **_: Any):
        return [self.encode(t) for t in texts]

    def get_embedding_dimension(self) -> int:
        return self.embedding_dimension

    @staticmethod
    def cosine_similarity(a, b) -> float:
        va = np.asarray(a, dtype=np.float64)
        vb = np.asarray(b, dtype=np.float64)
        if va.shape != vb.shape:
            raise ValueError(f"Embedding dimensions do not match: {va.shape} vs {vb.shape}")
        return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb)))


_FAKE = FakeEmbedder()

_PATCH_TARGETS = (
    "app.clients.sentence_transformer.get_sentence_transformer",
    "app.services.skill_features.skill_gap_analysis.get_sentence_transformer",
    "app.services.skill_features.skill_matching.get_sentence_transformer",
    "app.services.semantic_search.semantic_search.get_sentence_transformer",
)


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return _FAKE


@pytest.fixture(autouse=True)
def _patch_embedder(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest):
    """Replace the embedder everywhere and forbid loading the real model."""
    for target in _PATCH_TARGETS:
        monkeypatch.setattr(target, lambda: _FAKE)

    if request.node.get_closest_marker("external") is None:
        from app.clients.sentence_transformer import SentenceTransformerClient

        def _forbid(*_args: Any, **_kwargs: Any):
            raise AssertionError("real model load in tests")

        monkeypatch.setattr(SentenceTransformerClient, "__init__", _forbid)


# ─────────────────────────── App / client ────────────────────────────


@pytest.fixture(scope="session")
def app_instance():
    import app.main as main_module

    # TestClient without ``with`` does not run lifespan; patch anyway for safety.
    main_module.neo4j_client.connect = lambda *a, **k: None
    main_module.init_graph_schema = lambda *a, **k: None
    return main_module.app


@pytest.fixture
def client(app_instance):
    from fastapi.testclient import TestClient

    c = TestClient(app_instance)
    yield c
    app_instance.dependency_overrides.clear()


@pytest.fixture
def mock_db() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture
def override_db(app_instance) -> Callable[[Any], None]:
    from app.core.database import get_db

    def _override(db: Any) -> None:
        app_instance.dependency_overrides[get_db] = lambda: db

    return _override


@pytest.fixture
def auth_headers() -> Callable[..., Dict[str, str]]:
    from app.core.security import create_access_token
    from app.models.enum import UserRole

    def _make(role: Any = UserRole.CANDIDATE, user_id: int = 1, email: str = "user@example.com"):
        role_value = role.value if hasattr(role, "value") else str(role)
        return {"Authorization": f"Bearer {create_access_token(user_id, email, role_value)}"}

    return _make


# ─────────────────────────── Integration DB ──────────────────────────


@pytest.fixture(scope="session")
def pg_engine():
    url = os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
    db_name = make_url(url).database or ""
    if not db_name.endswith("_test"):
        pytest.skip(f"Refusing to run against database '{db_name}': name must end with _test")

    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        engine.dispose()
        pytest.skip(f"Test PostgreSQL unreachable at TEST_DATABASE_URL: {exc.__class__.__name__}")

    import app.models  # noqa: F401  (register all tables on Base.metadata)
    from app.core.database import Base

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(pg_engine):
    conn = pg_engine.connect()
    trans = conn.begin()
    session = Session(bind=conn, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()


@pytest.fixture
def db_client(client, db_session, override_db):
    override_db(db_session)
    return client
