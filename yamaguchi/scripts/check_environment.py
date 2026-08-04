"""Environment readiness check for the Yamaguchi LUTHEA pipeline.

Run from the repository root:

    python yamaguchi/scripts/check_environment.py

Walks through every prerequisite documented in docs/data_acquisition.md
and prints a checklist with [✓] / [✗] markers and remediation pointers.
Exits with non-zero status if anything is missing — so the script is
CI-friendly.

The check is deliberately tolerant of partial states: a fresh clone can
run this script and get a tidy list of "what to do next".
"""

from __future__ import annotations

import importlib
import json
import os
import platform
import sys
import traceback
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_REF = "yamaguchi/docs/data_acquisition.md"

CHECKS_PASSED: list[str] = []
CHECKS_FAILED: list[tuple[str, str]] = []   # (label, remediation hint)


# ── tiny logging helpers ────────────────────────────────────────────────

def ok(label: str) -> None:
    CHECKS_PASSED.append(label)
    print(f"  [✓] {label}")


def fail(label: str, hint: str) -> None:
    CHECKS_FAILED.append((label, hint))
    print(f"  [✗] {label}")
    print(f"        → {hint}")


def section(name: str) -> None:
    print(f"\n{name}")
    print("-" * len(name))


# ── individual checks ───────────────────────────────────────────────────

def check_python() -> None:
    section("Python environment")
    py_ver = platform.python_version_tuple()
    ok_py = (int(py_ver[0]), int(py_ver[1])) >= (3, 10)
    (ok if ok_py else lambda l: fail(l, "Install Python ≥ 3.10"))(
        f"Python {platform.python_version()}")

    for pkg in ["numpy", "pandas", "scipy", "xarray", "rasterio", "geopandas",
                "matplotlib", "scikit-learn", "xgboost", "shap"]:
        try:
            importlib.import_module(pkg if pkg != "scikit-learn" else "sklearn")
            ok(f"{pkg} importable")
        except ImportError:
            fail(f"{pkg} importable",
                 f"`pip install {pkg}` or `mamba env update -f yamaguchi/env/environment.yml`")


def check_luthea_package() -> None:
    section("luthea package")
    src = PROJECT_ROOT / "src"
    if src.exists() and str(src) not in sys.path:
        sys.path.insert(0, str(src))
    try:
        import luthea
        ok(f"luthea v{luthea.__version__} importable")
    except Exception as exc:
        fail("luthea importable",
             f"Repository layout issue: {exc!r}. Run from repo root.")
        return

    for sub in [
        "luthea.data_ingest.dynamic_world",
        "luthea.data_ingest.landsat_st",
        "luthea.data_ingest.jma",
        "luthea.data_ingest.fdma",
        "luthea.data_ingest.estat",
        "luthea.data_ingest.mlit_a50",
        "luthea.lst.selection",
        "luthea.lst.normalize",
        "luthea.lulc.aggregate",
        "luthea.lulc.transitions",
        "luthea.attribution.matching",
        "luthea.attribution.luthi",
        "luthea.attribution.bootstrap",
        "luthea.attribution.placebo",
        "luthea.attribution.baselines",
        "luthea.attribution.hipi",
        "luthea.attribution.exposure",
        "luthea.ml.xgb_attribution",
        "luthea.ml.shap_layer",
        "luthea.viz.figures",
    ]:
        try:
            importlib.import_module(sub)
        except Exception as exc:
            fail(f"{sub} importable", f"{type(exc).__name__}: {exc}")
            return
    ok("All 20 algorithm modules importable")


