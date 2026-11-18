"""Semantic search trên pgvector thật (embedding giả, kiểm soát được độ tương đồng)."""
import pytest

from app.repositories.postgres import semantic_search as repo
from app.schemas.semantic_search import JobRequirementSearchRequest, SkillSearchRequest
from app.services.semantic_search import semantic_search as service
from tests.factories import make_jd, make_profile

pytestmark = pytest.mark.integration


@pytest.fixture
def seeded(db_session, seed_user, fake_embedder):
    enc = fake_embedder.encode
    profile = make_profile(user_id=seed_user.Id)
    db_session.add(profile)
    db_session.flush()
    jd = make_jd(title="Backend")
    jd.Responsibility = "build apis"
    jd.VectorResponsibility = enc("python")
    other = make_jd(title="NoVector")  # vector NULL phải bị loại
    db_session.add_all([jd, other])
    db_session.flush()
    from app.models.jd_skill import JDSkill
    from app.models.profile_skill import ProfileSkill

    db_session.add_all([
        ProfileSkill(ProfileId=profile.Id, SkillTitle="python", Vector=enc("python")),
        ProfileSkill(ProfileId=profile.Id, SkillTitle="fastapi", Vector=enc("fastapi")),
        ProfileSkill(ProfileId=profile.Id, SkillTitle="docker", Vector=enc("docker")),
        ProfileSkill(ProfileId=profile.Id, SkillTitle="no-vector", Vector=None),
        JDSkill(JDId=jd.Id, Title="Python", Vector=enc("python")),
    ])
    db_session.flush()
    return profile, jd


def test_results_ordered_by_similarity_desc(db_session, seeded, fake_embedder):
    results = repo.search_profile_skills_vector(db_session, fake_embedder.encode("python"), top_k=5)
    titles = [r[0].SkillTitle for r in results]
    sims = [r[1] for r in results]
    assert titles[:2] == ["python", "fastapi"]
    assert sims == sorted(sims, reverse=True)
    assert sims[0] == pytest.approx(1.0, abs=1e-3)
    assert sims[1] == pytest.approx(0.90, abs=1e-3)
    assert "no-vector" not in titles


def test_min_similarity_filters_rows(db_session, seeded, fake_embedder):
    results = repo.search_profile_skills_vector(db_session, fake_embedder.encode("python"), top_k=5, min_similarity=0.8)
    assert [r[0].SkillTitle for r in results] == ["python", "fastapi"]


def test_top_k_limits_rows(db_session, seeded, fake_embedder):
    assert len(repo.search_profile_skills_vector(db_session, fake_embedder.encode("python"), top_k=1)) == 1


def test_top_k_below_one_raises(db_session, fake_embedder):
    with pytest.raises(ValueError):
        repo.search_profile_skills_vector(db_session, fake_embedder.encode("python"), top_k=0)


def test_job_requirements_excludes_null_vectors(db_session, seeded, fake_embedder):
    results = repo.search_job_requirements_vector(db_session, fake_embedder.encode("python"), top_k=5)
    assert [r[0].Title for r in results] == ["Backend"]
    assert results[0][1] == "Responsibility"


def test_service_merges_sources_and_truncates(db_session, seeded):
    resp = service.search_skills_semantic(db_session, SkillSearchRequest(query="Python", top_k=3))
    assert resp.model_name == "fake-minilm" and resp.total_results == 3
    assert {r.source for r in resp.results} == {"PROFILE_SKILL", "JD_SKILL"}
    sims = [r.similarity for r in resp.results]
    assert sims == sorted(sims, reverse=True)


def test_service_source_filter(db_session, seeded):
    resp = service.search_skills_semantic(db_session, SkillSearchRequest(query="python", source="jd_skill"))
    assert {r.source for r in resp.results} == {"JD_SKILL"}


def test_service_job_requirements(db_session, seeded):
    resp = service.search_job_requirements_semantic(db_session, JobRequirementSearchRequest(query="python"))
    assert resp.total_results == 1 and resp.results[0].title == "Backend"


def test_semantic_search_endpoints_over_real_db(db_client, seeded):
    r = db_client.post("/api/v1/semantic-search/skills", json={"query": "python", "top_k": 2})
    assert r.status_code == 200
    assert [i["title"] for i in r.json()["data"]["results"]][0].lower() == "python"
    r = db_client.post("/api/v1/semantic-search/job-requirements", json={"query": "python"})
    assert r.status_code == 200 and r.json()["data"]["results"][0]["title"] == "Backend"
