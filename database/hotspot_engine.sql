DROP TABLE IF EXISTS hotspot_results;

CREATE TABLE hotspot_results AS

WITH base AS (
    SELECT
        COALESCE(spatial_ward_number, ward_number) AS ward_number,
        category,
        complaint_date,
        severity,
        status
    FROM complaints
    WHERE COALESCE(spatial_ward_number, ward_number) IS NOT NULL
      AND complaint_date IS NOT NULL
      AND complaint_date <= CURRENT_TIMESTAMP
),

monthly AS (
    SELECT
        ward_number,
        category,
        DATE_TRUNC('month', complaint_date) AS month,
        COUNT(*) AS monthly_complaints
    FROM base
    GROUP BY
        ward_number,
        category,
        DATE_TRUNC('month', complaint_date)
),

aggregated AS (
    SELECT
        b.ward_number,
        b.category,

        COUNT(*) AS complaint_count,

        COUNT(DISTINCT DATE_TRUNC('month', b.complaint_date))
            AS active_months,

        MIN(b.complaint_date) AS first_complaint,
        MAX(b.complaint_date) AS last_complaint,

        ROUND(AVG(b.severity)::numeric, 2)
            AS avg_severity,

        COUNT(*) FILTER (
            WHERE LOWER(COALESCE(b.status, '')) NOT IN
            ('resolved', 'closed')
        ) AS unresolved_count

    FROM base b

    GROUP BY
        b.ward_number,
        b.category
),

limits AS (
    SELECT
        MAX(complaint_count) AS max_complaints,
        MAX(active_months) AS max_active_months
    FROM aggregated
),

scored AS (
    SELECT
        a.*,

        ROUND(
            (a.complaint_count::numeric /
             NULLIF(l.max_complaints, 0)) * 100,
            2
        ) AS volume_score,

        ROUND(
            (a.active_months::numeric /
             NULLIF(l.max_active_months, 0)) * 100,
            2
        ) AS persistence_score,

        ROUND(
            (COALESCE(a.avg_severity, 0)::numeric / 5) * 100,
            2
        ) AS severity_score

    FROM aggregated a
    CROSS JOIN limits l
)

SELECT
    ward_number,
    category,
    complaint_count,
    active_months,
    first_complaint,
    last_complaint,
    avg_severity,
    unresolved_count,

    volume_score,
    persistence_score,
    severity_score,

    ROUND(
        (
            volume_score * 0.40 +
            persistence_score * 0.35 +
            severity_score * 0.25
        )::numeric,
        2
    ) AS hotspot_score

FROM scored
ORDER BY hotspot_score DESC;