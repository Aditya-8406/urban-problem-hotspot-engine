from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.priority import router as priority_router
from app.api.hotspots import router as hotspots_router
from app.api.relationships import router as relationships_router
from app.api.analytics import router as analytics_router
from app.api.wards import router as wards_router
from app.api.complaints import router as complaints_router
from app.api.urban import router as urban_router
from app.api.roads import router as roads_router


app = FastAPI(
    title="Urban Problem Hotspot Engine",
    version="0.2.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# ============================================================
# API ROUTERS
# ============================================================

app.include_router(priority_router)
app.include_router(hotspots_router)
app.include_router(relationships_router)
app.include_router(analytics_router)
app.include_router(wards_router)
app.include_router(complaints_router)
app.include_router(urban_router)
app.include_router(roads_router)