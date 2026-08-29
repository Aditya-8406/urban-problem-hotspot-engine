import os
from itertools import combinations

import psycopg2


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/urban_hotspot",
)

MAX_DISTANCE_M = 100.0


# ============================================================
# CATEGORY PRIOR MODEL
# ============================================================

CATEGORY_PRIORS = {
    frozenset(("Drainage", "Waterlogging")): 1.00,
    frozenset(("Pothole", "Damaged Road")): 1.00,
    frozenset(("Water Supply", "Water Leakage")): 1.00,

    frozenset(("Garbage Collection", "Illegal Dumping")): 0.95,

    frozenset(("Damaged Sidewalk", "Streetlight")): 0.90,

    frozenset(("Garbage Collection", "Waterlogging")): 0.85,
    frozenset(("Garbage Collection", "Drainage")): 0.85,

    frozenset(("Damaged Road", "Drainage")): 0.75,
    frozenset(("Damaged Road", "Waterlogging")): 0.75,
    frozenset(("Drainage", "Illegal Dumping")): 0.75,

    frozenset(("Pothole", "Waterlogging")): 0.70,
    frozenset(("Pothole", "Drainage")): 0.70,

    frozenset(("Damaged Sidewalk", "Pothole")): 0.65,

    frozenset(("Water Leakage", "Drainage")): 0.65,
    frozenset(("Streetlight", "Damaged Road")): 0.60,
    frozenset(("Streetlight", "Pothole")): 0.60,
    frozenset(("Illegal Dumping", "Waterlogging")): 0.60,
}


DEFAULT_CATEGORY_PRIOR = 0.30


def category_prior(category_a: str, category_b: str) -> float:
    """
    Return a normalized 0-1 prior representing how strongly
    two different municipal problem categories are expected
    to be related.

    Same-category relationships are excluded before this
    function is called.
    """

    key = frozenset((category_a, category_b))

    return CATEGORY_PRIORS.get(
        key,
        DEFAULT_CATEGORY_PRIOR,
    )


# ============================================================
# SPATIAL SCORE
# ============================================================

def spatial_score(distance_m: float) -> float:
    if distance_m < 10:
        return 100.0

    elif distance_m <= 25:
        return 80.0

    elif distance_m < 50:
        return 60.0

    else:
        return 30.0


# ============================================================
# TEMPORAL SCORE
# ============================================================

def temporal_score(time_difference_days: float) -> float:
    if time_difference_days <= 30:
        return 100.0

    elif time_difference_days <= 90:
        return 80.0

    elif time_difference_days <= 180:
        return 60.0

    elif time_difference_days <= 365:
        return 40.0

    else:
        return 20.0


# ============================================================
# SEVERITY SCORE
# ============================================================

def severity_score(
    source_severity: int,
    target_severity: int,
) -> float:
    return (
        (source_severity + target_severity) / 2.0
    ) * 20.0


# ============================================================
# FINAL RELATIONSHIP SCORE
# ============================================================

def relationship_score(
    spatial: float,
    temporal: float,
    severity: float,
    category: float,
) -> float:
    """
    Combined relationship score.

    Spatial evidence      = 45%
    Temporal evidence     = 25%
    Severity evidence     = 15%
    Category prior        = 15%
    """

    return round(
        0.45 * spatial
        + 0.25 * temporal
        + 0.15 * severity
        + 0.15 * (category * 100.0),
        2,
    )


# ============================================================
# RELATIONSHIP TYPE
# ============================================================

def relationship_type(score: float) -> str:
    if score >= 80:
        return "STRONG"

    elif score >= 60:
        return "MODERATE"

    return "WEAK"


# ============================================================
# LOAD COMPLAINTS
# ============================================================

def load_complaints(conn):
    query = """
        SELECT
            complaint_id,
            category,
            complaint_date,
            latitude,
            longitude,
            ward_number,
            severity
        FROM complaints
        WHERE
            latitude IS NOT NULL
            AND longitude IS NOT NULL
            AND complaint_date IS NOT NULL
            AND ward_number IS NOT NULL
            AND severity IS NOT NULL
        ORDER BY ward_number, complaint_id;
    """

    with conn.cursor() as cur:
        cur.execute(query)

        columns = [
            desc[0]
            for desc in cur.description
        ]

        return [
            dict(zip(columns, row))
            for row in cur.fetchall()
        ]


