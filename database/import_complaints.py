import pandas as pd
from pathlib import Path

INPUT = Path("data/processed/complaints_clean.csv")
OUTPUT = Path("database/import_complaints.sql")

df = pd.read_csv(INPUT)

def sql_text(value):
    if pd.isna(value):
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"

def sql_int(value):
    if pd.isna(value):
        return "NULL"
    return str(int(value))

def sql_float(value):
    if pd.isna(value):
        return "NULL"
    return str(float(value))

sql = [
    "BEGIN;",
    "TRUNCATE TABLE complaints RESTART IDENTITY CASCADE;"
]

for _, row in df.iterrows():

    lat = row["mapped_latitude"]
    lon = row["mapped_longitude"]

    if pd.isna(lat) or pd.isna(lon):
        geom = "NULL"
    else:
        geom = (
            f"ST_SetSRID("
            f"ST_MakePoint({float(lon)}, {float(lat)}),"
            f"4326)"
        )

    complaint_date = sql_text(row["date"])

    resolution_date = sql_text(
        row["resolution_date"]
        if "resolution_date" in row
        else None
    )

    sql.append(f"""
INSERT INTO complaints (
    complaint_id,
    category,
    description,
    complaint_date,
    latitude,
    longitude,
    geom,
    ward_number,
    severity,
    status,
    resolution_date,
    data_type,
    source
)
VALUES (
    {sql_text(row["complaint_id"])},
    {sql_text(row["category"])},
    {sql_text(row["description"])},
    {complaint_date},
    {sql_float(row["original_latitude"])},
    {sql_float(row["original_longitude"])},
    {geom},
    {sql_int(row["ward_number"])},
    {sql_int(row["severity"])},
    {sql_text(row["status"])},
    {resolution_date},
    {sql_text(row["data_type"])},
    {sql_text(row["source"])}
);
""")

sql.append("COMMIT;")

OUTPUT.write_text(
    "\n".join(sql),
    encoding="utf-8"
)

print(f"Generated SQL for {len(df)} complaints.")
print(f"Output: {OUTPUT}")