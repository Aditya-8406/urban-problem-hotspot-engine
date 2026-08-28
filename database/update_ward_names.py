import json
from pathlib import Path

geojson_path = Path("geo/jabalpur_79_wards.geojson")

ward_names = {
    71: "Lamti",
    72: "Tilhari",
    73: "Kugawan",
    74: "Andhuwa",
    75: "Chhiwlaha",
    76: "Bhatauli",
    77: "Regwa",
    78: "Khairi",
    79: "Rachai",
}

with geojson_path.open("r", encoding="utf-8") as f:
    data = json.load(f)

updated = 0

for feature in data["features"]:
    ward_number = int(feature["properties"]["ward_number"])

    if ward_number in ward_names:
        feature["properties"]["ward_name"] = ward_names[ward_number]
        updated += 1

with geojson_path.open("w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Updated {updated} ward names.")