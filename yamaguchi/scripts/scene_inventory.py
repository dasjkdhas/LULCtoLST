"""Join the Landsat scene list to the JMA daily record and report how many
scenes survive the typical / extreme day filters, per epoch.

This is the **statistical power check** that must pass before any LUTHI
estimate is trustworthy: the α/β contrast needs at least
``MIN_SCENES_PER_EPOCH_SCENARIO`` scenes in every (epoch × scenario)
cell of the design.

Usage (from the repository root, with EE_PROJECT exported):

    python yamaguchi/scripts/scene_inventory.py                      # Yamaguchi
    python yamaguchi/scripts/scene_inventory.py --city yonago        # Yonago
    python yamaguchi/scripts/scene_inventory.py --json out.json      # machine-readable

The scene list is obtained from Earth Engine via the same filter the
pipeline uses (``ingest-lst --dry-run`` equivalent), so the inventory
cannot drift from what will actually be ingested.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from luthea.config import (EPOCH_EARLY, EPOCH_LATE, EPOCH_MID,          # noqa: E402
                           MIN_SCENES_PER_EPOCH_SCENARIO, YEAR_END,
                           YEAR_START)

CITIES = {
    "yamaguchi": {
        "aoi": PROJECT_ROOT / "aoi" / "yamaguchi_center.geojson",
        "daily": PROJECT_ROOT / "outputs" / "raw" / "jma" / "yamaguchi_daily.csv",
        "amedas": PROJECT_ROOT / "outputs" / "raw" / "jma" / "yamaguchi_10min.csv",
    },
    "yonago": {
        "aoi": PROJECT_ROOT / "yonago" / "aoi" / "yonago_center.geojson",
        "daily": PROJECT_ROOT / "yonago" / "outputs" / "raw" / "jma" / "yonago_daily.csv",
        "amedas": PROJECT_ROOT / "yonago" / "outputs" / "raw" / "jma" / "yonago_10min.csv",
    },
}


def epoch_of(year: int) -> str:
    if year in EPOCH_EARLY:
        return "t0_early"
    if year in EPOCH_LATE:
        return "t1_late"
    if year in EPOCH_MID:
        return "mid"
    return "outside"


def landsat_dates(aoi_path: Path, project: str | None) -> list[dict]:
    """Return [{date, scene_id, cloud_cover}] using the pipeline's own filter."""
    from luthea.data_ingest._gee import (init_ee, load_aoi_geojson,
                                         to_ee_geometry, utc_date_string)
    from luthea.data_ingest.landsat_st import collection_for_aoi
    init_ee(project)
    import ee

    geom = to_ee_geometry(load_aoi_geojson(aoi_path))
    col = collection_for_aoi(YEAR_START, YEAR_END, geom)
    n = int(col.size().getInfo())
    if n == 0:
        return []
    lst = col.toList(n)
    out = []
    for i in range(n):
        img = ee.Image(lst.get(i))
        props = img.toDictionary(
            ["system:time_start", "CLOUD_COVER", "LANDSAT_SCENE_ID",
             "SPACECRAFT_ID"]).getInfo()
        out.append({
            "date": utc_date_string(int(props["system:time_start"])),
            "scene_id": props.get("LANDSAT_SCENE_ID"),
            "spacecraft": props.get("SPACECRAFT_ID"),
            "cloud_cover": props.get("CLOUD_COVER"),
        })
    return sorted(out, key=lambda r: r["date"])


