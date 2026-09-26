from typing import List


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from torch import embedding
from app.api.deps import get_db, get_current_user
from app.api.v1.schemas.response import ResponseSchema

from app.services.embedding import *
from app.services.cv import *

router = APIRouter()


@router.get(
    "/info",
    summary="Get Model Information And Status",
    description="Get model information such as loaded status and device",
)
async def model_info():
    return ResponseSchema(
        success=True,
        message="Model information retrieved successfully",
        data={
            "model_loaded": model_loaded(),
            "device": "cuda" if model_loaded() else "cpu",
        },
    )


@router.post(
    "/execute",
    summary="Validate CV-Job Match",
    description="Calculate and validate the semantic similarity between a CV and a Job posting",
)
async def validate_match(
    cv_id: int,
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return ResponseSchema(
        success=True,
        message="Similarity score calculated successfully",
        data={
            "cv_id": cv_id,
            "job_id": job_id,
            "match_result": (match_job_result_service(db, current_user, cv_id, job_id)),
        },
    )
