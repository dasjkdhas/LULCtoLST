"""Command-line orchestration: ``luthea <step>``.

Each subcommand corresponds to a step in
``/root/.claude/plans/token-token-quiet-bachman.md``. Subcommands map to a
short description and the module path that implements (or will implement)
the step. Until each handler is wired, the CLI prints the binding so
operators can locate the code path without running into NotImplementedError
in surprising places.
"""

from __future__ import annotations

import argparse
import sys


COMMANDS = {
    "ingest-dw":      ("Step 2",  "luthea.data_ingest.dynamic_world.export_all"),
    "ingest-lst":     ("Step 3",  "luthea.data_ingest.landsat_st.export_scenes"),
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
    "ml-attribute":   ("Step 9",  "luthea.ml.xgb_attribution.spatial_cv_train"),
    "hipi":           ("Step 10", "luthea.viz.figures.fig8_hipi (driver TBD)"),
    "figures":        ("Step 12", "luthea.viz.figures"),
    "all":            ("Pipeline","sequential run of every step"),
}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="luthea",
        description="Land-Use Transition-based Heat Exposure Attribution pipeline.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, (step, target) in COMMANDS.items():
        sp = sub.add_parser(name, help=f"{step} — implemented by {target}")
        sp.set_defaults(_target=target, _step=step)

    args = p.parse_args(argv)
    print(f"[luthea] {args.cmd}: {args._step} → {args._target}")
    print("[luthea] handler dispatch not yet wired — call the function directly "
          "from a notebook or extend cli.py.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
