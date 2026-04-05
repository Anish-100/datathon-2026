import json
import math
import urllib.request
import urllib.parse


# ── Haversine distance (meters) ─────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── Overpass API query for commercial zones ─────────────────────────────────
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def fetch_nearby_commercial(lat: float, lon: float, radius_m: int = 5000) -> list[dict]:
    """
    Query OpenStreetMap via Overpass for commercial/retail land use areas
    within radius_m of (lat, lon). Returns list of elements with center coords.
    """
    query = f"""
    [out:json][timeout:15];
    (
      way["landuse"="commercial"](around:{radius_m},{lat},{lon});
      way["landuse"="retail"](around:{radius_m},{lat},{lon});
      relation["landuse"="commercial"](around:{radius_m},{lat},{lon});
      relation["landuse"="retail"](around:{radius_m},{lat},{lon});
    );
    out center;
    """
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(OVERPASS_URL, data=data, method="POST")
    req.add_header("User-Agent", "datathon-zone-finder/1.0")
    with urllib.request.urlopen(req, timeout=20) as resp:
        result = json.loads(resp.read())
    return result.get("elements", [])


def _extract_center(element: dict) -> tuple[float, float] | None:
    """Get (lat, lon) from an Overpass element's center or direct coords."""
    center = element.get("center")
    if center:
        return center["lat"], center["lon"]
    if "lat" in element and "lon" in element:
        return element["lat"], element["lon"]
    return None


def find_closest_commercial_zone(lat: float, lon: float) -> dict | None:
    """
    Given a (lat, lon), find the nearest commercial/retail zone via OpenStreetMap.
    Returns: {"lat": float, "lon": float, "name": str, "landuse": str, "distance_m": float}
    Returns None if nothing is found.
    """
    elements = fetch_nearby_commercial(lat, lon, radius_m=5000)

    if not elements:
        elements = fetch_nearby_commercial(lat, lon, radius_m=30_000)

    if not elements:
        return None

    best = None
    best_dist = float("inf")

    for elem in elements:
        center = _extract_center(elem)
        if center is None:
            continue
        c_lat, c_lon = center
        dist = haversine(lat, lon, c_lat, c_lon)
        if dist < best_dist:
            best_dist = dist
            tags = elem.get("tags", {})
            best = {
                "lat": c_lat,
                "lon": c_lon,
                "name": tags.get("name", "Unnamed"),
                "landuse": tags.get("landuse", "commercial"),
                "distance_m": round(dist, 1),
            }

    return best


def obtain_lat_long(file_path: str) -> tuple[float, float]:
    """
    Read a file of lat, lon pairs (one per line) and return the average
    of the first 5 entries as (lat, lon).
    """
    lats = []
    lons = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            line = line.replace("\u2212", "-")
            parts = line.split(",")
            if len(parts) != 2:
                continue
            lats.append(float(parts[0].strip()))
            lons.append(float(parts[1].strip()))
            if len(lats) == 5:
                break
    if not lats:
        raise ValueError(f"No valid lat/lon pairs found in {file_path}")
    avg_lat = sum(lats) / len(lats)
    avg_lon = sum(lons) / len(lons)
    return avg_lat, avg_lon

def main():
    file_path = 'API/Prediction/raw_text.txt'

    lat, long = obtain_lat_long(file_path)

    print(f"Looking for commercial zone near ({lat}, {long}) ...")
    result = find_closest_commercial_zone(lat, long)
    if result:
        print(f"\n── Closest Commercial Zone ──────────────────────────────")
        print(f"  Name        : {result['name']}")
        print(f"  Land Use    : {result['landuse']}")
        print(f"  Centroid    : ({result['lat']:.6f}, {result['lon']:.6f})")
        print(f"  Distance    : {result['distance_m']:,.1f} m  ({result['distance_m']/1609.34:.2f} miles)")
        print(f"─────────────────────────────────────────────────────────")
    else:
        print("  No commercial zones found nearby.")



# ── Standalone test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
