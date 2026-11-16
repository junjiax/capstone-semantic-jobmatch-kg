from fastapi import APIRouter
from app.api.v1.routers.router import (
    auth,
    user,
    graph_router,
    semantic_search,
    skill_gap,
    skill_match,
    profile,
    jd,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(user.router, prefix="/user", tags=["Users"])
api_router.include_router(profile.router, prefix="/profile", tags=["Profiles"])
api_router.include_router(jd.router, prefix="/jd", tags=["Jobs"])


"""
    KNOWLEDGE GRAPH
"""

api_router.include_router(
    graph_router.router, prefix="/graph", tags=["Knowledge Graph"]
)

"""
    SEMANTIC-SEARCH
"""

api_router.include_router(
    semantic_search.router, prefix="/semantic-search", tags=["Semantic Search"]
)

"""
    SKILL-MATCHING
"""
api_router.include_router(skill_match.router, prefix="/graph", tags=["Skill Matching"])

"""
    SKILL-GAP-ANALYSIS
"""
api_router.include_router(
    skill_gap.router, prefix="/skill-gap", tags=["Skill Gap Analysis"]
)


# ── Public Routes (accessible without auth) ─────────────────
public_router = APIRouter()

api_router.include_router(public_router)


# ── Private / Authenticated Routes ─────────────────────────
private_router = APIRouter()

api_router.include_router(private_router)