def check_earth_engine() -> None:
    section("Google Earth Engine")
    try:
        import ee  # type: ignore
    except ImportError:
        fail("earthengine-api installed",
             "`pip install earthengine-api` "
             f"(see {DOCS_REF} Step 1)")
        return
    ok("earthengine-api importable")

    project = os.environ.get("EE_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        fail("EE_PROJECT environment variable set",
             f"`export EE_PROJECT=<your-project-id>` (see {DOCS_REF} Step 1)")
        return
    ok(f"EE_PROJECT = {project}")

    try:
        ee.Initialize(project=project)
        # Lightweight sanity ping
        _ = ee.Number(42).getInfo()
        ok("ee.Initialize() succeeded, 42 returned")
    except Exception as exc:
        fail("ee.Initialize() succeeds",
             f"Run `earthengine authenticate`. Underlying error: {exc}")


def check_aoi() -> None:
    section("AOI polygon")
    real = PROJECT_ROOT / "aoi" / "yamaguchi_center.geojson"
    example = PROJECT_ROOT / "aoi" / "yamaguchi_center.example.geojson"

    if not real.exists():
        fail(f"AOI file present at {real.relative_to(PROJECT_ROOT)}",
             f"Draw the polygon in QGIS — see {DOCS_REF} Step 2. "
             f"(placeholder example exists at {example.relative_to(PROJECT_ROOT)})")
        return
    ok(f"AOI file present: {real.relative_to(PROJECT_ROOT)}")

    try:
        gj = json.loads(real.read_text(encoding="utf-8"))
    except Exception as exc:
        fail("AOI parses as GeoJSON", f"{type(exc).__name__}: {exc}")
        return

    geom_dict = _extract_first_geometry(gj)
    if geom_dict is None:
        fail("AOI contains a polygon geometry",
             "GeoJSON has no usable geometry; redraw in QGIS")
        return
    coords = _flatten_polygon_coords(geom_dict)
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    centroid = (sum(lons) / len(lons), sum(lats) / len(lats))
    ok(f"AOI geometry type = {geom_dict['type']}, centroid ≈ ({centroid[0]:.3f}, {centroid[1]:.3f})")

    # Yamaguchi central district bounding sanity: lon 131.3-131.6, lat 34.1-34.3
    in_yamaguchi = (131.3 < centroid[0] < 131.7) and (34.0 < centroid[1] < 34.3)
    (ok if in_yamaguchi else lambda l: fail(
        l, f"Centroid not over Yamaguchi (expected lon 131.3-131.7, lat 34.0-34.3); "
           "verify the AOI is in WGS84 (EPSG:4326)"
    ))("AOI centroid is within Yamaguchi extent")

    # Approximate area in km² via crude planar projection
    area_km2 = _approx_polygon_area_km2(coords)
    if 5 <= area_km2 <= 30:
        ok(f"AOI area ≈ {area_km2:.2f} km² (within 5-30 km² target band)")
    else:
        fail(f"AOI area ≈ {area_km2:.2f} km² in [5, 30] km² target",
             "If too small, the central district is not fully covered. "
             "If too large, the 'compact central district' framing breaks "
             "and Landsat scene count explodes. See data_acquisition.md Step 2 pitfall.")


def check_jma() -> None:
    section("JMA / AMeDAS CSVs")
    raw = PROJECT_ROOT / "outputs" / "raw" / "jma"
    daily = raw / "yamaguchi_daily.csv"
    ten = raw / "yamaguchi_10min.csv"

    if not daily.exists():
        fail(f"Daily CSV present at {daily.relative_to(PROJECT_ROOT)}",
             f"Download from JMA portal — see {DOCS_REF} Step 3")
    else:
        ok(f"Daily CSV present: {daily.relative_to(PROJECT_ROOT)}"
           f" ({daily.stat().st_size // 1024} KB)")
        _try_parse_daily(daily)

    if not ten.exists():
        fail(f"AMeDAS 10-min CSV present at {ten.relative_to(PROJECT_ROOT)}",
             f"Download from JMA portal — see {DOCS_REF} Step 4")
    else:
        ok(f"AMeDAS 10-min CSV present: {ten.relative_to(PROJECT_ROOT)}"
           f" ({ten.stat().st_size // 1024} KB)")
        _try_parse_amedas(ten)


