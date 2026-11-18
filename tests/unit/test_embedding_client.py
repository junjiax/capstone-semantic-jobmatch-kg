from unittest.mock import MagicMock

import numpy as np
import pytest
import torch

from app.clients.sentence_transformer import SentenceTransformerClient
from tests.conftest import EMBEDDING_DIM, FakeEmbedder

pytestmark = pytest.mark.unit


@pytest.fixture
def client_with_stub_model():
    """Client instance built without loading a model (conftest forbids __init__)."""
    client = object.__new__(SentenceTransformerClient)
    model = MagicMock()
    model.encode.side_effect = lambda payload, **kw: (
        np.ones((len(payload), 3)) if isinstance(payload, list) else np.ones(3)
    )
    client._model = model
    return client, model


def test_cosine_similarity_static_values():
    cos = SentenceTransformerClient.cosine_similarity
    assert cos([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cos([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cos(torch.tensor([1.0, 1.0]), [2.0, 2.0]) == pytest.approx(1.0)


def test_cosine_similarity_rejects_shape_mismatch():
    with pytest.raises(ValueError, match="dimensions"):
        SentenceTransformerClient.cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0])


def test_encode_requires_string(client_with_stub_model):
    client, _ = client_with_stub_model
    with pytest.raises(TypeError):
        client.encode(["a", "b"])  # type: ignore[arg-type]


def test_encode_blank_text_is_replaced_by_single_space(client_with_stub_model):
    client, model = client_with_stub_model
    assert client.encode("   ") == [1.0, 1.0, 1.0]
    assert model.encode.call_args.args[0] == " "
    assert model.encode.call_args.kwargs["normalize_embeddings"] is True


def test_encode_batch_cleans_inputs_and_handles_empty(client_with_stub_model):
    client, model = client_with_stub_model
    assert client.encode_batch([]) == []
    out = client.encode_batch([" a ", "", "b"])
    assert len(out) == 3
    assert model.encode.call_args.args[0] == ["a", " ", "b"]


def test_real_client_cannot_be_constructed_in_hermetic_tests():
    with pytest.raises(AssertionError, match="real model load"):
        SentenceTransformerClient()


# ── FakeEmbedder contract (guards the helper the other tests rely on) ────────


def test_fake_embedder_dimension_and_normalization():
    fake = FakeEmbedder()
    vec = fake.encode("Anything at all")
    assert len(vec) == EMBEDDING_DIM == fake.embedding_dimension
    assert np.linalg.norm(vec) == pytest.approx(1.0)


def test_fake_embedder_is_deterministic_and_case_insensitive():
    fake = FakeEmbedder()
    assert fake.encode("Docker") == fake.encode("  docker ")
    assert fake.encode("unknown skill x") == fake.encode("unknown skill x")


def test_fake_embedder_controlled_similarities():
    fake = FakeEmbedder()
    sim = fake.cosine_similarity
    assert sim(fake.encode("python"), fake.encode("fastapi")) == pytest.approx(0.90)
    assert sim(fake.encode("mysql"), fake.encode("postgresql")) == pytest.approx(0.70)
    assert sim(fake.encode("python"), fake.encode("docker")) == pytest.approx(0.0)


def test_embedder_is_patched_in_all_modules(fake_embedder):
    from app.clients import sentence_transformer as st
    from app.services.semantic_search import semantic_search
    from app.services.skill_features import skill_gap_analysis, skill_matching

    for module in (st, semantic_search, skill_gap_analysis, skill_matching):
        assert module.get_sentence_transformer() is fake_embedder
