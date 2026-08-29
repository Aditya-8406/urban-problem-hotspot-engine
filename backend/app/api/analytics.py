from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get("")
def get_analytics(
    db: Session = Depends(get_db),
):
    query = text("""
        WITH valid_complaints AS (
            SELECT *
            FROM complaints
            WHERE complaint_date IS NOT NULL
              AND complaint_date <= CURRENT_TIMESTAMP
        ),

        priority_summary AS (
            SELECT
                COUNT(*) FILTER (
                    WHERE priority_level = 'CRITICAL'
                ) AS critical_priorities,

                COUNT(*) FILTER (
                    WHERE priority_level = 'HIGH'
                ) AS high_priorities,

                COUNT(*) FILTER (
                    WHERE priority_level = 'MEDIUM'
                ) AS medium_priorities,

                COUNT(*) FILTER (
                    WHERE priority_level = 'LOW'
                ) AS low_priorities

            FROM municipal_explanations
        )

        SELECT
            (SELECT COUNT(*) FROM valid_complaints)
                AS total_complaints,

            (
                SELECT COUNT(DISTINCT COALESCE(
                    spatial_ward_number,
                    ward_number
                ))
                FROM valid_complaints
                WHERE COALESCE(
                    spatial_ward_number,
                    ward_number
                ) IS NOT NULL
            ) AS wards_with_complaints,

            (
                SELECT COUNT(DISTINCT category)
                FROM valid_complaints
            ) AS problem_categories,

            ps.critical_priorities,
            ps.high_priorities,
            ps.medium_priorities,
            ps.low_priorities,

            (
                SELECT COUNT(*)
                FROM problem_connectivity
            ) AS problem_relationships,

            (
                SELECT COUNT(*)
                FROM hotspot_results
            ) AS hotspot_count

        FROM priority_summary ps;
    """)

    row = db.execute(query).mappings().one()

    return dict(row)