from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db


router = APIRouter(
    prefix="/roads",
    tags=["Roads"],
)


@router.get("")
def list_roads(
    limit: int = Query(default=50, ge=1, le=500),
    ward_number: int | None = Query(default=None),
    priority_level: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = text("""
        SELECT
            road_segment_id,
            ward_number,
            segment_name,
            osm_name,
            highway,
            length_m,
            complaint_count,
            active_months,
            avg_severity,
            unresolved_count,
            volume_score,
            persistence_score,
            severity_score,
            unresolved_score,
            confidence_score,
            road_priority_score,
            priority_level,
            explanation,
            ST_AsGeoJSON(geom)::json AS geometry
        FROM road_priority_results
        WHERE
            (:ward_number IS NULL OR ward_number = :ward_number)
            AND (:priority_level IS NULL OR priority_level = :priority_level)
        ORDER BY road_priority_score DESC
        LIMIT :limit
    """)

    rows = db.execute(
        query,
        {
            "limit": limit,
            "ward_number": ward_number,
            "priority_level": priority_level,
        },
    ).mappings().all()

    return {
        "count": len(rows),
        "results": [dict(row) for row in rows],
    }


@router.get("/priority")
def road_priority(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = text("""
        SELECT
            road_segment_id,
            ward_number,
            segment_name,
            osm_name,
            highway,
            length_m,
            complaint_count,
            active_months,
            avg_severity,
            unresolved_count,
            road_priority_score,
            priority_level,
            explanation,
            ST_AsGeoJSON(geom)::json AS geometry
        FROM road_priority_results
        ORDER BY road_priority_score DESC
        LIMIT :limit
    """)

    rows = db.execute(
        query,
        {"limit": limit},
    ).mappings().all()

    return {
        "count": len(rows),
        "results": [dict(row) for row in rows],
    }


@router.get("/priority/{ward_number}")
def road_priority_by_ward(
    ward_number: int,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = text("""
        SELECT
            road_segment_id,
            ward_number,
            segment_name,
            osm_name,
            highway,
            length_m,
            complaint_count,
            active_months,
            avg_severity,
            unresolved_count,
            road_priority_score,
            priority_level,
            explanation,
            ST_AsGeoJSON(geom)::json AS geometry
        FROM road_priority_results
        WHERE ward_number = :ward_number
        ORDER BY road_priority_score DESC
        LIMIT :limit
    """)

    rows = db.execute(
        query,
        {
            "ward_number": ward_number,
            "limit": limit,
        },
    ).mappings().all()

    return {
        "ward_number": ward_number,
        "count": len(rows),
        "results": [dict(row) for row in rows],
    }


@router.get("/map")
def road_map(
    ward_number: int | None = Query(default=None),
    priority_level: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = text("""
        SELECT
            road_segment_id,
            ward_number,
            segment_name,
            osm_name,
            highway,
            length_m,
            complaint_count,
            active_months,
            avg_severity,
            unresolved_count,
            road_priority_score,
            priority_level,
            explanation,
            ST_AsGeoJSON(geom)::json AS geometry
        FROM road_priority_results
        WHERE
            geom IS NOT NULL
            AND (:ward_number IS NULL OR ward_number = :ward_number)
            AND (:priority_level IS NULL OR priority_level = :priority_level)
        ORDER BY road_priority_score DESC
    """)

    rows = db.execute(
        query,
        {
            "ward_number": ward_number,
            "priority_level": priority_level,
        },
    ).mappings().all()

    features = []

    for row in rows:
        feature = {
            "type": "Feature",
            "geometry": row["geometry"],
            "properties": {
                "road_segment_id": row["road_segment_id"],
                "ward_number": row["ward_number"],
                "segment_name": row["segment_name"],
                "osm_name": row["osm_name"],
                "highway": row["highway"],
                "length_m": row["length_m"],
                "complaint_count": row["complaint_count"],
                "active_months": row["active_months"],
                "avg_severity": row["avg_severity"],
                "unresolved_count": row["unresolved_count"],
                "road_priority_score": row["road_priority_score"],
                "priority_level": row["priority_level"],
                "explanation": row["explanation"],
            },
        }

        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
    }