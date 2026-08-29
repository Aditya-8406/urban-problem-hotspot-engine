from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db


router = APIRouter(
    prefix="/priority",
    tags=["Priority"],
)


@router.get("")
def get_priority(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = text("""
        SELECT
            ward_number,
            ward_name,
            category,
            complaint_count,
            active_months,
            avg_severity,
            unresolved_count,
            connected_category,
            connection_score,
            municipal_priority_score,
            priority_level,

            CONCAT(
                'Ward ', ward_number,
                ' (', COALESCE(ward_name, 'Unknown Ward'), ') has a ',
                category,
                ' hotspot with ',
                complaint_count,
                ' complaints recurring across ',
                active_months,
                ' months. ',
                hotspot_reason,
                '. ',
                persistence_reason,
                '. ',
                resolution_reason,
                '. ',
                CASE
                    WHEN connected_category IS NOT NULL
                    THEN CONCAT(
                        'It is repeatedly associated with ',
                        connected_category,
                        ' (connection score ',
                        ROUND(connection_score::numeric, 2),
                        '). '
                    )
                    ELSE ''
                END,
                'Municipal priority: ',
                priority_level,
                ' (',
                ROUND(municipal_priority_score::numeric, 2),
                ').'
            ) AS explanation,

            recommended_action

        FROM municipal_explanations
        ORDER BY municipal_priority_score DESC
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


@router.get("/{ward_number}")
def get_ward_priority(
    ward_number: int,
    db: Session = Depends(get_db),
):
    query = text("""
        SELECT
            ward_number,
            ward_name,
            category,
            complaint_count,
            active_months,
            avg_severity,
            unresolved_count,
            connected_category,
            connection_score,
            municipal_priority_score,
            priority_level,

            CONCAT(
                'Ward ', ward_number,
                ' (', COALESCE(ward_name, 'Unknown Ward'), ') has a ',
                category,
                ' hotspot with ',
                complaint_count,
                ' complaints recurring across ',
                active_months,
                ' months. ',
                hotspot_reason,
                '. ',
                persistence_reason,
                '. ',
                resolution_reason,
                '. ',
                CASE
                    WHEN connected_category IS NOT NULL
                    THEN CONCAT(
                        'It is repeatedly associated with ',
                        connected_category,
                        ' (connection score ',
                        ROUND(connection_score::numeric, 2),
                        '). '
                    )
                    ELSE ''
                END,
                'Municipal priority: ',
                priority_level,
                ' (',
                ROUND(municipal_priority_score::numeric, 2),
                ').'
            ) AS explanation,

            recommended_action

        FROM municipal_explanations
        WHERE ward_number = :ward_number
        ORDER BY municipal_priority_score DESC
    """)

    rows = db.execute(
        query,
        {"ward_number": ward_number}
    ).mappings().all()

    return {
        "ward_number": ward_number,
        "count": len(rows),
        "results": [dict(row) for row in rows]
    }