DROP TABLE IF EXISTS problem_connectivity;

CREATE TABLE problem_connectivity AS

WITH ward_month_category AS (
    SELECT
        COALESCE(spatial_ward_number, ward_number) AS ward_number,
        category,
        DATE_TRUNC('month', complaint_date) AS month,
        COUNT(*) AS complaint_count
    FROM complaints
    WHERE COALESCE(spatial_ward_number, ward_number) IS NOT NULL
      AND complaint_date IS NOT NULL
      AND complaint_date <= CURRENT_TIMESTAMP
    GROUP BY
        COALESCE(spatial_ward_number, ward_number),
        category,
        DATE_TRUNC('month', complaint_date)
),

category_stats AS (
    SELECT
        ward_number,
        category,
        COUNT(*) AS active_months
    FROM ward_month_category
    GROUP BY ward_number, category
),

pairs AS (
    SELECT
        a.ward_number,
        a.category AS category_a,
        b.category AS category_b,

        COUNT(*) AS co_occurring_months,

        SUM(
            LEAST(
                a.complaint_count,
                b.complaint_count
            )
        ) AS co_occurrence_strength

    FROM ward_month_category a

    JOIN ward_month_category b
      ON a.ward_number = b.ward_number
     AND a.month = b.month
     AND a.category < b.category

    GROUP BY
        a.ward_number,
        a.category,
        b.category
)

SELECT
    p.ward_number,
    p.category_a,
    p.category_b,

    p.co_occurring_months,
    p.co_occurrence_strength,

    a.active_months AS category_a_active_months,
    b.active_months AS category_b_active_months,

    ROUND(
        (
            p.co_occurring_months::numeric /
            SQRT(
                a.active_months::numeric *
                b.active_months::numeric
            )
        ) * 100,
        2
    ) AS connection_score

FROM pairs p

JOIN category_stats a
  ON a.ward_number = p.ward_number
 AND a.category = p.category_a

JOIN category_stats b
  ON b.ward_number = p.ward_number
 AND b.category = p.category_b

WHERE p.co_occurring_months >= 3

ORDER BY connection_score DESC;