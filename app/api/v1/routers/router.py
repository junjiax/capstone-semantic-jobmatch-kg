from fastapi import APIRouter
from app.api.v1.routers import (
    applicant,
    cv,
    education,
    experience,
    health,
    job,
    skill,
    users,
    auth,
    embedding,
    application_router as application,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])

# Public routes (accessible to all users)
public_router = APIRouter()
public_router.include_router(cv.public_router, prefix="/cvs", tags=["CV"])
public_router.include_router(job.public_router, prefix="/jobs", tags=["Jobs"])

# Private routes (accessible only to authenticated users)
private_router = APIRouter()
private_router.include_router(cv.private_router, prefix="/cvs", tags=["CV"])
private_router.include_router(embedding.router, prefix="/calculate_similarity", tags=["Calculate Similarity"])
private_router.include_router(applicant.router, prefix="/applicants", tags=["Applicant Management"])
private_router.include_router(education.router, prefix="/education", tags=["Education"])
private_router.include_router(experience.router, prefix="/experience", tags=["Experience"])
private_router.include_router(skill.router, prefix="/skills", tags=["Skills"])
private_router.include_router(application.router, prefix="/applications", tags=["Applications Tracking"])
private_router.include_router(job.private_router, prefix="/jobs", tags=["Jobs"])

api_router.include_router(public_router)
api_router.include_router(private_router)
