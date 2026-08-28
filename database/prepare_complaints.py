import json
from pathlib import Path

import pandas as pd

INPUT_CSV = Path("data/synthetic/complaints_test_1820.csv")
GEOJSON = Path("geo/jabalpur_79_wards.geojson")
OUTPUT_CSV = Path("data/processed/complaints_clean.csv")

df = pd.read_csv(INPUT_CSV)

with GEOJSON.open("r", encoding="utf-8") as f:
    geojson = json.load(f)

# Ward → centroid lookup
ward_centroids = {}

for feature in geojson["features"]:
    props = feature["properties"]

    ward = int(props["ward_number"])

    ward_centroids[ward] = {
        "latitude": float(props["centroid_latitude"]),
        "longitude": float(props["centroid_longitude"]),
        "name": props["ward_name"],
    }

# Normalize ward number
df["ward_number"] = pd.to_numeric(
    df["ward_number"],
    errors="coerce"
)

# Preserve original coordinates
df["original_latitude"] = df["latitude"]
df["original_longitude"] = df["longitude"]

# New inferred coordinates
df["mapped_latitude"] = df["latitude"]
df["mapped_longitude"] = df["longitude"]

# Location method
df["location_method"] = "exact"

missing_coords = (
    df["latitude"].isna()
    | df["longitude"].isna()
)

df.loc[missing_coords, "location_method"] = "ward_centroid"

# Fill ONLY mapped coordinates
for index in df.index[missing_coords]:

    ward = df.at[index, "ward_number"]

    if pd.isna(ward):
        df.at[index, "location_method"] = "unknown"
        continue

    ward = int(ward)

    if ward not in ward_centroids:
        df.at[index, "location_method"] = "unknown"
        continue

    centroid = ward_centroids[ward]

    df.at[index, "mapped_latitude"] = centroid["latitude"]
    df.at[index, "mapped_longitude"] = centroid["longitude"]

# Confidence
df["location_confidence"] = df["location_method"].map({
    "exact": "high",
    "ward_centroid": "medium",
    "unknown": "none"
})

OUTPUT_CSV.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_CSV,
    index=False
)

print("Complaint preprocessing complete.")
print(f"Total complaints: {len(df)}")
print(
    f"Exact locations: "
    f"{(df['location_method'] == 'exact').sum()}"
)
print(
    f"Ward centroid locations: "
    f"{(df['location_method'] == 'ward_centroid').sum()}"
)
print(
    f"Unknown locations: "
    f"{(df['location_method'] == 'unknown').sum()}"
)
print(f"Output: {OUTPUT_CSV}")