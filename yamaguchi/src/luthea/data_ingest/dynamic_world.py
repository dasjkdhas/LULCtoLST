"""Pull Dynamic World V1 annual LULC composites from Google Earth Engine.

Output: one 10 m GeoTIFF per year (configured in luthea.config), 9 LULC
classes, clipped to AOI, exported via Drive.

Plan reference: Step 2 of /root/.claude/plans/token-token-quiet-bachman.md
Manuscript reference: § 3.2 (trajectory identification), Eq. 1.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ..config import CRS_WORK, DW_NATIVE_RES_M, SUMMER_MONTHS, YEAR_END, YEAR_START
from ._gee import init_ee, load_aoi_geojson, to_ee_geometry


DW_COLLECTION = "GOOGLE/DYNAMICWORLD/V1"


def annual_mode_composite(year: int, aoi_geometry, months: tuple[int, ...] = SUMMER_MONTHS):
    """Return an ee.Image: per-pixel mode label across `months` of `year`,
    clipped to `aoi_geometry`. Single 'label' band, 10 m, uint8.
    """
    import ee
    start = f"{year}-{min(months):02d}-01"
    end_month = max(months) + 1
    end_year = year + 1 if end_month > 12 else year
    end_month = 1 if end_month > 12 else end_month
    end = f"{end_year}-{end_month:02d}-01"

    col = (
        ee.ImageCollection(DW_COLLECTION)
        .filterBounds(aoi_geometry)
        .filterDate(start, end)
        .select("label")
    )
    return col.mode().clip(aoi_geometry).toUint8().rename(f"lulc_{year}")


def export_year(year: int, aoi_geojson_path: Path,
                drive_folder: str = "luthea_dw",
                scale: float = DW_NATIVE_RES_M,
                crs: str = CRS_WORK,
                project: str | None = None) -> str:
    """Submit a Drive export task; return the task id for monitoring."""
    init_ee(project)
    import ee
    geom = to_ee_geometry(load_aoi_geojson(aoi_geojson_path))
    image = annual_mode_composite(year, geom)
    task = ee.batch.Export.image.toDrive(
        image=image,
        description=f"dw_lulc_{year}",
        folder=drive_folder,
        fileNamePrefix=f"dw_lulc_{year}",
        region=geom,
        scale=scale,
        crs=crs,
        maxPixels=int(1e9),
    )
    task.start()
    return task.id


def export_all(aoi_geojson_path: Path,
               years: Iterable[int] | None = None,
               drive_folder: str = "luthea_dw",
               scale: float = DW_NATIVE_RES_M,
               crs: str = CRS_WORK,
               project: str | None = None) -> list[str]:
    """Batch export across all configured years. Returns list of task ids."""
    years = list(years) if years is not None else list(range(YEAR_START, YEAR_END + 1))
    return [export_year(y, aoi_geojson_path, drive_folder, scale, crs, project)
            for y in years]
