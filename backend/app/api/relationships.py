from fastapi import APIRouter, Depends, HTTPException, Query
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
    """
    Return strongest problem relationships across wards.
    """

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


@router.get("/ward/{ward_number}")
def get_ward_relationships(
    ward_number: int,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Return problem relationships detected within a specific ward.
    """

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
        WHERE ward_number = :ward_number
        ORDER BY connection_score DESC
        LIMIT :limit
    """)

    rows = db.execute(
        query,
        {
            "ward_number": ward_number,
            "limit": limit,
        }
    ).mappings().all()

    return {
        "ward_number": ward_number,
        "count": len(rows),
        "results": [dict(row) for row in rows]
    }


@router.get("/road/{road_segment_id}")
def get_road_relationships(
    road_segment_id: int,
    db: Session = Depends(get_db),
):
    """
    Return problem relationships associated with a road segment.

    A relationship is attached to a road only when that road has
    complaints belonging to both categories of the detected
    ward-level relationship.
    """

    query = text("""
        SELECT
            r.road_segment_id,
            r.ward_number,

            r.category_a,
            r.category_b,

            r.co_occurring_months,
            r.co_occurrence_strength,
            r.relationship_score

        FROM road_relationship_context r
        WHERE r.road_segment_id = :road_segment_id
        ORDER BY r.relationship_score DESC
    """)

    rows = db.execute(
        query,
        {"road_segment_id": road_segment_id}
    ).mappings().all()

    if not rows:
        return {
            "road_segment_id": road_segment_id,
            "has_problem_relationship": False,
            "count": 0,
            "relationships": []
        }

    return {
        "road_segment_id": road_segment_id,
        "ward_number": rows[0]["ward_number"],
        "has_problem_relationship": True,
        "count": len(rows),
        "relationships": [dict(row) for row in rows]
    }