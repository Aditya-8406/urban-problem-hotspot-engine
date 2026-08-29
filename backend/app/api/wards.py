from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db


router = APIRouter(
    prefix="/wards",
    tags=["Wards"],
)


@router.get("")
def get_wards(
    db: Session = Depends(get_db),
):
    query = text("""
        WITH hotspot_summary AS (
            SELECT
                ward_number,
                COUNT(*) AS hotspot_count,
                SUM(complaint_count) AS analyzed_complaint_count,
                MAX(hotspot_score) AS max_hotspot_score
            FROM hotspot_results
            GROUP BY ward_number
        ),

        priority_ranked AS (
            SELECT
                ward_number,
                category,
                municipal_priority_score,
                priority_level,
                ROW_NUMBER() OVER (
                    PARTITION BY ward_number
                    ORDER BY municipal_priority_score DESC
                ) AS rn
            FROM municipal_explanations
        )

        SELECT
            w.ward_number,
            w.name,
            ST_AsGeoJSON(w.geom)::json AS geometry,

            COALESCE(hs.analyzed_complaint_count, 0)
                AS analyzed_complaint_count,

            COALESCE(hs.hotspot_count, 0)
                AS hotspot_count,

            COALESCE(hs.max_hotspot_score, 0)
                AS max_hotspot_score,

            COALESCE(pr.municipal_priority_score, 0)
                AS highest_priority_score,

            pr.priority_level AS highest_priority_level,

            pr.category AS top_priority_category

        FROM wards w

        LEFT JOIN hotspot_summary hs
            ON hs.ward_number = w.ward_number

        LEFT JOIN priority_ranked pr
            ON pr.ward_number = w.ward_number
           AND pr.rn = 1

        ORDER BY w.ward_number;
    """)

    rows = db.execute(query).mappings().all()

    return {
        "count": len(rows),
        "results": [dict(row) for row in rows]
    }