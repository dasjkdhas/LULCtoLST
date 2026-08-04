"""Command-line orchestration: ``luthea <step>``.

Each subcommand corresponds to a step in
``/root/.claude/plans/token-token-quiet-bachman.md``.

Ingestion subcommands (``ingest-dw``, ``ingest-lst``) are wired to real
handlers; the remaining analytical steps print a one-line binding to
their implementation module until the orchestration is filled in.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _default_aoi() -> Path:
    """Return the active AOI path, preferring the user's real polygon
    over the placeholder example."""
    here = Path(__file__).resolve().parents[3] / "yamaguchi" / "aoi"
    real = here / "yamaguchi_center.geojson"
    example = here / "yamaguchi_center.example.geojson"
    if real.exists():
        return real
    return example


def _cmd_ingest_dw(args: argparse.Namespace) -> int:
    from .data_ingest.dynamic_world import export_all
    years = range(args.year_start, args.year_end + 1)
    print(f"[ingest-dw] AOI={args.aoi} years={list(years)} folder={args.folder} "
          f"dry_run={args.dry_run}")
    records = export_all(
        aoi_geojson_path=args.aoi,
        years=years,
        drive_folder=args.folder,
        project=args.project,
        dry_run=args.dry_run,
    )
    print(f"  {len(records)} year(s) "
          f"{'listed' if args.dry_run else 'submitted'}")
    print(json.dumps(records, indent=2))
    empty = [r["year"] for r in records if r["n_source_images"] == 0]
    if empty:
        print(f"  WARNING: no Dynamic World source images for years {empty} — "
              "check the AOI location and the summer month window.")
    return 0


def _cmd_ingest_lst(args: argparse.Namespace) -> int:
    from .data_ingest.landsat_st import export_scenes
    print(f"[ingest-lst] AOI={args.aoi} years={args.year_start}-{args.year_end} "
          f"dry_run={args.dry_run}")
    records = export_scenes(
        aoi_geojson_path=args.aoi,
        year_start=args.year_start,
        year_end=args.year_end,
        drive_folder=args.folder,
        project=args.project,
        dry_run=args.dry_run,
    )
    print(f"  {len(records)} scene(s) {'listed' if args.dry_run else 'submitted'}")
    print(json.dumps(records, indent=2))
    return 0


def _cmd_stub(label: str, target: str):
    def _runner(_args: argparse.Namespace) -> int:
        print(f"[luthea] {label}: {target}")
        print("[luthea] handler dispatch not yet wired — call the function directly "
              "from a notebook or extend cli.py.")
        return 0
    return _runner


STUBS = {
    "ingest-jma":     ("Step 4",  "luthea.data_ingest.jma.load_daily"),
    "select-days":    ("Step 4",  "luthea.lst.selection.label_days"),
    "normalise-lst":  ("Step 5",  "luthea.lst.normalize.fit_beta + normalise_scene"),
    "wnsc":           ("Step 5",  "luthea.lst.wnsc.composite_year"),
    "aggregate-lulc": ("Step 6",  "luthea.lulc.aggregate.aggregate_to_30m"),
    "transitions":    ("Step 6",  "luthea.lulc.transitions.identify_transitions"),
    "match":          ("Step 7",  "luthea.attribution.matching.match_path"),
    "luthi":          ("Step 8",  "luthea.attribution.luthi.from_matched_pairs"),
    "bootstrap":      ("Step 8",  "luthea.attribution.bootstrap.bootstrap_path_ci"),
    "placebo":        ("Step 8",  "luthea.attribution.placebo.placebo_p_value"),
    "baselines":      ("Step 8",  "luthea.attribution.baselines.assemble_comparison"),
    "ml-attribute":   ("Step 9",  "luthea.ml.xgb_attribution.spatial_cv_train"),
    "hipi":           ("Step 10", "luthea.viz.figures.fig8_hipi (driver TBD)"),
    "figures":        ("Step 12", "luthea.viz.figures"),
    "all":            ("Pipeline", "sequential run of every step"),
}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="luthea",
        description="Land-Use Transition-based Heat Exposure Attribution pipeline.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # ── ingest-dw ────────────────────────────────────────────────────
    sp = sub.add_parser("ingest-dw",
                        help="Step 2 — pull Dynamic World yearly LULC composites")
    sp.add_argument("--aoi", type=Path, default=_default_aoi())
    sp.add_argument("--year-start", type=int, default=2016)
    sp.add_argument("--year-end", type=int, default=2025)
    sp.add_argument("--folder", default="luthea_dw")
    sp.add_argument("--project", default=None,
                    help="GEE project id (overrides EE_PROJECT env var)")
    sp.add_argument("--dry-run", action="store_true",
                    help="report per-year source-image counts without "
                         "submitting any Drive export task")
    sp.set_defaults(func=_cmd_ingest_dw)

    # ── ingest-lst ───────────────────────────────────────────────────
    sp = sub.add_parser("ingest-lst",
                        help="Step 3 — pull Landsat 8/9 C2 L2 ST scenes")
    sp.add_argument("--aoi", type=Path, default=_default_aoi())
    sp.add_argument("--year-start", type=int, default=2016)
    sp.add_argument("--year-end", type=int, default=2025)
    sp.add_argument("--folder", default="luthea_lst")
    sp.add_argument("--project", default=None)
    sp.add_argument("--dry-run", action="store_true",
                    help="list matching scenes without submitting exports")
    sp.set_defaults(func=_cmd_ingest_lst)

    # ── remaining steps (stubs) ──────────────────────────────────────
    for name, (step, target) in STUBS.items():
        sp = sub.add_parser(name, help=f"{step} — implemented by {target}")
        sp.set_defaults(func=_cmd_stub(f"{name}: {step}", target))

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
