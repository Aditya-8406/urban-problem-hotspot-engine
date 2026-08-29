DROP TABLE IF EXISTS municipal_explanations;

CREATE TABLE municipal_explanations AS

SELECT
    p.ward_number,
    w.name AS ward_name,
    p.category,

    p.complaint_count,
    p.active_months,
    p.avg_severity,
    p.unresolved_count,
    p.unresolved_rate_score,

    p.hotspot_score,

    p.connected_category,
    p.connection_score,

    p.municipal_priority_score,
    p.priority_level,

    CASE
        WHEN p.hotspot_score >= 80
            THEN 'Very high hotspot intensity'

        WHEN p.hotspot_score >= 65
            THEN 'High hotspot intensity'

        WHEN p.hotspot_score >= 50
            THEN 'Moderate hotspot intensity'

        ELSE 'Low hotspot intensity'
    END AS hotspot_reason,

    CASE
        WHEN p.active_months >= 18
            THEN 'Highly persistent problem'

        WHEN p.active_months >= 12
            THEN 'Persistent problem'

        WHEN p.active_months >= 6
            THEN 'Recurring problem'

        ELSE 'Limited temporal recurrence'
    END AS persistence_reason,

    CASE
        WHEN p.unresolved_rate_score >= 70
            THEN 'Very high unresolved burden'

        WHEN p.unresolved_rate_score >= 50
            THEN 'High unresolved burden'

        WHEN p.unresolved_rate_score >= 25
            THEN 'Moderate unresolved burden'

        ELSE 'Low unresolved burden'
    END AS resolution_reason,

    CASE
        WHEN p.connection_score >= 75
            THEN 'Strong connection with another recurring urban problem'

        WHEN p.connection_score >= 50
            THEN 'Moderate connection with another recurring urban problem'

        WHEN p.connection_score >= 25
            THEN 'Some recurring association with another urban problem'

        ELSE 'No strong recurring problem association'
    END AS connectivity_reason,

    CASE
        WHEN p.category = 'Drainage'
            THEN 'Inspect and rehabilitate drainage infrastructure; investigate recurring waterlogging locations.'

        WHEN p.category = 'Waterlogging'
            THEN 'Inspect drainage capacity and identify recurring water accumulation locations.'

        WHEN p.category = 'Garbage Collection'
            THEN 'Increase collection frequency and inspect recurring accumulation locations.'

        WHEN p.category = 'Illegal Dumping'
            THEN 'Inspect dumping hotspots and strengthen waste-control measures.'

        WHEN p.category = 'Pothole'
            THEN 'Inspect affected road sections and prioritize pavement repair.'

        WHEN p.category = 'Damaged Road'
            THEN 'Inspect road condition and prioritize structural/pavement repairs.'

        WHEN p.category = 'Streetlight'
            THEN 'Inspect non-functional streetlights and prioritize electrical maintenance.'

        WHEN p.category = 'Water Supply'
            THEN 'Inspect water-supply infrastructure and investigate recurring service complaints.'

        WHEN p.category = 'Water Leakage'
            THEN 'Inspect leakage locations and prioritize pipeline maintenance.'

        WHEN p.category = 'Damaged Sidewalk'
            THEN 'Inspect pedestrian infrastructure and prioritize damaged sections.'

        ELSE
            'Inspect the affected locations and determine an appropriate municipal intervention.'
    END AS recommended_action

FROM municipal_priority_results p

LEFT JOIN wards w
    ON w.ward_number = p.ward_number

ORDER BY p.municipal_priority_score DESC;