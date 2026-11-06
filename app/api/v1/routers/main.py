from fastapi import APIRouter
from app.api.v1.routers.router import (
    auth,
    user,
    profile,
    health,
    graph_router,
    job,
    semantic_search,
    skill_gap,
    skill_match,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(user.router, prefix="/user", tags=["Users"])
api_router.include_router(profile.router, prefix="/user-profile", tags=["User Profile"])
api_router.include_router(job.router, prefix="/job", tags=["Job"])
api_router.include_router(graph_router.router, prefix="/graph", tags=["Knowledge Graph"])
api_router.include_router(semantic_search.router, prefix="/semantic-search", tags=["Semantic Search"])
api_router.include_router(skill_match.router, prefix="/skill-match", tags=["Skill Matching"])
api_router.include_router(skill_gap.router, prefix="/skill-gap", tags=["Skill Gap Analysis"])


# ── Public Routes (accessible without auth) ─────────────────
public_router = APIRouter()

api_router.include_router(public_router)


# ── Private / Authenticated Routes ─────────────────────────
private_router = APIRouter()

api_router.include_router(private_router)