def check_output_dirs() -> None:
    section("Output directories")
    for sub in ["aoi", "outputs/lulc", "outputs/lst", "outputs/raw/jma",
                "outputs/raw/estat", "outputs/raw/mlit_a50",
                "outputs/raw/fdma",
                "outputs/matching", "outputs/luthi", "outputs/ml",
                "outputs/hipi", "figures", "tables",
                "yonago/aoi", "yonago/outputs/raw/jma"]:
        d = PROJECT_ROOT / sub
        if d.exists():
            ok(f"{d.relative_to(PROJECT_ROOT)}/")
        else:
            d.mkdir(parents=True, exist_ok=True)
            ok(f"{d.relative_to(PROJECT_ROOT)}/  (created)")


def check_yonago() -> None:
    section("Yonago (second case city)")
    aoi = PROJECT_ROOT / "yonago" / "aoi" / "yonago_center.geojson"
    daily = PROJECT_ROOT / "yonago" / "outputs" / "raw" / "jma" / "yonago_daily.csv"
    ten = PROJECT_ROOT / "yonago" / "outputs" / "raw" / "jma" / "yonago_10min.csv"
    for label, path, step in [
        ("Yonago AOI", aoi, "Step 5.1"),
        ("Yonago daily JMA CSV (68861)", daily, "Step 5.2"),
        ("Yonago AMeDAS 10-min CSV", ten, "Step 5.3"),
    ]:
        if path.exists():
            ok(f"{label}: {path.relative_to(PROJECT_ROOT)}")
        else:
            fail(f"{label} present", f"See {DOCS_REF} {step}")


def check_estat() -> None:
    """e-Stat ingest accepts EITHER a boundary shapefile OR the statistics
    table alone — mesh codes carry their own geometry, so the shapefile
    download is optional."""
    section("e-Stat 250 m mesh census (population)")
    for pref in ("yamaguchi", "tottori"):
        d = PROJECT_ROOT / "outputs" / "raw" / "estat" / f"{pref}_250m_pop_2020"
        if not d.exists():
            fail(f"e-Stat 250 m mesh for {pref}", f"See {DOCS_REF} Step 6")
            continue
        shps = list(d.glob("*.shp"))
        tables = sorted(d.glob("tbl*.txt")) + sorted(d.glob("tbl*.csv"))
        if shps:
            ok(f"{pref}: boundary shapefile {shps[0].name}")
        elif tables:
            ok(f"{pref}: statistics table {tables[0].name} "
               "(geometry derived from mesh codes — no shapefile needed)")
        else:
            fail(f"e-Stat data for {pref} (need *.shp or tbl*.txt)",
                 f"See {DOCS_REF} Step 6")
            continue
        _try_parse_estat(d, pref)


def _try_parse_estat(directory, pref: str) -> None:
    try:
        from luthea.data_ingest.estat import load_mesh_auto
        gdf = load_mesh_auto(directory)
        cols = [c for c in ("total_pop", "elderly_pop", "households")
                if c in gdf.columns]
        ok(f"  {pref}: {len(gdf)} mesh cells parsed; population columns {cols}")
        if "total_pop" not in cols:
            fail(f"  {pref}: 'total_pop' column resolved",
                 "Re-download with 人口（総数） ticked — see "
                 f"{DOCS_REF} Step 6")
    except ImportError:
        fail(f"  {pref}: geopandas needed to parse e-Stat mesh",
             "`pip install geopandas`")
    except Exception as exc:
        fail(f"  {pref}: e-Stat parse", f"{type(exc).__name__}: {exc}")


