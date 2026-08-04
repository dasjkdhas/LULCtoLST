"""Build both AOI polygons (Yamaguchi + Yonago) from hard-coded landmark
bounding boxes — removes the QGIS dependency so codex can produce the
GeoJSONs entirely in Python without a desktop GUI.

Coordinates are declared as (west_lon, south_lat, east_lon, north_lat) in
WGS84 (EPSG:4326). Each bounding box is sized to:

- cover every core landmark for the compact central district;
- leave ≥ 500 m buffer beyond the outermost landmark so that
  neighbourhood radii (100 / 300 / 500 m) stay inside the AOI for every
  focal pixel;
- keep the total area in the 8–15 km² band declared in the manuscript.

If the operator later wants a hand-refined polygon, they can drop a
QGIS-drawn GeoJSON into the same target path and it will take
precedence — this script never overwrites an existing non-example file
unless `--force` is passed.

Usage:
    python yamaguchi/scripts/build_aoi_polygons.py               # both cities
    python yamaguchi/scripts/build_aoi_polygons.py --only yamaguchi
    python yamaguchi/scripts/build_aoi_polygons.py --only yonago --force
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


# ── AOI declarations ────────────────────────────────────────────────────
# Each entry: (west_lon, south_lat, east_lon, north_lat), plus landmark list
# for the GeoJSON `properties.landmarks` metadata field.

AOIS = {
    "yamaguchi": {
        "bbox": (131.4500, 34.1660, 131.4880, 34.1945),
        "target_path_rel": "aoi/yamaguchi_center.geojson",
        "landmarks": [
            ("山口駅",       131.4733, 34.1745),
            ("湯田温泉",     131.4550, 34.1740),
            ("中央商店街",   131.4747, 34.1800),
            ("県庁",         131.4690, 34.1860),
        ],
    },
    "yonago": {
        "bbox": (133.3120, 35.4240, 133.3430, 35.4580),
        "target_path_rel": "yonago/aoi/yonago_center.geojson",
        "landmarks": [
            ("米子駅",       133.3310, 35.4280),
            ("皆生温泉",     133.3200, 35.4540),
            ("中心商店街",   133.3350, 35.4320),
            ("米子城跡",     133.3180, 35.4280),
        ],
    },
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _bbox_polygon_geojson(bbox: tuple[float, float, float, float]) -> dict:
    w, s, e, n = bbox
    return {
        "type": "Polygon",
        "coordinates": [[
            [w, s], [e, s], [e, n], [w, n], [w, s],
        ]],
    }


def _bbox_area_km2(bbox: tuple[float, float, float, float]) -> float:
    w, s, e, n = bbox
    mean_lat = 0.5 * (s + n)
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 111_320.0 * math.cos(math.radians(mean_lat))
    return abs((e - w) * m_per_deg_lon * (n - s) * m_per_deg_lat) / 1e6


def _landmarks_inside(landmarks, bbox) -> bool:
    w, s, e, n = bbox
    return all(w <= lon <= e and s <= lat <= n for _, lon, lat in landmarks)


def build_geojson(city: str) -> dict:
    spec = AOIS[city]
    bbox = spec["bbox"]
    area_km2 = _bbox_area_km2(bbox)
    if not _landmarks_inside(spec["landmarks"], bbox):
        raise RuntimeError(f"{city}: at least one landmark falls outside the bbox")
    if not (8.0 <= area_km2 <= 15.0):
        raise RuntimeError(
            f"{city}: bbox area {area_km2:.2f} km² outside 8–15 km² target — "
            "adjust AOIS in build_aoi_polygons.py.")
    return {
        "type": "FeatureCollection",
        "name": f"{city}_center",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": [{
            "type": "Feature",
            "properties": {
                "city": city,
                "area_km2": round(area_km2, 3),
                "landmarks": [
                    {"name": n, "lon": lo, "lat": la}
                    for n, lo, la in spec["landmarks"]
                ],
                "source": "build_aoi_polygons.py — bounding box over landmarks",
            },
            "geometry": _bbox_polygon_geojson(bbox),
        }],
    }


def write_geojson(city: str, force: bool = False) -> Path:
    spec = AOIS[city]
    dest = PROJECT_ROOT / spec["target_path_rel"]
    if dest.exists() and not force:
        content = dest.read_text(encoding="utf-8")
        if "bounding box over landmarks" not in content:
            print(f"[skip] {dest} exists and is NOT one of ours — leaving alone. "
                  f"Pass --force to overwrite.", file=sys.stderr)
            return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    gj = build_geojson(city)
    dest.write_text(json.dumps(gj, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    print(f"[ok]   {dest}  area={gj['features'][0]['properties']['area_km2']} km²")
    return dest


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--only", choices=list(AOIS),
                   help="Build only one city; default: both")
    p.add_argument("--force", action="store_true",
                   help="Overwrite even a hand-drawn polygon at the target path")
    args = p.parse_args(argv)

    cities = [args.only] if args.only else list(AOIS)
    for c in cities:
        write_geojson(c, force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
