from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db


router = APIRouter(
    prefix="/hotspots",
    tags=["Hotspots"],
)


@router.get("")
def get_hotspots(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = text("""
        SELECT
            ward_number,
            category,
            complaint_count,
            active_months,
            first_complaint,
            last_complaint,
            avg_severity,
            unresolved_count,
            volume_score,
            persistence_score,
            severity_score,
            hotspot_score
        FROM hotspot_results
        ORDER BY hotspot_score DESC
        LIMIT :limit
    """)

    rows = db.execute(
        query,
        {"limit": limit}
    ).mappings().all()

    return {
        "count": len(rows),
        "results": [dict(row) for row in rows]
    }