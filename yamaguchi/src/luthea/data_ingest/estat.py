"""e-Stat 統計 GIS census mesh loader.

Data source: https://www.e-stat.go.jp/gis (国勢調査 2020, statsId T001142,
5次メッシュ = 250 m, JGD2011).

Two ingest paths are supported:

1. **Statistics table only** (`load_mesh_from_stat_table`) — the TXT/CSV
   downloaded from the 統計データダウンロード tab. **No boundary
   shapefile is required**: Japanese standard mesh codes encode their own
   geometry, so the 250 m polygon is derived arithmetically from the
   10-digit KEY_CODE. This is the preferred path — it removes a whole
   manual download step.

2. **Boundary shapefile** (`load_mesh`) — if the operator has separately
   downloaded the 境界データ shapefile, it is used directly.

`load_mesh_auto` picks whichever is available in a directory.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ESTAT_COLUMN_MAP = {
    # By column code (schema T001142, 人口及び世帯)
    "T001142001": "total_pop",
    "T001142002": "male_pop",
    "T001142003": "female_pop",
    "T001142004": "households",
    # By Japanese label — matched against the second header row.
    "人口（総数）": "total_pop",
    "人口(総数)": "total_pop",
    "総人口": "total_pop",
    "男": "male_pop",
    "女": "female_pop",
    "世帯総数": "households",
    "世帯数": "households",
    "65歳以上人口": "elderly_pop",
    "65歳以上人口 総数": "elderly_pop",
    "65歳以上": "elderly_pop",
}

# e-Stat marks suppressed / secret cells with these tokens.
MISSING_TOKENS = {"*", "-", "X", "x", "－", "＊", ""}


# ── Mesh-code geometry ──────────────────────────────────────────────────

def mesh_code_to_bbox(code: str) -> tuple[float, float, float, float]:
    """Convert a Japanese standard mesh code to (west, south, east, north)
    in WGS84 degrees.

    Supports 1st (4 digits, 80 km), 2nd (6, 10 km), 3rd (8, 1 km),
    4th (9, 500 m) and 5th (10, 250 m) mesh levels.

    Reference: JIS X 0410 地域メッシュコード.
    """
    code = str(code).strip()
    if len(code) < 4 or not code.isdigit():
        raise ValueError(f"not a mesh code: {code!r}")

    # 1st mesh: first two digits = lat × 1.5, next two = lon − 100
    lat = int(code[0:2]) / 1.5
    lon = int(code[2:4]) + 100.0
    dlat, dlon = 2.0 / 3.0, 1.0

    if len(code) >= 6:                       # 2nd mesh (10 km): 8 × 8 split
        lat += int(code[4]) * dlat / 8.0
        lon += int(code[5]) * dlon / 8.0
        dlat, dlon = dlat / 8.0, dlon / 8.0

    if len(code) >= 8:                       # 3rd mesh (1 km): 10 × 10 split
        lat += int(code[6]) * dlat / 10.0
        lon += int(code[7]) * dlon / 10.0
        dlat, dlon = dlat / 10.0, dlon / 10.0

    for idx in (8, 9):                       # 4th (500 m), 5th (250 m)
        if len(code) >= idx + 1:
            q = int(code[idx])
            if q not in (1, 2, 3, 4):
                raise ValueError(f"invalid quadrant digit {q} in {code!r}")
            dlat, dlon = dlat / 2.0, dlon / 2.0
            lat += ((q - 1) // 2) * dlat
            lon += ((q - 1) % 2) * dlon

    return lon, lat, lon + dlon, lat + dlat


def mesh_code_to_polygon(code: str):
    """Shapely box for one mesh code."""
    from shapely.geometry import box
    return box(*mesh_code_to_bbox(code))


# ── Statistics-table ingest (no shapefile needed) ───────────────────────

def _read_stat_table(path: Path) -> pd.DataFrame:
    """Read an e-Stat mesh statistics TXT/CSV with its two header rows."""
    for enc in ("utf-8-sig", "cp932", "shift_jis"):
        try:
            head = pd.read_csv(path, encoding=enc, nrows=2, header=None,
                               dtype=str)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise UnicodeDecodeError("estat", b"", 0, 1, f"cannot decode {path}")

    codes = [str(c).strip() for c in head.iloc[0].tolist()]
    labels = ([str(c).strip() for c in head.iloc[1].tolist()]
              if len(head) > 1 else [""] * len(codes))

    # If the second row already looks like data (starts with a mesh code),
    # there is no Japanese label row.
    has_label_row = not (labels and labels[0].isdigit() and len(labels[0]) >= 8)

    df = pd.read_csv(path, encoding=enc, dtype=str,
                     skiprows=2 if has_label_row else 1, header=None)
    df.columns = codes[:df.shape[1]]

    rename: dict[str, str] = {}
    for i, code in enumerate(codes[:df.shape[1]]):
        label = labels[i] if has_label_row and i < len(labels) else ""
        if code in ESTAT_COLUMN_MAP:
            rename[code] = ESTAT_COLUMN_MAP[code]
        elif label in ESTAT_COLUMN_MAP:
            rename[code] = ESTAT_COLUMN_MAP[label]
    df = df.rename(columns=rename)

    key_col = next((c for c in df.columns
                    if str(c).upper() in {"KEY_CODE", "MESH_ID", "MESHCODE"}),
                   df.columns[0])
    df = df.rename(columns={key_col: "mesh_id"})
    df["mesh_id"] = df["mesh_id"].astype(str).str.strip()
    df = df[df["mesh_id"].str.isdigit()]

    for col in ("total_pop", "male_pop", "female_pop",
                "households", "elderly_pop"):
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].where(~df[col].isin(MISSING_TOKENS)), errors="coerce")
    return df.reset_index(drop=True)


def load_mesh_from_stat_table(path: Path | str,
                              target_crs: str = "EPSG:6690"):
    """Build a GeoDataFrame directly from an e-Stat statistics table by
    deriving each 250 m polygon from its mesh code. No boundary
    shapefile required.
    """
    import geopandas as gpd
    p = Path(path)
    if p.is_dir():
        candidates = (sorted(p.glob("tbl*.txt")) + sorted(p.glob("tbl*.csv"))
                      + sorted(p.glob("*.txt")) + sorted(p.glob("*.csv")))
        if not candidates:
            raise FileNotFoundError(f"no e-Stat statistics table under {p}")
        p = candidates[0]

    df = _read_stat_table(p)
    geometry = [mesh_code_to_polygon(c) for c in df["mesh_id"]]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    return gdf.to_crs(target_crs)


# ── Boundary-shapefile ingest (optional alternative) ────────────────────

def load_mesh(shapefile_or_dir: Path | str, target_crs: str = "EPSG:6690"):
    """Load an e-Stat mesh *boundary shapefile* (if the operator chose to
    download one) and normalise its column names."""
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


def load_mesh_auto(directory: Path | str, target_crs: str = "EPSG:6690"):
    """Prefer a boundary shapefile if present; otherwise derive geometry
    from the statistics table's mesh codes."""
    d = Path(directory)
    if any(d.glob("*.shp")):
        return load_mesh(d, target_crs=target_crs)
    return load_mesh_from_stat_table(d, target_crs=target_crs)


def clip_to_aoi(mesh_gdf, aoi_geojson_path: Path | str):
    """Clip an e-Stat mesh GeoDataFrame to an AOI polygon (GeoJSON path)."""
    import geopandas as gpd
    aoi = gpd.read_file(aoi_geojson_path).to_crs(mesh_gdf.crs)
    return gpd.overlay(mesh_gdf, aoi, how="intersection")
