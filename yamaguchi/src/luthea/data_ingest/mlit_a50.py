"""MLIT 国土数値情報 A50 立地適正化計画区域 loader.

Data source: https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A50-v1_0.html

**Two release layouts are supported.** MLIT changed the packaging between
releases, so the loader sniffs whichever is on disk:

*Legacy layout* — one shapefile per prefecture per zone type, encoded in
the filename::

    A50-YY_35-jgd_1_UDA.shp     # 都市機能誘導区域, Yamaguchi
    A50-YY_35-jgd_1_JIA.shp     # 居住誘導区域
    A50-YY_35-jgd_1_URA.shp     # 立地適正化計画区域

*Current layout (A50-20 and later)* — one shapefile per **municipality**,
with the zone type carried in the ``A50_006`` attribute::

    A50-20_35201.shp            # Yamaguchi-shi (municipality code 35201)
    A50-20_35202.shp            # Ube-shi
    ...
    A50_006 == 1  ->  URA (立地適正化計画区域)
    A50_006 == 2  ->  JIA (居住誘導区域)
    A50_006 == 3  ->  UDA (都市機能誘導区域)

Municipality codes are prefixed by the two-digit prefecture code, so
prefecture 35 (Yamaguchi) matches ``A50-*_35???.shp``.

Prefecture codes used by this project: 35 = Yamaguchi, 31 = Tottori.

.. note::
   **Tottori (31) is not published in the A50-20 release.** The loader
   returns an empty GeoDataFrame with ``attrs['unpublished'] = True``
   rather than raising, so the Yonago policy overlay (H8) can degrade
   gracefully. This is a real data gap and is reported as such in the
   manuscript Limitations — never fabricate a substitute polygon.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Literal


ZONE_LABEL = {
    "URA": "立地適正化計画区域",
    "JIA": "居住誘導区域",
    "UDA": "都市機能誘導区域",
}

# A50_006 attribute encoding in the current (A50-20+) layout.
ZONE_ATTR_CODE = {"URA": 1, "JIA": 2, "UDA": 3}

ZONE_ATTR_COLUMN_CANDIDATES = ("A50_006", "a50_006", "A50006")

# Prefectures known to be absent from the A50-20 national release.
UNPUBLISHED_PREFECTURES = {"31"}


def _legacy_paths(base: Path, prefecture_code: str, zone: str) -> list[Path]:
    return sorted(base.rglob(f"A50-*_{prefecture_code}-*_{zone}.shp"))


def _current_paths(base: Path, prefecture_code: str) -> list[Path]:
    """Municipality-level shapefiles whose 5-digit code starts with the
    prefecture code."""
    hits = [p for p in base.rglob("A50-*_*.shp")
            if _municipality_code(p).startswith(prefecture_code)
            and len(_municipality_code(p)) == 5]
    return sorted(hits)


def _municipality_code(path: Path) -> str:
    stem = path.stem                      # e.g. "A50-20_35201"
    if "_" not in stem:
        return ""
    tail = stem.split("_")[-1]
    return tail if tail.isdigit() else ""


def _zone_column(gdf) -> str | None:
    for c in ZONE_ATTR_COLUMN_CANDIDATES:
        if c in gdf.columns:
            return c
    return None


def _empty_like(target_crs: str):
    import geopandas as gpd
    gdf = gpd.GeoDataFrame({"geometry": []}, geometry="geometry",
                           crs="EPSG:6668")
    return gdf.to_crs(target_crs)


def load_zone(base_dir: Path | str,
              prefecture_code: str,
              zone: Literal["UDA", "JIA", "URA"] = "UDA",
              target_crs: str = "EPSG:6690",
              drop_empty_geometry: bool = True):
    """Load one A50 zone for a prefecture, from either release layout.

    Parameters
    ----------
    base_dir : directory holding the unzipped A50 shapefiles (searched
        recursively, so ``.../mlit_a50`` with a ``prefectures/`` subtree
        works).
    prefecture_code : "35" (Yamaguchi) or "31" (Tottori).
    zone : "UDA" (default, needed for H8), "JIA", or "URA".
    target_crs : projected CRS for reliable area / IoU computation.
    drop_empty_geometry : skip null / empty geometries. Several
        municipalities ship empty features; concatenating without this
        guard is what broke the earlier merge attempt.
    """
    import geopandas as gpd
    import pandas as pd

    if zone not in ZONE_LABEL:
        raise ValueError(f"unknown zone {zone!r}; expected one of {list(ZONE_LABEL)}")
    base = Path(base_dir)
    if not base.exists():
        raise FileNotFoundError(f"A50 base directory not found: {base}")

    # 1. Legacy per-zone filenames.
    legacy = _legacy_paths(base, prefecture_code, zone)
    if legacy:
        frames = [gpd.read_file(p) for p in legacy]
        gdf = pd.concat(frames, ignore_index=True)
        return _finalise(gdf, target_crs, drop_empty_geometry, layout="legacy")

    # 2. Current per-municipality layout, filtered on A50_006.
    current = _current_paths(base, prefecture_code)
    if current:
        wanted = ZONE_ATTR_CODE[zone]
        frames = []
        for p in current:
            g = gpd.read_file(p)
            col = _zone_column(g)
            if col is None:
                warnings.warn(f"{p.name}: no A50_006-like column; skipped",
                              RuntimeWarning, stacklevel=2)
                continue
            sel = g[pd.to_numeric(g[col], errors="coerce") == wanted]
            if len(sel):
                frames.append(sel)
        if frames:
            gdf = pd.concat(frames, ignore_index=True)
            return _finalise(gdf, target_crs, drop_empty_geometry,
                             layout="current")
        warnings.warn(
            f"prefecture {prefecture_code}: {len(current)} municipality "
            f"shapefile(s) found but none contain zone {zone} "
            f"(A50_006 == {ZONE_ATTR_CODE[zone]})",
            RuntimeWarning, stacklevel=2)
        out = _empty_like(target_crs)
        out.attrs["zone"] = zone
        out.attrs["prefecture"] = prefecture_code
        return out

    # 3. Nothing on disk for this prefecture.
    if prefecture_code in UNPUBLISHED_PREFECTURES:
        warnings.warn(
            f"prefecture {prefecture_code} is not published in the A50-20 "
            "national release; returning an empty layer. The policy "
            "overlay (H8) must be reported as unavailable for this city — "
            "do not substitute another boundary.",
            RuntimeWarning, stacklevel=2)
        out = _empty_like(target_crs)
        out.attrs["unpublished"] = True
        out.attrs["zone"] = zone
        out.attrs["prefecture"] = prefecture_code
        return out

    raise FileNotFoundError(
        f"No A50 shapefile for prefecture {prefecture_code} under {base}. "
        f"Looked for legacy 'A50-*_{prefecture_code}-*_{zone}.shp' and "
        f"current 'A50-*_{prefecture_code}???.shp'."
    )


def _finalise(gdf, target_crs: str, drop_empty: bool, layout: str):
    if drop_empty:
        gdf = gdf[~gdf.geometry.isna()]
        gdf = gdf[~gdf.geometry.is_empty]
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:6668", allow_override=True)
    out = gdf.to_crs(target_crs)
    out.attrs["layout"] = layout
    return out


def filter_by_city(gdf, city_name_ja: str, name_column: str | None = None):
    """Filter a loaded zone layer to a single city (e.g. '山口市')."""
    if name_column is None:
        for cand in ("A50_004", "A50_003", "shityoumei", "gyousei_na",
                     "city_name"):
            if cand in gdf.columns:
                name_column = cand
                break
        else:
            raise KeyError(
                f"cannot locate a city-name column in {list(gdf.columns)}; "
                "pass name_column explicitly")
    return gdf[gdf[name_column].astype(str).str.contains(city_name_ja)].copy()


def rasterise_to_grid(zone_gdf, ref_raster_path: Path | str):
    """Rasterise the zone polygons onto the reference (30 m) grid,
    returning a boolean array that is True inside the zone."""
    import numpy as np
    import rasterio
    from rasterio.features import rasterize

    with rasterio.open(ref_raster_path) as src:
        transform = src.transform
        out_shape = (src.height, src.width)
        crs = src.crs

    if len(zone_gdf) == 0:
        return np.zeros(out_shape, dtype=bool)

    zone_local = zone_gdf.to_crs(crs)
    shapes = [(geom, 1) for geom in zone_local.geometry
              if geom is not None and not geom.is_empty]
    if not shapes:
        return np.zeros(out_shape, dtype=bool)
    mask = rasterize(shapes=shapes, out_shape=out_shape,
                     transform=transform, fill=0, dtype="uint8")
    return mask.astype(bool)
