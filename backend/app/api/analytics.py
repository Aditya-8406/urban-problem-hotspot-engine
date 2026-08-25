from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/")
def analytics():
    return {"status": "not implemented"}