def check_mlit_a50() -> None:
    """A50 ships in two layouts; accept either. Tottori (31) is absent
    from the A50-20 national release — reported as a known gap, not a
    failure."""
    section("MLIT A50 立地適正化計画 (policy overlay)")
    d = PROJECT_ROOT / "outputs" / "raw" / "mlit_a50"
    if not d.exists():
        fail("A50 directory present", f"See {DOCS_REF} Step 7")
        return

    legacy = list(d.rglob("*_UDA.shp"))
    current = [p for p in d.rglob("A50-*_*.shp")
               if p.stem.split("_")[-1].isdigit()
               and len(p.stem.split("_")[-1]) == 5]

    if legacy:
        ok(f"A50 legacy-layout UDA shapefiles: {len(legacy)}")
    elif current:
        prefs = sorted({p.stem.split("_")[-1][:2] for p in current})
        ok(f"A50 current-layout municipality shapefiles: {len(current)} "
           f"across prefectures {prefs}")
    else:
        fail("A50 shapefiles present (either layout)",
             f"See {DOCS_REF} Step 7")
        return

    _try_load_a50(d, "35", "Yamaguchi", required=True)
    _try_load_a50(d, "31", "Tottori", required=False)


def _try_load_a50(base, code: str, label: str, required: bool) -> None:
    try:
        import warnings as _w
        from luthea.data_ingest.mlit_a50 import load_zone
        with _w.catch_warnings():
            _w.simplefilter("ignore")
            gdf = load_zone(base, code, zone="UDA")
        if len(gdf) > 0:
            ok(f"  {label} (code {code}): {len(gdf)} UDA polygons "
               f"[{gdf.attrs.get('layout', 'n/a')} layout]")
        elif gdf.attrs.get("unpublished"):
            ok(f"  {label} (code {code}): NOT PUBLISHED in A50-20 — "
               "H8 policy overlay will be reported as unavailable "
               "(known data gap, documented in Limitations)")
        elif required:
            fail(f"  {label} (code {code}) UDA polygons found",
                 "Shapefiles exist but contain no A50_006 == 3 features; "
                 f"verify the download per {DOCS_REF} Step 7")
        else:
            ok(f"  {label} (code {code}): no UDA polygons (optional)")
    except ImportError:
        fail("  geopandas needed to parse A50", "`pip install geopandas`")
    except Exception as exc:
        if required:
            fail(f"  {label} A50 load", f"{type(exc).__name__}: {exc}")
        else:
            ok(f"  {label} A50 unavailable ({type(exc).__name__}) — optional")


def check_fdma() -> None:
    """FDMA feeds only the correlation-only sub-analysis (§ 4.7), which is
    auxiliary. Accept any mix of XLSX / CSV / PDF so that PDF-only release
    years never block the main pipeline; report which years will need
    manual transcription."""
    section("FDMA heatstroke transports (correlation-only, auxiliary)")
    d = PROJECT_ROOT / "outputs" / "raw" / "fdma"
    if not d.exists():
        fail("FDMA directory present", f"See {DOCS_REF} Step 8")
        return

    files = sorted(p for p in d.glob("heatstroke_*.*")
                   if p.suffix.lower() in {".xlsx", ".xls", ".csv", ".pdf"})
    if not files:
        fail("FDMA files present", f"See {DOCS_REF} Step 8")
        return

    def _year(p) -> int | None:
        digits = "".join(c for c in p.stem if c.isdigit())[:4]
        return int(digits) if len(digits) == 4 else None

    years = sorted({y for y in (_year(p) for p in files) if y})
    parsable = [p for p in files if p.suffix.lower() != ".pdf"]
    pdf_only_years = sorted({_year(p) for p in files
                             if p.suffix.lower() == ".pdf"}
                            - {_year(p) for p in parsable})

    if len(years) >= 8:
        ok(f"FDMA files: {len(files)} covering years {years[0]}–{years[-1]}")
        if pdf_only_years:
            ok(f"  note: {pdf_only_years} are PDF-only — those years need "
               "manual transcription before § 4.7; the main pipeline is "
               "unaffected")
    else:
        fail(f"FDMA year coverage (found {len(years)} of 10 years)",
             f"See {DOCS_REF} Step 8; need at least 8 of 2016–2025 "
             "(PDF counts toward coverage)")


# ── helpers ─────────────────────────────────────────────────────────────

