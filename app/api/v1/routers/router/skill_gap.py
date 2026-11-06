from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def health_check():
    return {"status": "activate", "message": "Job API is running successfully."}
