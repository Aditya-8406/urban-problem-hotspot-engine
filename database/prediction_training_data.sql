DROP TABLE IF EXISTS prediction_training_data;

CREATE TABLE prediction_training_data AS

WITH months AS (
    SELECT generate_series(
        DATE '2024-01-01',
        DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 month',
        INTERVAL '1 month'
    )::date AS month
),

categories AS (
    SELECT DISTINCT category
    FROM complaints
    WHERE complaint_date >= DATE '2024-01-01'
      AND category IN (
          'Garbage Collection',
          'Drainage',
          'Waterlogging',
          'Streetlight',
          'Pothole',
          'Damaged Road',
          'Illegal Dumping',
          'Water Supply',
          'Water Leakage',
          'Damaged Sidewalk'
      )
),

wards AS (
    SELECT generate_series(1, 79) AS ward_number
),

grid AS (
    SELECT
        w.ward_number,
        c.category,
        m.month
    FROM wards w
    CROSS JOIN categories c
    CROSS JOIN months m
),

monthly AS (
    SELECT
        g.ward_number,
        g.category,
        g.month,

        COUNT(c.complaint_id) AS complaint_count,

        COALESCE(AVG(c.severity), 0) AS avg_severity,

        COUNT(c.complaint_id)
            FILTER (WHERE c.status NOT IN ('Resolved', 'Closed')) AS unresolved_count

    FROM grid g

    LEFT JOIN complaints c
        ON c.ward_number = g.ward_number
       AND c.category = g.category
       AND DATE_TRUNC('month', c.complaint_date)::date = g.month

    GROUP BY
        g.ward_number,
        g.category,
        g.month
),

features AS (
    SELECT
        *,

        SUM(complaint_count) OVER (
            PARTITION BY ward_number, category
            ORDER BY month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS complaints_3m,

        SUM(complaint_count) OVER (
            PARTITION BY ward_number, category
            ORDER BY month
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        ) AS complaints_6m,

        SUM(
            CASE WHEN complaint_count > 0 THEN 1 ELSE 0 END
        ) OVER (
            PARTITION BY ward_number, category
            ORDER BY month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ) AS active_months_3m,

        SUM(
            CASE WHEN complaint_count > 0 THEN 1 ELSE 0 END
        ) OVER (
            PARTITION BY ward_number, category
            ORDER BY month
            ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
        ) AS active_months_6m,

        SUM(
            CASE WHEN complaint_count > 0 THEN 1 ELSE 0 END
        ) OVER (
            PARTITION BY ward_number, category
            ORDER BY month
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS historical_active_months

    FROM monthly
),

with_trend AS (
    SELECT
        *,

        complaint_count
        - LAG(complaint_count, 3) OVER (
            PARTITION BY ward_number, category
            ORDER BY month
        ) AS trend_3m

    FROM features
),

with_target AS (
    SELECT
        *,

        EXTRACT(MONTH FROM month)::integer AS month_of_year,

        CASE
            WHEN LEAD(complaint_count) OVER (
                PARTITION BY ward_number, category
                ORDER BY month
            ) > 0
            THEN 1
            ELSE 0
        END AS target_next_month

    FROM with_trend
)

SELECT
    ward_number,
    category,
    month,
    complaint_count,
    complaints_3m,
    complaints_6m,
    active_months_3m,
    active_months_6m,
    historical_active_months,
    trend_3m,
    month_of_year,
    target_next_month

FROM with_target

ORDER BY
    ward_number,
    category,
    month;