"""Pull Landsat 8/9 Collection 2 Level-2 Surface Temperature scenes from GEE.

Applies QA_PIXEL cloud / shadow / cirrus mask, converts the thermal band
to Celsius via the official C2 L2 ST scale + offset (manuscript Eq. 3),
clips to AOI, and exports each surviving scene as a separate 30 m
GeoTIFF.

Plan reference: Step 3 of /root/.claude/plans/token-token-quiet-bachman.md
Manuscript reference: § 3.3 (weather-normalised LST), Eq. 3.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from ..config import (CRS_WORK, LANDSAT_ST_OFFSET, LANDSAT_ST_SCALE,
                      LST_RES_M, SUMMER_MONTHS, YEAR_END, YEAR_START)
from ._gee import init_ee, load_aoi_geojson, to_ee_geometry, utc_date_string


L8_COLLECTION = "LANDSAT/LC08/C02/T1_L2"
L9_COLLECTION = "LANDSAT/LC09/C02/T1_L2"

# QA_PIXEL bit positions for cloud-family flags (Landsat C2 product guide).
QA_BITS_CLOUD_FAMILY: tuple[int, ...] = (1, 2, 3, 4)  # dilated, cirrus, cloud, shadow
SCENE_CLOUD_COVER_MAX = 50.0  # property-level pre-filter; per-pixel mask still applies


def scale_st_celsius(image):
    """ST_B10 (digital-number) → LST in °C (manuscript Eq. 3)."""
    import ee
    lst = (image.select("ST_B10")
           .multiply(LANDSAT_ST_SCALE)
           .add(LANDSAT_ST_OFFSET)
           .subtract(273.15)
           .rename("LST_C"))
    return lst.copyProperties(image, [
        "system:time_start", "CLOUD_COVER",
        "WRS_PATH", "WRS_ROW", "LANDSAT_SCENE_ID", "SPACECRAFT_ID",
    ])


def mask_qa(image, bits: tuple[int, ...] = QA_BITS_CLOUD_FAMILY):
    """Drop pixels where any of `bits` is set in QA_PIXEL.

    Bit ordering for Landsat 8/9 Collection 2 Level-2 (per USGS QA spec):
      bit 1 = dilated cloud, bit 2 = cirrus, bit 3 = cloud, bit 4 = cloud shadow.
    """
    import ee
    qa = image.select("QA_PIXEL")
    mask = ee.Image(1)
    for b in bits:
        mask = mask.And(qa.bitwiseAnd(1 << b).eq(0))
    return image.updateMask(mask)


def qa_mask_numpy(qa_array: np.ndarray,
                  bits: tuple[int, ...] = QA_BITS_CLOUD_FAMILY) -> np.ndarray:
    """Pure-numpy mirror of `mask_qa`'s bit logic, for unit testing.

    Returns a boolean array where True means "keep this pixel".
    """
    qa = np.asarray(qa_array, dtype=np.int64)
    keep = np.ones_like(qa, dtype=bool)
    for b in bits:
        keep &= (qa & (1 << b)) == 0
    return keep


def collection_for_aoi(year_start: int, year_end: int, aoi_geometry,
                       months: tuple[int, ...] = SUMMER_MONTHS):
    """Return a merged LC08 + LC09 collection of LST scenes (°C) clipped
    to `aoi_geometry`, with QA-pixel cloud masking applied."""
    import ee
    start = f"{year_start}-{min(months):02d}-01"
    end_month = max(months) + 1
    end_year = year_end + 1 if end_month > 12 else year_end
    end_month = 1 if end_month > 12 else end_month
    end = f"{end_year}-{end_month:02d}-01"

    def _prep(image):
        return scale_st_celsius(mask_qa(image)).clip(aoi_geometry)

    l8 = ee.ImageCollection(L8_COLLECTION)
    l9 = ee.ImageCollection(L9_COLLECTION)
    merged = l8.merge(l9)
    return (merged
            .filterBounds(aoi_geometry)
            .filterDate(start, end)
            .filter(ee.Filter.calendarRange(min(months), max(months), "month"))
            .filter(ee.Filter.lt("CLOUD_COVER", SCENE_CLOUD_COVER_MAX))
            .map(_prep))


def export_scenes(aoi_geojson_path: Path,
                  year_start: int = YEAR_START,
                  year_end: int = YEAR_END,
                  drive_folder: str = "luthea_lst",
                  scale: float = LST_RES_M,
                  crs: str = CRS_WORK,
                  project: str | None = None,
                  dry_run: bool = False) -> list[dict]:
    """Submit one Drive export per surviving scene. Returns a list of
    {date, scene_id, task_id} dicts. If `dry_run=True`, lists scenes
    without submitting any tasks (useful for sanity-checking the filter)."""
    init_ee(project)
    import ee
    geom = to_ee_geometry(load_aoi_geojson(aoi_geojson_path))
    col = collection_for_aoi(year_start, year_end, geom)

    n = int(col.size().getInfo())
    if n == 0:
        return []

    image_list = col.toList(n)
    out = []
    for i in range(n):
        image = ee.Image(image_list.get(i))
        time_start = int(image.get("system:time_start").getInfo())
        date = utc_date_string(time_start)
        scene_id = image.get("LANDSAT_SCENE_ID").getInfo()
        record = {"date": date, "scene_id": scene_id, "task_id": None}
        if not dry_run:
            task = ee.batch.Export.image.toDrive(
                image=image.toFloat(),
                description=f"lst_{date}_{scene_id}",
                folder=drive_folder,
                fileNamePrefix=f"lst_{date}_{scene_id}",
                region=geom,
                scale=scale,
                crs=crs,
                maxPixels=int(1e9),
            )
            task.start()
            record["task_id"] = task.id
        out.append(record)
    return out
