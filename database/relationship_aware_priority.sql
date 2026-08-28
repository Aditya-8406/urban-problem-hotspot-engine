DROP TABLE IF EXISTS road_relationship_context;

CREATE TABLE road_relationship_context AS
WITH road_categories AS (
    SELECT
        road_segment_id,
        ward_number,
        ARRAY_AGG(DISTINCT category) AS categories
    FROM road_complaint_assignments
    WHERE
        road_segment_id IS NOT NULL
        AND match_confidence <> 'UNMATCHED'
        AND category IS NOT NULL
    GROUP BY road_segment_id, ward_number
),

matched_relationships AS (
    SELECT
        rc.road_segment_id,
        pc.ward_number,
        pc.category_a,
        pc.category_b,
        pc.co_occurring_months,
        pc.co_occurrence_strength,
        pc.connection_score
    FROM road_categories rc
    JOIN problem_connectivity pc
        ON pc.ward_number = rc.ward_number
       AND pc.category_a = ANY(rc.categories)
       AND pc.category_b = ANY(rc.categories)
)

SELECT
    road_segment_id,
    ward_number,

    category_a,
    category_b,

    co_occurring_months,
    co_occurrence_strength,
    connection_score AS relationship_score

FROM matched_relationships;


DROP TABLE IF EXISTS road_unified_priority;

CREATE TABLE road_unified_priority AS
SELECT
    p.road_segment_id,
    p.ward_number,
    p.segment_name,
    p.highway,

    p.complaint_count,
    p.active_months,
    p.avg_severity,
    p.unresolved_count,

    p.road_priority_score,

    COALESCE(r.relationship_score, 0) AS relationship_score,

    COALESCE(r.co_occurring_months, 0) AS relationship_co_occurring_months,

    COALESCE(r.co_occurrence_strength, 0) AS relationship_co_occurrence_strength,

    r.category_a AS relationship_category_a,
    r.category_b AS relationship_category_b,

    CASE
        WHEN r.road_segment_id IS NOT NULL THEN TRUE
        ELSE FALSE
    END AS has_problem_relationship

FROM road_priority_results p

LEFT JOIN road_relationship_context r
    ON r.road_segment_id = p.road_segment_id;