# ============================================================
# DISTANCE
# ============================================================

def calculate_distance(
    conn,
    lon1,
    lat1,
    lon2,
    lat2,
):
    query = """
        SELECT ST_Distance(
            ST_Transform(
                ST_SetSRID(
                    ST_MakePoint(%s, %s),
                    4326
                ),
                3857
            ),
            ST_Transform(
                ST_SetSRID(
                    ST_MakePoint(%s, %s),
                    4326
                ),
                3857
            )
        );
    """

    with conn.cursor() as cur:
        cur.execute(
            query,
            (
                lon1,
                lat1,
                lon2,
                lat2,
            ),
        )

        return float(
            cur.fetchone()[0]
        )


# ============================================================
# GENERATE RELATIONSHIPS
# ============================================================

def generate_relationships(conn):
    complaints = load_complaints(conn)

    print(
        f"Loaded complaints: {len(complaints)}"
    )

    relationships = []

    complaints_by_ward = {}

    for complaint in complaints:
        complaints_by_ward.setdefault(
            complaint["ward_number"],
            [],
        ).append(complaint)

    for ward_number, ward_complaints in complaints_by_ward.items():

        print(
            f"Processing ward {ward_number}: "
            f"{len(ward_complaints)} complaints"
        )

        for source, target in combinations(
            ward_complaints,
            2,
        ):

            # ------------------------------------------------
            # IMPORTANT:
            # Only create relationships between DIFFERENT
            # problem categories.
            # ------------------------------------------------

            if source["category"] == target["category"]:
                continue

            distance = calculate_distance(
                conn,
                source["longitude"],
                source["latitude"],
                target["longitude"],
                target["latitude"],
            )

            if distance > MAX_DISTANCE_M:
                continue

            time_difference = abs(
                (
                    source["complaint_date"]
                    - target["complaint_date"]
                ).total_seconds()
            ) / 86400.0

            spatial = spatial_score(
                distance
            )

            temporal = temporal_score(
                time_difference
            )

            severity = severity_score(
                source["severity"],
                target["severity"],
            )

            prior = category_prior(
                source["category"],
                target["category"],
            )

            score = relationship_score(
                spatial,
                temporal,
                severity,
                prior,
            )

            rel_type = relationship_type(
                score
            )

            relationships.append(
                (
                    source["complaint_id"],
                    target["complaint_id"],
                    source["category"],
                    target["category"],
                    ward_number,
                    round(distance, 2),
                    round(time_difference, 2),
                    source["severity"],
                    target["severity"],
                    spatial,
                    temporal,
                    severity,
                    score,
                    rel_type,
                )
            )

    print(
        f"Generated relationships: "
        f"{len(relationships)}"
    )

    return relationships


# ============================================================
# CREATE TEST TABLE
# ============================================================

def create_test_table(conn):
    with conn.cursor() as cur:

        cur.execute(
            """
            DROP TABLE IF EXISTS
                complaint_relationships_test;
            """
        )

        cur.execute(
            """
            CREATE TABLE
                complaint_relationships_test
            AS
                SELECT *
                FROM complaint_relationships
                WITH NO DATA;
            """
        )

    conn.commit()


# ============================================================
# INSERT TEST RELATIONSHIPS
# ============================================================

def insert_relationships(
    conn,
    relationships,
):
    query = """
        INSERT INTO complaint_relationships_test (
            source_complaint_id,
            target_complaint_id,
            source_category,
            target_category,
            ward_number,
            distance_m,
            time_difference_days,
            source_severity,
            target_severity,
            spatial_score,
            temporal_score,
            severity_score,
            relationship_score,
            relationship_type
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        );
    """

    with conn.cursor() as cur:

        cur.executemany(
            query,
            relationships,
        )

    conn.commit()


# ============================================================
# MAIN
# ============================================================

def main():
    print("Connecting to database...")

    conn = psycopg2.connect(
        DATABASE_URL
    )

    try:

        create_test_table(conn)

        relationships = generate_relationships(
            conn
        )

        insert_relationships(
            conn,
            relationships,
        )

        print(
            "Created "
            "complaint_relationships_test"
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()