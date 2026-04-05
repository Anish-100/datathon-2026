import re
import csv

input_path = "API/Prediction/pretty_text.txt"
output_path = "frontend/graphs/use_for_graphs.csv"

with open(input_path, "r") as f:
    lines = f.readlines()

rows = []
for line in lines[1:]:  # skip header
    match = re.match(r"\(([^,]+),\s*([^)]+)\)\s*->\s*([0-9.]+)", line.strip())
    if match:
        lat, lon, score = match.group(1), match.group(2), match.group(3)
        rows.append(((float(lat), float(lon)), float(score)))

with open(output_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["lat", "lon", "viability_score"])
    for (lat, lon), score in rows:
        writer.writerow([lat, lon, score])

print(f"Wrote {len(rows)} rows to {output_path}")
