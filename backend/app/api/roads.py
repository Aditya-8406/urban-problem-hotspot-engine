from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db


router = APIRouter(
    prefix="/roads",
    tags=["Roads"],
)


# ---------------------------------------------------------
# Helper: relationship context for a road
# ---------------------------------------------------------

def get_relationship_context(
    db: Session,
    road_segment_ids: list[int],
):
    if not road_segment_ids:
        return {}

    query = text("""
        SELECT
            road_segment_id,
            ward_number,
            category_a,
            category_b,
            co_occurring_months,
            co_occurrence_strength,
            relationship_score
        FROM road_relationship_context
        WHERE road_segment_id = ANY(:road_ids)
        ORDER BY road_segment_id, relationship_score DESC
    """)

    rows = db.execute(
        query,
        {"road_ids": road_segment_ids},
    ).mappings().all()

    relationships = {}

    for row in rows:
        road_id = row["road_segment_id"]

        if road_id not in relationships:
            relationships[road_id] = []

        relationships[road_id].append({
            "category_a": row["category_a"],
            "category_b": row["category_b"],
            "co_occurring_months": row["co_occurring_months"],
            "co_occurrence_strength": row["co_occurrence_strength"],
            "relationship_score": row["relationship_score"],
        })

    return relationships


# ---------------------------------------------------------
# GET /roads
# ---------------------------------------------------------

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

    road_ids = [row["road_segment_id"] for row in rows]
    relationship_context = get_relationship_context(db, road_ids)

    results = []

    for row in rows:
        road_id = row["road_segment_id"]
        relationships = relationship_context.get(road_id, [])

        result = dict(row)

        result["has_problem_relationship"] = bool(relationships)
        result["relationship_count"] = len(relationships)
        result["relationships"] = relationships

        results.append(result)

    return {
        "count": len(results),
        "results": results,
    }


# ---------------------------------------------------------
# GET /roads/priority
# ---------------------------------------------------------

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

    road_ids = [row["road_segment_id"] for row in rows]
    relationship_context = get_relationship_context(db, road_ids)

    results = []

    for row in rows:
        road_id = row["road_segment_id"]
        relationships = relationship_context.get(road_id, [])

        result = dict(row)

        result["has_problem_relationship"] = bool(relationships)
        result["relationship_count"] = len(relationships)
        result["relationships"] = relationships

        results.append(result)

    return {
        "count": len(results),
        "results": results,
    }


# ---------------------------------------------------------
# GET /roads/priority/{ward_number}
# ---------------------------------------------------------

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

    road_ids = [row["road_segment_id"] for row in rows]
    relationship_context = get_relationship_context(db, road_ids)

    results = []

    for row in rows:
        road_id = row["road_segment_id"]
        relationships = relationship_context.get(road_id, [])

        result = dict(row)

        result["has_problem_relationship"] = bool(relationships)
        result["relationship_count"] = len(relationships)
        result["relationships"] = relationships

        results.append(result)

    return {
        "ward_number": ward_number,
        "count": len(results),
        "results": results,
    }


# ---------------------------------------------------------
# GET /roads/map
# ---------------------------------------------------------

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

    road_ids = [row["road_segment_id"] for row in rows]
    relationship_context = get_relationship_context(db, road_ids)

    features = []

    for row in rows:
        road_id = row["road_segment_id"]
        relationships = relationship_context.get(road_id, [])

        properties = {
            "road_segment_id": road_id,
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

            # Relationship intelligence
            "has_problem_relationship": bool(relationships),
            "relationship_count": len(relationships),
            "relationships": relationships,
        }

        features.append({
            "type": "Feature",
            "geometry": row["geometry"],
            "properties": properties,
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


# ---------------------------------------------------------
# GET /roads/{road_segment_id}
# ---------------------------------------------------------

@router.get("/{road_segment_id}")
def get_road(
    road_segment_id: int,
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
        WHERE road_segment_id = :road_segment_id
    """)

    row = db.execute(
        query,
        {"road_segment_id": road_segment_id},
    ).mappings().first()

    if not row:
        return {
            "road_segment_id": road_segment_id,
            "found": False,
        }

    relationships = get_relationship_context(
        db,
        [road_segment_id],
    ).get(road_segment_id, [])

    result = dict(row)

    result["found"] = True
    result["has_problem_relationship"] = bool(relationships)
    result["relationship_count"] = len(relationships)
    result["relationships"] = relationships

    return result