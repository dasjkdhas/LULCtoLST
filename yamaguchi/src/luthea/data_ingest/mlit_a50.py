"""MLIT 国土数値情報 A50 立地適正化計画区域 loader.

Data source: https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A50-v1_0.html

Family of shapefiles under the same A50 dataset:
  - **UDA** = 都市機能誘導区域 (Urban function inducement zone) — H8 needs this.
  - **JIA** = 居住誘導区域 (Residential inducement zone)
  - **URA** = 立地適正化計画区域 (outer plan boundary)

Prefecture codes: 35 = Yamaguchi, 31 = Tottori.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal


ZONE_CODE = {
    "UDA": "都市機能誘導区域",
    "JIA": "居住誘導区域",
    "URA": "立地適正化計画区域",
}


def load_zone(base_dir: Path | str,
              prefecture_code: str,
              zone: Literal["UDA", "JIA", "URA"] = "UDA",
              target_crs: str = "EPSG:6690"):
    """Load one A50 zone shapefile for a prefecture.

    Parameters
    ----------
    base_dir : directory holding the unzipped A50 shapefiles.
    prefecture_code : e.g. "35" (Yamaguchi) or "31" (Tottori).
    zone : "UDA" (default, for H8), "JIA", or "URA".
    target_crs : projected CRS for reliable area / IoU computations.
    """
    import geopandas as gpd
    if zone not in ZONE_CODE:
        raise ValueError(f"unknown zone {zone!r}; expected one of {list(ZONE_CODE)}")
    base = Path(base_dir)
    pattern = f"A50-*_{prefecture_code}-*_{zone}.shp"
    candidates = list(base.glob(pattern))
    if not candidates:
        alt = list(base.glob(f"A50-*_{prefecture_code}-*.shp"))
        raise FileNotFoundError(
            f"No {zone} shapefile matching {pattern} under {base}. "
            f"Available for prefecture {prefecture_code}: "
            f"{[c.name for c in alt]}"
        )
    gdf = gpd.read_file(candidates[0])
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:6668", allow_override=True)
    return gdf.to_crs(target_crs)


def filter_by_city(gdf, city_name_ja: str, name_column: str = "A50_004"):
    """Filter the loaded zone to a single city (e.g. '山口市' or '米子市').

    The exact column name varies by A50 release; pass `name_column` if
    the default fails."""
    if name_column not in gdf.columns:
        for cand in ("A50_004", "shityoumei", "gyousei_na", "city_name"):
            if cand in gdf.columns:
                name_column = cand
                break
        else:
            raise KeyError(
                f"cannot locate city-name column in {list(gdf.columns)}"
            )
    return gdf[gdf[name_column].astype(str).str.contains(city_name_ja)].copy()


def rasterise_to_grid(zone_gdf, ref_raster_path: Path | str):
    """Rasterise the zone polygon onto the reference (30 m) grid,
    returning a boolean array True inside the zone."""
    import rasterio
    from rasterio.features import rasterize
    with rasterio.open(ref_raster_path) as src:
        transform = src.transform
        out_shape = (src.height, src.width)
        crs = src.crs
    zone_local = zone_gdf.to_crs(crs)
    shapes = ((geom, 1) for geom in zone_local.geometry if geom is not None)
    mask = rasterize(shapes=shapes, out_shape=out_shape,
                     transform=transform, fill=0, dtype="uint8")
    return mask.astype(bool)
