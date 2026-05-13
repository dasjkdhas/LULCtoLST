"""Shared helpers for GEE-dependent ingestion modules.

Key design choices:

* `ee` is imported lazily inside `init_ee()` so that the wider `luthea`
  package remains importable on machines without `earthengine-api`.
* AOI loading is GEE-free — pure GeoJSON parsing into a dict; only when
  the user actually triggers an export does the helper wrap it in
  `ee.Geometry`.
* Project identifier comes from the env var `EE_PROJECT` (modern Earth
  Engine requires explicit project context) and may be overridden in
  function calls.

All ingest modules build on these primitives.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def init_ee(project: str | None = None) -> None:
    """Initialise Earth Engine. Idempotent: re-calling is cheap.

    Resolution order for the GEE project id:
      1. explicit `project` argument
      2. env var `EE_PROJECT`
      3. env var `GOOGLE_CLOUD_PROJECT`
      4. None — GEE will use the user's default registered project, if any
    """
    import ee  # delayed
    project = (
        project
        or os.environ.get("EE_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
    )
    try:
        ee.Initialize(project=project) if project else ee.Initialize()
    except Exception as exc:  # pragma: no cover - GEE init paths are env-specific
        raise RuntimeError(
            "ee.Initialize() failed. Run `earthengine authenticate` and set "
            "EE_PROJECT to a project that has Earth Engine enabled."
        ) from exc


def load_aoi_geojson(path: Path | str) -> dict[str, Any]:
    """Parse a GeoJSON file (FeatureCollection / Feature / Geometry) and
    return a plain geometry dict in WGS84. Does **not** import `ee`."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        gj = json.load(fh)

    if gj.get("type") == "FeatureCollection":
        features = gj.get("features") or []
        if not features:
            raise ValueError(f"{path}: empty FeatureCollection")
        if len(features) == 1:
            geom = features[0]["geometry"]
        else:
            # union via a GeometryCollection; ee.Geometry(...) accepts this
            geom = {
                "type": "GeometryCollection",
                "geometries": [f["geometry"] for f in features],
            }
    elif gj.get("type") == "Feature":
        geom = gj["geometry"]
    elif gj.get("type") in {"Polygon", "MultiPolygon", "GeometryCollection"}:
        geom = gj
    else:
        raise ValueError(f"{path}: unsupported GeoJSON top-level type {gj.get('type')!r}")

    return geom


def to_ee_geometry(geom_dict: dict[str, Any]):
    """Wrap a geometry dict in `ee.Geometry`. Requires GEE imported."""
    import ee
    return ee.Geometry(geom_dict)


def utc_date_string(epoch_ms: int) -> str:
    """`system:time_start` (epoch ms) → 'YYYYMMDD' UTC string for filenames."""
    import datetime as dt
    return dt.datetime.utcfromtimestamp(epoch_ms / 1000).strftime("%Y%m%d")
