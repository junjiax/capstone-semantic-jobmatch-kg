from fastapi import APIRouter

router = APIRouter(tags=["Job"])

@router.get("/")
def health_check():
    return {"status": "activate", "message": "API is running successfully."}
