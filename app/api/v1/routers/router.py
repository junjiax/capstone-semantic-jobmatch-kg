from fastapi import APIRouter
from app.api.v1.routers import (
    applicant,
    cv,
    data,
    education,
    experience,
    health,
    job,
    users,
    auth,
    # embedding,
    application_router as application,
    graph_router,
    semantic_search,
)

api_router = APIRouter()


api_router.include_router(
    semantic_search.router, prefix="/semantic-search", tags=["Semantic Search"]
)

# ── Core & Standalone Routers ──────────────────────────────
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(
#     embedding.router, prefix="/embedding_model", tags=["Embedding Model"]
# )
api_router.include_router(
    graph_router.router, prefix="/graph", tags=["Knowledge Graph"]
)

# ── Public Routes (accessible without auth) ─────────────────
public_router = APIRouter()
public_router.include_router(cv.public_router, prefix="/cvs", tags=["CV"])
public_router.include_router(job.public_router, prefix="/jobs", tags=["Jobs"])

api_router.include_router(public_router)

# ── Private / Authenticated Routes ─────────────────────────
private_router = APIRouter()
private_router.include_router(cv.private_router, prefix="/cvs", tags=["CV"])
private_router.include_router(job.private_router, prefix="/jobs", tags=["Jobs"])
private_router.include_router(
    applicant.router, prefix="/applicants", tags=["Applicant Management"]
)
private_router.include_router(education.router, prefix="/education", tags=["Education"])
private_router.include_router(
    experience.router, prefix="/experience", tags=["Experience"]
)
private_router.include_router(data.router, prefix="/jd/data", tags=["JD Data Crawling"])
private_router.include_router(
    application.router, prefix="/applications", tags=["Applications Tracking"]
)

api_router.include_router(private_router)
