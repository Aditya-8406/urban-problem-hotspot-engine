from fastapi import APIRouter

router = APIRouter(prefix="/relationships", tags=["relationships"])

@router.get("/")
def relationships():
    return {"items": []}