def classify(scenes: list[dict], daily_csv: Path, amedas_csv: Path) -> "pd.DataFrame":
    """Attach JMA meteorology to each scene and apply the day-selection rules."""
    import pandas as pd
    from luthea.data_ingest.jma import load_amedas_10min, load_daily
    from luthea.lst.selection import label_days

    daily = load_daily(daily_csv)
    amedas = load_amedas_10min(amedas_csv)

    rows = []
    for s in scenes:
        d = pd.Timestamp(s["date"])
        if d not in daily.index:
            rows.append({**s, "note": "no JMA daily record"})
            continue
        rec = daily.loc[d]
        # overpass ≈ 01:30 UTC over western Japan → 10:30 JST
        overpass_utc = d.tz_localize("UTC") + pd.Timedelta(hours=1, minutes=30)
        near = amedas.index.get_indexer([overpass_utc], method="nearest")
        wind = float(amedas.iloc[near[0]]["wind_ms"]) if len(amedas) else float("nan")
        rows.append({
            **s,
            "year": d.year,
            "epoch": epoch_of(d.year),
            "t_max": float(rec.get("t_max", float("nan"))),
            "precip_mm": float(rec.get("precip_mm", float("nan"))),
            "sunshine_h": float(rec.get("sunshine_h", float("nan"))),
            "cumrain_48h": float(rec.get("cumrain_48h", float("nan"))),
            "overpass_wind": wind,
            "scene_cloud_pct": float(s.get("cloud_cover") or 0.0),
        })

    df = pd.DataFrame(rows)
    required = ("t_max", "precip_mm", "sunshine_h", "overpass_wind",
                "cumrain_48h", "scene_cloud_pct")
    if all(c in df.columns for c in required):
        df = label_days(df)
    return df


def report(df, city: str) -> dict:
    import pandas as pd
    print(f"\n{'=' * 72}\n  Scene inventory — {city}\n{'=' * 72}")
    cols = [c for c in ("date", "spacecraft", "epoch", "t_max", "sunshine_h",
                        "precip_mm", "overpass_wind", "scene_cloud_pct",
                        "is_typical", "is_extreme") if c in df.columns]
    print(df[cols].to_string(index=False))

    summary: dict = {"city": city, "n_scenes": int(len(df)), "cells": {}}
    if "is_typical" not in df.columns:
        print("\n[!] Day labels unavailable — check the JMA columns.")
        return summary

    print(f"\n{'epoch':<10} {'typical':>8} {'extreme':>8}   verdict")
    print("-" * 46)
    blocking = []
    for ep in ("t0_early", "t1_late"):
        sub = df[df["epoch"] == ep]
        n_typ = int(sub["is_typical"].sum())
        n_ext = int(sub["is_extreme"].sum())
        okay = (n_typ >= MIN_SCENES_PER_EPOCH_SCENARIO
                and n_ext >= MIN_SCENES_PER_EPOCH_SCENARIO)
        verdict = "OK" if okay else "INSUFFICIENT"
        if not okay:
            blocking.append((ep, n_typ, n_ext))
        print(f"{ep:<10} {n_typ:>8} {n_ext:>8}   {verdict}")
        summary["cells"][ep] = {"typical": n_typ, "extreme": n_ext, "ok": okay}

    mid = df[df["epoch"] == "mid"]
    print(f"{'mid':<10} {int(mid.get('is_typical', pd.Series(dtype=bool)).sum()):>8} "
          f"{int(mid.get('is_extreme', pd.Series(dtype=bool)).sum()):>8}   "
          "(robustness only)")

    print()
    if blocking:
        print("VERDICT: the α/β contrast is NOT yet supported. Options, in "
              "order of preference:")
        print("  1. widen SUMMER_MONTHS to (6, 7, 8, 9) in config.py and re-run "
              "ingest-lst --dry-run;")
        print("  2. relax CLOUD_AOI_MAX_PCT from 5 to 10;")
        print("  3. relax the typical-day T_max band (currently 30–33 °C);")
        print("  4. redefine the epochs to 4 years each (2016–2019 vs 2022–2025).")
        print("  Report the numbers above before changing any threshold.")
        summary["verdict"] = "insufficient"
    else:
        print("VERDICT: every (epoch × scenario) cell meets the minimum. "
              "Proceed to ingestion.")
        summary["verdict"] = "ok"
    return summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--city", choices=list(CITIES), default="yamaguchi")
    p.add_argument("--project", default=None, help="GEE project id")
    p.add_argument("--json", type=Path, help="write the summary as JSON")
    args = p.parse_args(argv)

    spec = CITIES[args.city]
    for key in ("aoi", "daily", "amedas"):
        if not spec[key].exists():
            print(f"error: missing {key} at {spec[key]}", file=sys.stderr)
            return 2

    scenes = landsat_dates(spec["aoi"], args.project)
    if not scenes:
        print("error: Earth Engine returned no scenes for this AOI",
              file=sys.stderr)
        return 3

    df = classify(scenes, spec["daily"], spec["amedas"])
    summary = report(df, args.city)

    if args.json:
        args.json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"\n[written] {args.json}")
    return 0 if summary.get("verdict") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
