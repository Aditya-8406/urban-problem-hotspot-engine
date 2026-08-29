import json
import psycopg2

INPUT = "data/osm/jabalpur_roads.json"

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="urban_hotspot",
    user="postgres",
    password="postgres",
)

cur = conn.cursor()

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

count = 0

for element in data.get("elements", []):
    if element.get("type") != "way":
        continue

    geometry = element.get("geometry", [])

    if len(geometry) < 2:
        continue

    tags = element.get("tags", {})

    coords = [
        (point["lon"], point["lat"])
        for point in geometry
        if "lon" in point and "lat" in point
    ]

    if len(coords) < 2:
        continue

    wkt = "LINESTRING(" + ",".join(
        f"{lon} {lat}" for lon, lat in coords
    ) + ")"

    cur.execute(
        """
        INSERT INTO osm_roads_raw
        (
            osm_id,
            name,
            highway,
            surface,
            lanes,
            oneway,
            maxspeed,
            ref,
            geom
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,
            ST_GeomFromText(%s, 4326)
        )
        ON CONFLICT (osm_id) DO NOTHING
        """,
        (
            element["id"],
            tags.get("name"),
            tags.get("highway"),
            tags.get("surface"),
            tags.get("lanes"),
            tags.get("oneway"),
            tags.get("maxspeed"),
            tags.get("ref"),
            wkt,
        ),
    )

    count += 1

    if count % 1000 == 0:
        print(f"Imported {count} roads...")

conn.commit()

cur.close()
conn.close()

print(f"Imported {count} road ways.")