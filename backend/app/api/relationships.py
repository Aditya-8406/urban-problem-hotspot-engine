from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db


router = APIRouter(
    prefix="/relationships",
    tags=["Relationships"],
)


@router.get("")
def get_relationships(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = text("""
        SELECT
            ward_number,
            category_a,
            category_b,
            co_occurring_months,
            co_occurrence_strength,
            category_a_active_months,
            category_b_active_months,
            connection_score
        FROM problem_connectivity
        ORDER BY connection_score DESC
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