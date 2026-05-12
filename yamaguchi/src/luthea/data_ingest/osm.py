"""OSM extracts: road network and (optional) building footprints.

Building footprints inside Japan are better sourced from
基盤地図情報「建物の外周線」 (GSI). OSM is used here for roads and as a
fallback for buildings.

Plan reference: Step 1 / Step 7.
"""

from __future__ import annotations
from pathlib import Path

import geopandas as gpd


def fetch_roads(aoi_geojson_path: Path) -> gpd.GeoDataFrame:
    """Use osmnx to download highways within AOI; return GeoDataFrame in WGS84."""
    raise NotImplementedError


def fetch_buildings(aoi_geojson_path: Path) -> gpd.GeoDataFrame:
    """OSM building polygons within AOI (fallback)."""
    raise NotImplementedError
