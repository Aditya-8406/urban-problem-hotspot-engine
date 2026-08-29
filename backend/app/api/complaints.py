from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db


router = APIRouter(
    prefix="/complaints",
    tags=["Complaints"],
)


@router.get("")
def list_complaints(
    limit: int = Query(default=50, ge=1, le=500),
    ward_number: int | None = Query(default=None),
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    severity: int | None = Query(default=None, ge=1, le=5),
    db: Session = Depends(get_db),
):
    query = text("""
        SELECT
            complaint_id,
            category,
            description,
            complaint_date,
            resolution_date,
            latitude,
            longitude,
            ward_number,
            spatial_ward_number,
            severity,
            status,
            data_type,
            source,
            location_method,
            location_confidence,
            ST_AsGeoJSON(geom)::json AS geometry
        FROM complaints
        WHERE
            complaint_date IS NOT NULL
            AND complaint_date <= CURRENT_TIMESTAMP

            AND (
                :ward_number IS NULL
                OR ward_number = :ward_number
            )

            AND (
                :category IS NULL
                OR category = :category
            )

            AND (
                :status IS NULL
                OR status = :status
            )

            AND (
                :severity IS NULL
                OR severity = :severity
            )

        ORDER BY complaint_date DESC NULLS LAST
        LIMIT :limit
    """)

    rows = db.execute(
        query,
        {
            "limit": limit,
            "ward_number": ward_number,
            "category": category,
            "status": status,
            "severity": severity,
        },
    ).mappings().all()

    return {
        "count": len(rows),
        "results": [dict(row) for row in rows],
    }