"""Pull Landsat 8/9 Collection 2 Level-2 Surface Temperature scenes from GEE.

Apply QA_PIXEL cloud/shadow/cirrus mask, scale ST_B10 to Celsius, clip to AOI,
export per-scene GeoTIFFs.

Plan reference: Step 3 of /root/.claude/plans/token-token-quiet-bachman.md
"""

from __future__ import annotations

from pathlib import Path

from ..config import LANDSAT_ST_OFFSET, LANDSAT_ST_SCALE


def scale_st_celsius(image):
    """Apply (DN * scale + offset) - 273.15."""
    raise NotImplementedError


def mask_qa(image):
    """Drop cloud, cloud_shadow, cirrus, dilated_cloud via QA_PIXEL bits."""
    raise NotImplementedError


def collection_for_aoi(year_start: int, year_end: int, aoi_geojson_path: Path):
    """Return merged LC08+LC09 C02 L2 collection filtered to AOI/date/months."""
    raise NotImplementedError


def export_scenes(year_start: int, year_end: int, aoi_geojson_path: Path,
                  drive_folder: str) -> list[str]:
    """Export each surviving scene as <yyyymmdd>.tif of LST in Celsius."""
    raise NotImplementedError