def _extract_first_geometry(gj: dict):
    t = gj.get("type")
    if t == "FeatureCollection":
        feats = gj.get("features") or []
        return feats[0]["geometry"] if feats else None
    if t == "Feature":
        return gj["geometry"]
    if t in {"Polygon", "MultiPolygon"}:
        return gj
    return None


def _flatten_polygon_coords(geom: dict) -> list[tuple[float, float]]:
    if geom["type"] == "Polygon":
        return [tuple(pt) for pt in geom["coordinates"][0]]
    if geom["type"] == "MultiPolygon":
        out: list[tuple[float, float]] = []
        for poly in geom["coordinates"]:
            out.extend(tuple(pt) for pt in poly[0])
        return out
    return []


def _approx_polygon_area_km2(coords: list[tuple[float, float]]) -> float:
    """Crude shoelace area with a per-latitude planar approximation; good
    enough for the 5-30 km² range we care about."""
    import math
    if len(coords) < 4:
        return 0.0
    mean_lat = sum(c[1] for c in coords) / len(coords)
    m_per_deg_lat = 111_320.0
    m_per_deg_lon = 111_320.0 * math.cos(math.radians(mean_lat))
    xy = [(c[0] * m_per_deg_lon, c[1] * m_per_deg_lat) for c in coords]
    a = 0.0
    for i in range(len(xy)):
        x1, y1 = xy[i]
        x2, y2 = xy[(i + 1) % len(xy)]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0 / 1e6


def _try_parse_daily(path: Path) -> None:
    try:
        from luthea.data_ingest.jma import load_daily
        df = load_daily(path)
        years = sorted({d.year for d in df.index})
        ok(f"  daily CSV parses, {len(df)} rows, years={years[0]}–{years[-1]}")
        for col in ("t_max", "precip_mm", "sunshine_h"):
            if col in df.columns:
                ok(f"  column '{col}' present")
            else:
                fail(f"  column '{col}' present",
                     "Re-download with the columns listed in data_acquisition.md Step 3")
    except Exception as exc:
        fail("  daily CSV parses cleanly",
             f"{type(exc).__name__}: {exc}\n"
             f"        full traceback:\n{traceback.format_exc(limit=2)}")


def _try_parse_amedas(path: Path) -> None:
    try:
        from luthea.data_ingest.jma import load_amedas_10min
        df = load_amedas_10min(path)
        years = sorted({t.year for t in df.index})
        ok(f"  10-min CSV parses, {len(df)} rows, years={years[0]}–{years[-1]}")
        if "t_air" in df.columns:
            ok("  column 't_air' present")
        else:
            fail("  column 't_air' present",
                 "Ensure 気温 was ticked at JMA portal Step 4")
    except Exception as exc:
        fail("  10-min CSV parses cleanly",
             f"{type(exc).__name__}: {exc}")


# ── entry point ─────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 70)
    print("  Yamaguchi LUTHEA — environment readiness check")
    print("=" * 70)

    check_python()
    check_luthea_package()
    check_earth_engine()
    check_output_dirs()
    check_aoi()
    check_jma()
    check_yonago()
    check_estat()
    check_mlit_a50()
    check_fdma()

    print()
    print("=" * 70)
    print(f"  Passed: {len(CHECKS_PASSED)}    Failed: {len(CHECKS_FAILED)}")
    print("=" * 70)

    if CHECKS_FAILED:
        print("\nThings to fix before running the pipeline:")
        for label, hint in CHECKS_FAILED:
            print(f"  • {label}")
            print(f"      → {hint}")
        print(f"\nDetailed guidance: {DOCS_REF}")
        return 1

    print(f"\nAll checks passed — you can now run:")
    print("    luthea ingest-lst --dry-run    # sanity-check Landsat scene list")
    print("    luthea ingest-dw               # 10 Drive tasks for 2016-2025 LULC")
    print("    luthea ingest-lst              # 30-60 Drive tasks for Landsat LST")
    return 0


if __name__ == "__main__":
    sys.exit(main())
