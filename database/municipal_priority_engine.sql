DROP TABLE IF EXISTS municipal_priority_results;

CREATE TABLE municipal_priority_results AS

WITH connectivity AS (

    SELECT
        ward_number,
        category_a AS category,
        category_b AS connected_category,
        connection_score
    FROM problem_connectivity

    UNION ALL

    SELECT
        ward_number,
        category_b AS category,
        category_a AS connected_category,
        connection_score
    FROM problem_connectivity
),

best_connection AS (

    SELECT DISTINCT ON (ward_number, category)
        ward_number,
        category,
        connected_category,
        connection_score

    FROM connectivity

    ORDER BY
        ward_number,
        category,
        connection_score DESC
),

base AS (

    SELECT
        h.*,

        COALESCE(
            bc.connection_score,
            0
        ) AS connection_score,

        bc.connected_category

    FROM hotspot_results h

    LEFT JOIN best_connection bc
      ON bc.ward_number = h.ward_number
     AND bc.category = h.category
),

scored AS (

    SELECT
        *,

        ROUND(
            (
                unresolved_count::numeric /
                NULLIF(complaint_count, 0)
            ) * 100,
            2
        ) AS unresolved_rate_score

    FROM base
)

SELECT
    ward_number,
    category,

    complaint_count,
    active_months,
    avg_severity,
    unresolved_count,

    hotspot_score,

    connected_category,
    connection_score,

    unresolved_rate_score,

    ROUND(
        (
            hotspot_score * 0.60 +
            connection_score * 0.20 +
            unresolved_rate_score * 0.20
        )::numeric,
        2
    ) AS municipal_priority_score,

    CASE

        WHEN (
            hotspot_score * 0.60 +
            connection_score * 0.20 +
            unresolved_rate_score * 0.20
        ) >= 80
        THEN 'CRITICAL'

        WHEN (
            hotspot_score * 0.60 +
            connection_score * 0.20 +
            unresolved_rate_score * 0.20
        ) >= 65
        THEN 'HIGH'

        WHEN (
            hotspot_score * 0.60 +
            connection_score * 0.20 +
            unresolved_rate_score * 0.20
        ) >= 50
        THEN 'MEDIUM'

        ELSE 'LOW'

    END AS priority_level

FROM scored

ORDER BY municipal_priority_score DESC;