from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import get_db


router = APIRouter(
    prefix="/urban",
    tags=["Urban Priority"],
)


# ============================================================
# HELPER: RECOMMENDATION ENGINE
# ============================================================

def build_recommendation(road, patterns):
    """
    Convert the evidence collected for a road into a
    municipality-facing recommended action.
    """

    score = float(road["urban_priority_score"] or 0)

    complaint_count = int(road["complaint_count"] or 0)
    unresolved_count = int(road["unresolved_count"] or 0)

    strong_relationships = int(
        road["strong_relationships"] or 0
    )

    moderate_relationships = int(
        road["moderate_relationships"] or 0
    )

    if complaint_count > 0:
        unresolved_ratio = unresolved_count / complaint_count
    else:
        unresolved_ratio = 0

    # --------------------------------------------------------
    # Pattern matching
    # --------------------------------------------------------

    categories = set()

    for pattern in patterns:
        categories.add(pattern["source_category"])
        categories.add(pattern["target_category"])

    # --------------------------------------------------------
    # ROAD CONDITION
    # --------------------------------------------------------

    if (
        "Pothole" in categories
        and "Damaged Road" in categories
    ):
        action = "ROAD SURFACE INSPECTION + REPAIR"
        action_category = "ROAD_REPAIR"

        reason = (
            "Connected pothole and damaged-road complaints "
            "indicate a persistent road-surface problem. "
            "The road should be inspected for pavement failure "
            "and repaired according to the observed damage."
        )

        confidence = 0.92

    # --------------------------------------------------------
    # DRAINAGE / WATERLOGGING
    # --------------------------------------------------------

    elif (
        "Waterlogging" in categories
        and "Drainage" in categories
    ):
        action = "DRAINAGE INSPECTION + DESILTING"
        action_category = "DRAINAGE"

        reason = (
            "Repeated drainage and waterlogging complaints "
            "are spatially and temporally connected. "
            "Inspect drainage capacity, blockage and "
            "desilting requirements."
        )

        confidence = 0.91

    # --------------------------------------------------------
    # GARBAGE / ILLEGAL DUMPING
    # --------------------------------------------------------

    elif (
        "Illegal Dumping" in categories
        and "Garbage Collection" in categories
    ):
        action = "WASTE COLLECTION + DUMPING INSPECTION"
        action_category = "WASTE_MANAGEMENT"

        reason = (
            "Connected garbage-collection and illegal-dumping "
            "complaints indicate a recurring waste-management "
            "problem. Increase collection attention and inspect "
            "the location for unauthorized dumping."
        )

        confidence = 0.89

    # --------------------------------------------------------
    # STREETLIGHT / SIDEWALK
    # --------------------------------------------------------

    elif (
        "Damaged Sidewalk" in categories
        and "Streetlight" in categories
    ):
        action = "STREETLIGHT + SIDEWALK SAFETY INSPECTION"
        action_category = "PUBLIC_SAFETY"

        reason = (
            "Connected damaged-sidewalk and streetlight complaints "
            "indicate a combined pedestrian-safety issue. "
            "Inspect both the lighting asset and pedestrian path."
        )

        confidence = 0.87

    # --------------------------------------------------------
    # WATER SUPPLY / LEAKAGE
    # --------------------------------------------------------

    elif (
        "Water Leakage" in categories
        and "Water Supply" in categories
    ):
        action = "WATER NETWORK INSPECTION"
        action_category = "WATER_INFRASTRUCTURE"

        reason = (
            "Connected water-leakage and water-supply complaints "
            "suggest a possible water-network problem. "
            "Inspect the local supply infrastructure and "
            "identify leakage or pressure-related issues."
        )

        confidence = 0.88

    # --------------------------------------------------------
    # DRAINAGE RELATED FALLBACK
    # --------------------------------------------------------

    elif "Drainage" in categories:
        action = "DRAINAGE INSPECTION"
        action_category = "DRAINAGE"

        reason = (
            "Drainage complaints are present in the connected "
            "problem network. Inspect the nearby drainage "
            "infrastructure for blockage, capacity or maintenance "
            "issues."
        )

        confidence = 0.78

    # --------------------------------------------------------
    # ROAD RELATED FALLBACK
    # --------------------------------------------------------

    elif (
        "Pothole" in categories
        or "Damaged Road" in categories
        or "Damaged Sidewalk" in categories
    ):
        action = "ROAD / PUBLIC-REALM INSPECTION"
        action_category = "ROAD_INSPECTION"

        reason = (
            "The connected complaints indicate deterioration "
            "of road or pedestrian infrastructure. Conduct a "
            "field inspection to determine the required repair."
        )

        confidence = 0.72

    # --------------------------------------------------------
    # GENERAL FALLBACK
    # --------------------------------------------------------

    else:
        action = "FIELD INSPECTION"
        action_category = "GENERAL_INSPECTION"

        reason = (
            "The road has sufficient complaint and priority "
            "evidence to justify a municipal field inspection."
        )

        confidence = 0.60

    # --------------------------------------------------------
    # Adjust confidence using relationship evidence
    # --------------------------------------------------------

    if strong_relationships >= 2:
        confidence += 0.03
    elif strong_relationships == 1:
        confidence += 0.02
    elif moderate_relationships >= 3:
        confidence += 0.01

    confidence = min(round(confidence, 2), 0.99)

    # --------------------------------------------------------
    # Urgency
    # --------------------------------------------------------

    if score >= 90:
        urgency = "CRITICAL"
    elif score >= 75:
        urgency = "HIGH"
    elif score >= 55:
        urgency = "MEDIUM"
    else:
        urgency = "LOW"

    if unresolved_ratio >= 0.80 and urgency == "MEDIUM":
        urgency = "HIGH"

    # --------------------------------------------------------
    # Evidence summary
    # --------------------------------------------------------

    dominant_patterns = []

    for pattern in patterns[:5]:
        dominant_patterns.append({
            "source_category": pattern["source_category"],
            "target_category": pattern["target_category"],
            "relationship_count": pattern["relationship_count"],
            "strong_relationships": pattern["strong_relationships"],
            "avg_relationship_score": pattern["avg_relationship_score"],
        })

    return {
        "recommended_action": action,
        "action_category": action_category,
        "confidence": confidence,
        "urgency": urgency,
        "reason": reason,
        "evidence": {
            "complaints": complaint_count,
            "unresolved": unresolved_count,
            "unresolved_ratio": round(unresolved_ratio, 2),
            "strong_relationships": strong_relationships,
            "moderate_relationships": moderate_relationships,
            "dominant_patterns": dominant_patterns,
        },
    }


