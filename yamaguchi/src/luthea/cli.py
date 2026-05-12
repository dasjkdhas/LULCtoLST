"""Command-line orchestration: `luthea run --aoi yamaguchi --years 2016-2025`.

Subcommands map 1:1 to Step numbers in the plan file.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="luthea")
    sub = p.add_subparsers(dest="cmd", required=True)

    for step in (
        "ingest-dw",       # Step 2
        "ingest-lst",      # Step 3
        "ingest-jma",      # Step 4
        "select-days",     # Step 4
        "normalise-lst",   # Step 5
        "wnsc",            # Step 5
        "aggregate-lulc",  # Step 6
        "transitions",     # Step 6
        "match",           # Step 7
        "luthi",           # Step 8
        "bootstrap",       # Step 8
        "placebo",         # Step 8
        "ml-attribute",    # Step 9
        "hipi",            # Step 10
        "figures",         # Step 12
        "all",             # full pipeline
    ):
        sub.add_parser(step)

    args = p.parse_args(argv)
    print(f"[luthea] subcommand '{args.cmd}' not yet wired — see plan Step.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
