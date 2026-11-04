from fastapi import APIRouter
from app.api.v1.routers.router import (
    auth,
    profile,
    users,
    health,
    graph_router,
    job,
    semantic_search,
)

api_router = APIRouter()

api_router.include_router(
    health.router, prefix="/health", tags=["Health"]
)
api_router.include_router(
    auth.router, prefix="/auth", tags=["Auth"]
)
api_router.include_router(
    users.router, prefix="/users", tags=["Users"]
)
api_router.include_router(
    graph_router.router, prefix="/graph", tags=["Knowledge Graph"]
)
api_router.include_router(
    semantic_search.router, prefix="/semantic-search", tags=["Semantic Search"]
)
api_router.include_router(
    job.router, prefix="/job", tags=["Job"]
)
api_router.include_router(
    profile.router, prefix="/user-profile", tags=["User Profile"]
)


# ── Public Routes (accessible without auth) ─────────────────
public_router = APIRouter()

api_router.include_router(public_router)



# ── Private / Authenticated Routes ─────────────────────────
private_router = APIRouter()

api_router.include_router(private_router)