# ============================================================
# 1. URBAN PRIORITY RANKING
# ============================================================

@router.get("/priority")
def urban_priority(
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
            highway,
            complaint_count,
            active_months,
            avg_severity,
            unresolved_count,
            road_priority_score,
            relationship_count,
            strong_relationships,
            moderate_relationships,
            weak_relationships,
            avg_relationship_score,
            relationship_risk_score,
            relationship_bonus_score,
            urban_priority_score,
            priority_level,
            explanation
        FROM urban_priority_results
        WHERE
            (:ward_number IS NULL OR ward_number = :ward_number)
            AND (
                :priority_level IS NULL
                OR priority_level = :priority_level
            )
        ORDER BY urban_priority_score DESC
        LIMIT :limit
    """)

    rows = db.execute(
        query,
        {
            "ward_number": ward_number,
            "priority_level": priority_level,
            "limit": limit,
        },
    ).mappings().all()

    return {
        "count": len(rows),
        "results": [dict(row) for row in rows],
    }


# ============================================================
# 2. ROAD PRIORITY DETAIL
# ============================================================

@router.get("/priority/{road_segment_id}")
def road_priority_detail(
    road_segment_id: int,
    db: Session = Depends(get_db),
):
    query = text("""
        SELECT
            road_segment_id,
            ward_number,
            segment_name,
            highway,
            complaint_count,
            active_months,
            avg_severity,
            unresolved_count,
            road_priority_score,
            relationship_count,
            strong_relationships,
            moderate_relationships,
            weak_relationships,
            avg_relationship_score,
            relationship_risk_score,
            relationship_bonus_score,
            urban_priority_score,
            priority_level,
            explanation
        FROM urban_priority_results
        WHERE road_segment_id = :road_segment_id
        LIMIT 1
    """)

    row = db.execute(
        query,
        {"road_segment_id": road_segment_id},
    ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Road segment not found",
        )

    return dict(row)


# ============================================================
# 3. ROAD RELATIONSHIPS
# ============================================================

@router.get("/priority/{road_segment_id}/relationships")
def road_relationships(
    road_segment_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = text("""
        WITH road_complaints AS (
            SELECT DISTINCT
                complaint_id
            FROM road_complaint_assignments
            WHERE
                road_segment_id = :road_segment_id
                AND match_confidence <> 'UNMATCHED'
        )

        SELECT
            cr.source_complaint_id,
            cr.target_complaint_id,
            cr.source_category,
            cr.target_category,
            a.ward_number,
            cr.distance_m,
            cr.time_difference_days,
            cr.source_severity,
            cr.target_severity,
            cr.spatial_score,
            cr.temporal_score,
            cr.severity_score,
            cr.relationship_score,
            cr.relationship_type
        FROM complaint_relationships cr
        JOIN road_complaint_assignments a
          ON a.complaint_id = cr.source_complaint_id
        WHERE
            cr.source_complaint_id IN (
                SELECT complaint_id
                FROM road_complaints
            )
            AND cr.target_complaint_id IN (
                SELECT complaint_id
                FROM road_complaints
            )
        ORDER BY cr.relationship_score DESC
        LIMIT :limit
    """)

    rows = db.execute(
        query,
        {
            "road_segment_id": road_segment_id,
            "limit": limit,
        },
    ).mappings().all()

    road = db.execute(
        text("""
            SELECT
                road_segment_id,
                ward_number,
                segment_name
            FROM urban_priority_results
            WHERE road_segment_id = :road_segment_id
            LIMIT 1
        """),
        {"road_segment_id": road_segment_id},
    ).mappings().first()

    if not road:
        raise HTTPException(
            status_code=404,
            detail="Road segment not found",
        )

    return {
        "road_segment_id": road_segment_id,
        "ward_number": road["ward_number"],
        "segment_name": road["segment_name"],
        "count": len(rows),
        "relationships": [dict(row) for row in rows],
    }


# ============================================================
# 4. ROAD RECOMMENDATION
# ============================================================

@router.get("/priority/{road_segment_id}/recommendation")
def road_recommendation(
    road_segment_id: int,
    db: Session = Depends(get_db),
):
    road_query = text("""
        SELECT *
        FROM urban_priority_results
        WHERE road_segment_id = :road_segment_id
        LIMIT 1
    """)

    road = db.execute(
        road_query,
        {"road_segment_id": road_segment_id},
    ).mappings().first()

    if not road:
        raise HTTPException(
            status_code=404,
            detail="Road segment not found",
        )

    pattern_query = text("""
        WITH road_complaints AS (
            SELECT DISTINCT
                complaint_id
            FROM road_complaint_assignments
            WHERE
                road_segment_id = :road_segment_id
                AND match_confidence <> 'UNMATCHED'
        ),

        road_relationships AS (
            SELECT
                cr.source_category,
                cr.target_category,
                cr.relationship_score,
                cr.relationship_type
            FROM complaint_relationships cr
            WHERE
                cr.source_complaint_id IN (
                    SELECT complaint_id
                    FROM road_complaints
                )
                AND cr.target_complaint_id IN (
                    SELECT complaint_id
                    FROM road_complaints
                )
        )

        SELECT
            source_category,
            target_category,
            COUNT(*) AS relationship_count,
            COUNT(*) FILTER (
                WHERE relationship_type = 'STRONG'
            ) AS strong_relationships,
            ROUND(
                AVG(relationship_score)::numeric,
                2
            ) AS avg_relationship_score
        FROM road_relationships
        GROUP BY
            source_category,
            target_category
        ORDER BY
            relationship_count DESC,
            strong_relationships DESC,
            avg_relationship_score DESC
        LIMIT 5
    """)

    patterns = db.execute(
        pattern_query,
        {"road_segment_id": road_segment_id},
    ).mappings().all()

    recommendation = build_recommendation(
        road,
        patterns,
    )

    return {
        "road_segment_id": road["road_segment_id"],
        "ward_number": road["ward_number"],
        "segment_name": road["segment_name"],
        "priority_level": road["priority_level"],
        "urban_priority_score": road["urban_priority_score"],
        **recommendation,
    }


# ============================================================
# 5. WARD PRIORITY
# ============================================================

@router.get("/wards")
def urban_wards(
    limit: int = Query(default=50, ge=1, le=100),
    priority_level: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = text("""
        WITH ward_summary AS (
            SELECT
                ward_number,

                COUNT(*) AS total_roads,

                COUNT(*) FILTER (
                    WHERE priority_level = 'CRITICAL'
                ) AS critical_roads,

                COUNT(*) FILTER (
                    WHERE priority_level = 'HIGH'
                ) AS high_roads,

                COUNT(*) FILTER (
                    WHERE priority_level = 'MEDIUM'
                ) AS medium_roads,

                COUNT(*) FILTER (
                    WHERE priority_level = 'LOW'
                ) AS low_roads,

                SUM(complaint_count) AS total_complaints,

                SUM(unresolved_count) AS unresolved_complaints,

                ROUND(
                    AVG(avg_severity)::numeric,
                    2
                ) AS avg_severity,

                SUM(relationship_count) AS relationship_count,

                SUM(strong_relationships) AS strong_relationships,

                SUM(moderate_relationships) AS moderate_relationships,

                ROUND(
                    AVG(urban_priority_score)::numeric,
                    2
                ) AS avg_urban_priority,

                ROUND(
                    MAX(urban_priority_score)::numeric,
                    2
                ) AS max_urban_priority

            FROM urban_priority_results

            GROUP BY ward_number
        )

        SELECT
            ward_number,
            total_roads,
            critical_roads,
            high_roads,
            medium_roads,
            low_roads,
            total_complaints,
            unresolved_complaints,
            avg_severity,
            relationship_count,
            strong_relationships,
            moderate_relationships,
            avg_urban_priority,
            max_urban_priority,

            ROUND(
                (
                    avg_urban_priority * 0.60
                    +
                    CASE
                        WHEN total_complaints > 0
                        THEN (
                            unresolved_complaints::numeric
                            / total_complaints
                        ) * 100 * 0.25
                        ELSE 0
                    END
                    +
                    LEAST(
                        strong_relationships * 5,
                        15
                    )
                )::numeric,
                2
            ) AS ward_risk_score

        FROM ward_summary

        WHERE
            (
                :priority_level IS NULL
                OR (
                    CASE
                        WHEN max_urban_priority >= 90
                            THEN 'CRITICAL'
                        WHEN max_urban_priority >= 75
                            THEN 'HIGH'
                        WHEN max_urban_priority >= 55
                            THEN 'MEDIUM'
                        ELSE 'LOW'
                    END
                ) = :priority_level
            )

        ORDER BY ward_risk_score DESC

        LIMIT :limit
    """)

    rows = db.execute(
        query,
        {
            "priority_level": priority_level,
            "limit": limit,
        },
    ).mappings().all()

    results = []

    for row in rows:
        item = dict(row)

        if item["ward_risk_score"] >= 90:
            item["priority_level"] = "CRITICAL"
        elif item["ward_risk_score"] >= 70:
            item["priority_level"] = "HIGH"
        elif item["ward_risk_score"] >= 50:
            item["priority_level"] = "MEDIUM"
        else:
            item["priority_level"] = "LOW"

        results.append(item)

    return {
        "count": len(results),
        "wards": results,
    }


# ============================================================
# 6. ROAD PRIORITY MAP
# ============================================================

@router.get("/map")
def urban_priority_map(
    priority_level: str | None = Query(default=None),
    ward_number: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = text("""
        SELECT
            upr.road_segment_id,
            upr.ward_number,
            upr.segment_name,
            upr.highway,
            upr.complaint_count,
            upr.active_months,
            upr.avg_severity,
            upr.unresolved_count,
            upr.road_priority_score,
            upr.relationship_count,
            upr.strong_relationships,
            upr.moderate_relationships,
            upr.weak_relationships,
            upr.avg_relationship_score,
            upr.relationship_risk_score,
            upr.relationship_bonus_score,
            upr.urban_priority_score,
            upr.priority_level,
            upr.explanation,
            ST_AsGeoJSON(r.geom)::json AS geometry
        FROM urban_priority_results upr
        JOIN roads r
          ON r.road_segment_id = upr.road_segment_id
        WHERE
            (
                :priority_level IS NULL
                OR upr.priority_level = :priority_level
            )
            AND (
                :ward_number IS NULL
                OR upr.ward_number = :ward_number
            )
        ORDER BY upr.urban_priority_score DESC
    """)

    rows = db.execute(
        query,
        {
            "priority_level": priority_level,
            "ward_number": ward_number,
        },
    ).mappings().all()

    features = []

    for row in rows:
        properties = dict(row)
        geometry = properties.pop("geometry")

        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": properties,
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }


# ============================================================
# 7. GLOBAL PROBLEM NETWORKS
# ============================================================

@router.get("/network")
def problem_networks(
    limit: int = Query(default=50, ge=1, le=200),
    network_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = text("""
        SELECT
            category_a,
            category_b,
            relationship_count,
            strong_relationships,
            moderate_relationships,
            weak_relationships,
            avg_relationship_score,
            max_relationship_score,
            network_strength_score,
            network_type
        FROM problem_network_summary
        WHERE
            :network_type IS NULL
            OR network_type = :network_type
        ORDER BY
            network_strength_score DESC,
            relationship_count DESC
        LIMIT :limit
    """)

    rows = db.execute(
        query,
        {
            "network_type": network_type,
            "limit": limit,
        },
    ).mappings().all()

    return {
        "count": len(rows),
        "networks": [dict(row) for row in rows],
    }


# ============================================================
# 8. SINGLE GLOBAL NETWORK
# ============================================================

@router.get("/network/{category_a}/{category_b}")
def problem_network_detail(
    category_a: str,
    category_b: str,
    db: Session = Depends(get_db),
):
    query = text("""
        SELECT
            category_a,
            category_b,
            relationship_count,
            strong_relationships,
            moderate_relationships,
            weak_relationships,
            avg_relationship_score,
            max_relationship_score,
            network_strength_score,
            network_type
        FROM problem_network_summary
        WHERE
            (
                category_a = :category_a
                AND category_b = :category_b
            )
            OR
            (
                category_a = :category_b
                AND category_b = :category_a
            )
        LIMIT 1
    """)

    row = db.execute(
        query,
        {
            "category_a": category_a,
            "category_b": category_b,
        },
    ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Problem network not found",
        )

    return dict(row)


# ============================================================
# 9. ROAD-SPECIFIC PROBLEM NETWORK
# ============================================================

@router.get("/priority/{road_segment_id}/network")
def road_problem_network(
    road_segment_id: int,
    db: Session = Depends(get_db),
):
    road_query = text("""
        SELECT
            road_segment_id,
            ward_number,
            segment_name,
            urban_priority_score,
            priority_level
        FROM urban_priority_results
        WHERE road_segment_id = :road_segment_id
        LIMIT 1
    """)

    road = db.execute(
        road_query,
        {
            "road_segment_id": road_segment_id,
        },
    ).mappings().first()

    if not road:
        raise HTTPException(
            status_code=404,
            detail="Road segment not found",
        )

    network_query = text("""
        WITH road_complaints AS (
            SELECT DISTINCT
                complaint_id
            FROM road_complaint_assignments
            WHERE
                road_segment_id = :road_segment_id
                AND match_confidence <> 'UNMATCHED'
        ),

        road_relationships AS (
            SELECT DISTINCT
                cr.source_complaint_id,
                cr.target_complaint_id,
                cr.source_category,
                cr.target_category,
                cr.relationship_score,
                cr.relationship_type
            FROM complaint_relationships cr
            WHERE
                cr.source_complaint_id IN (
                    SELECT complaint_id
                    FROM road_complaints
                )
                AND
                cr.target_complaint_id IN (
                    SELECT complaint_id
                    FROM road_complaints
                )
        ),

        normalized_relationships AS (
            SELECT
                LEAST(
                    source_category,
                    target_category
                ) AS category_a,

                GREATEST(
                    source_category,
                    target_category
                ) AS category_b,

                relationship_score,
                relationship_type
            FROM road_relationships
        )

        SELECT
            category_a,
            category_b,

            COUNT(*) AS relationship_count,

            COUNT(*) FILTER (
                WHERE relationship_type = 'STRONG'
            ) AS strong_relationships,

            COUNT(*) FILTER (
                WHERE relationship_type = 'MODERATE'
            ) AS moderate_relationships,

            COUNT(*) FILTER (
                WHERE relationship_type = 'WEAK'
            ) AS weak_relationships,

            ROUND(
                AVG(relationship_score)::numeric,
                2
            ) AS avg_relationship_score,

            MAX(relationship_score) AS max_relationship_score

        FROM normalized_relationships

        GROUP BY
            category_a,
            category_b

        ORDER BY
            relationship_count DESC,
            strong_relationships DESC,
            moderate_relationships DESC,
            avg_relationship_score DESC
    """)

    rows = db.execute(
        network_query,
        {
            "road_segment_id": road_segment_id,
        },
    ).mappings().all()

    return {
        "road_segment_id": road["road_segment_id"],
        "ward_number": road["ward_number"],
        "segment_name": road["segment_name"],
        "urban_priority_score": road["urban_priority_score"],
        "priority_level": road["priority_level"],
        "count": len(rows),
        "networks": [dict(row) for row in rows],
    }