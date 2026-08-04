"""e-Stat 統計 GIS 250 m census mesh loader.

Data source: https://www.e-stat.go.jp/gis (国勢調査 2020).
Format: shapefile bundle per prefecture, containing standard-mesh
polygon geometry plus population columns.

The e-Stat schema uses Japanese column names; this module normalises
them to English and returns a GeoDataFrame ready to intersect with the
30 m HIPI raster.
"""

from __future__ import annotations

from pathlib import Path


ESTAT_COLUMN_MAP = {
    "T000846001": "total_pop",
    "T000846002": "male_pop",
    "T000846003": "female_pop",
    "T000846004": "households",
    # Variants seen in released bundles — extend as needed.
    "総人口": "total_pop",
    "男": "male_pop",
    "女": "female_pop",
    "世帯数": "households",
    "65歳以上人口": "elderly_pop",
    "65歳以上": "elderly_pop",
}


def load_mesh(shapefile_or_dir: Path | str,
              target_crs: str = "EPSG:6690"):
    """Load an e-Stat mesh shapefile (or a directory containing one).

    Returns a GeoDataFrame in `target_crs` with normalised English
    column names for the standard population fields.
    """
    import geopandas as gpd
    p = Path(shapefile_or_dir)
    if p.is_dir():
        candidates = list(p.glob("*.shp"))
        if not candidates:
            raise FileNotFoundError(f"No .shp under {p}")
        shp = candidates[0]
    else:
        shp = p

    gdf = gpd.read_file(shp)
    gdf = gdf.rename(columns={k: v for k, v in ESTAT_COLUMN_MAP.items()
                              if k in gdf.columns})
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:6668", allow_override=True)
    return gdf.to_crs(target_crs)


def clip_to_aoi(mesh_gdf, aoi_geojson_path: Path | str):
    """Clip an e-Stat mesh GeoDataFrame to an AOI polygon (GeoJSON path).
    Returns a clipped GeoDataFrame in the same CRS as `mesh_gdf`."""
    import geopandas as gpd
    aoi = gpd.read_file(aoi_geojson_path).to_crs(mesh_gdf.crs)
    return gpd.overlay(mesh_gdf, aoi, how="intersection")
