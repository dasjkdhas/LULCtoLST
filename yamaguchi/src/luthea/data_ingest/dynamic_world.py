"""Pull Dynamic World V1 yearly LULC composites from Google Earth Engine.

Expected output: one 10 m GeoTIFF per year (2016–2025), 9 LULC classes,
clipped to AOI, exported via Drive or GCS.

Plan reference: Step 2 of /root/.claude/plans/token-token-quiet-bachman.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

# import ee  # delayed import — call ee.Initialize() in caller


def annual_mode_composite(year: int, aoi_geojson_path: Path):
    """Return an ee.Image: per-pixel mode label across SUMMER_MONTHS of `year`.

    Steps inside:
      1. Filter GOOGLE/DYNAMICWORLD/V1 by AOI bbox and date range.
      2. Take the 'label' band.
      3. Reduce by mode.
      4. Clip to AOI geometry.

    Returns
    -------
    ee.Image
        Single-band uint8 LULC label, 10 m.
    """
    raise NotImplementedError


def export_year(year: int, aoi_geojson_path: Path, drive_folder: str) -> str:
    """Submit Drive export task; return task id for monitoring."""
    raise NotImplementedError


def export_all(years: Iterable[int], aoi_geojson_path: Path, drive_folder: str) -> list[str]:
    """Batch export wrapper."""
    return [export_year(y, aoi_geojson_path, drive_folder) for y in years]
