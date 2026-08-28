import json
from pathlib import Path

geojson_path = Path("geo/jabalpur_79_wards.geojson")
sql_path = Path("database/import_wards.sql")

with geojson_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

features = data["features"]

print(f"Found {len(features)} ward features.")

sql = [
    "BEGIN;",
    "TRUNCATE TABLE wards RESTART IDENTITY CASCADE;"
]

for feature in features:
    properties = feature["properties"]
    geometry = feature["geometry"]

    ward_number = int(properties["ward_number"])
    ward_name = properties.get("ward_name")

    # Escape single quotes for SQL
    ward_name_sql = (
        str(ward_name).replace("'", "''")
        if ward_name is not None
        else ""
    )

    geometry_json = json.dumps(
        geometry,
        separators=(",", ":")
    ).replace("'", "''")

    sql.append(
        f"""
INSERT INTO wards (ward_number, name, geom)
VALUES (
    {ward_number},
    '{ward_name_sql}',
    ST_Multi(
        ST_SetSRID(
            ST_GeomFromGeoJSON('{geometry_json}'),
            4326
        )
    )
);
"""
    )

sql.append("COMMIT;")

sql_path.write_text("\n".join(sql), encoding="utf-8")

print(f"SQL generated: {sql_path}")