from fastapi import APIRouter

router = APIRouter(tags=["Profile"])


@router.get("/")
def health_check():
    return {"status": "activate", "message": "Profile API is running successfully."}
