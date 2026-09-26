from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.api.v1.schemas import ResponseSchema, CVResponse
from app.api.v1.schemas.cv import CVFilter
from app.services import cv as cv_services
from app.models import User

public_router = APIRouter()
private_router = APIRouter()

# 1. UPLOAD CV
@private_router.post(
    "/upload",
    response_model=ResponseSchema[CVResponse],
    summary="Upload CV",
    description="Upload a new CV file (PDF, DOCX) and save metadata."
)
async def upload_cv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Service xử lý lưu file vật lý và tạo record trong DB
    new_cv = cv_services.upload_and_create_cv(
        db=db, 
        file=file, 
        user_id=current_user.Id
    )
    
    return ResponseSchema[CVResponse](
        success=True,
        message="CV uploaded successfully",
        data=new_cv
    )

# 2. CV (LIST ALL WITH FILTERS)
@private_router.get(
    "",
    response_model=ResponseSchema[List[CVResponse]],
    summary="List all CVs",
    description="Get all CVs. HR sees everything, Applicants see only their own."
)
async def get_cvs(
    filters: CVFilter = Depends(), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cv_list = cv_services.get_user_cvs(
        db=db, 
        current_user=current_user, 
        filters=filters
    )
    
    return ResponseSchema[List[CVResponse]](
        success=True,
        message="Fetched all CVs successfully",
        data=cv_list
    )

# 3. GET CV BY ID (WITH RBAC)
@private_router.get(
    "/{cv_id}",
    response_model=ResponseSchema[CVResponse],
    summary="Get CV Details",
    description="HR can access any CV. Applicants can only access their own CV."
)
async def get_cv_details(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cv_data = cv_services.get_cv_details(
        db=db, 
        cv_id=cv_id, 
        current_user=current_user
    )
    
    return ResponseSchema[CVResponse](
        success=True,
        message="Fetched CV details successfully",
        data=cv_data
    )

# 4. DOWNLOAD CV
@private_router.get(
    "/{cv_id}/download",
    summary="Download Original CV",
    description="Download the original uploaded file by CV ID."
)
async def download_cv(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    file_path = cv_services.get_cv_file_path(
        db=db,
        cv_id=cv_id,
        current_user=current_user,
    )
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(path=file_path, filename=f"CV_{cv_id}.pdf")

# 5. TRIGGER PARSING
@private_router.post(
    "/{cv_id}/parse-trigger",
    response_model=ResponseSchema,
    summary="Trigger CV Parsing",
    description="Trích xuất và lưu thông tin học vấn, kinh nghiệm, kỹ năng từ file CV."
)
async def trigger_parsing(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cv_services.run_cv_parsing_task(
        db=db,
        cv_id=cv_id,
        current_user=current_user
    )

    return ResponseSchema(
        success=True,
        message="CV parsed and saved successfully",
        data=None
    )