"""Tests for the operator-facing environment checker."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT = (Path(__file__).resolve().parents[1] / "scripts" / "check_environment.py")


def _run() -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT)],
                          capture_output=True, text=True)


def test_script_runs_and_returns_a_clear_status_line():
    res = _run()
    assert "Passed:" in res.stdout
    assert "Failed:" in res.stdout
    # In a fresh sandbox without GEE / real AOI / JMA CSVs, the script
    # should exit non-zero — that is the *correct* behaviour, not a bug.
    assert res.returncode in (0, 1)


def test_check_python_lists_core_packages():
    res = _run()
    for pkg in ["numpy", "pandas", "scipy", "xarray", "matplotlib",
                "xgboost", "shap"]:
        assert pkg in res.stdout, f"checker did not mention {pkg}"


def test_check_luthea_modules_listed():
    res = _run()
    assert "luthea v" in res.stdout
    # Module count increased from 16 → 20 with the Urban Climate pivot
    # (added fdma, estat, mlit_a50, exposure). Assert on the pattern
    # rather than an exact number so future additions don't break.
    import re
    assert re.search(r"All \d+ algorithm modules importable", res.stdout)


def test_check_outputs_directories_created():
    """The checker creates missing output subdirectories on first run."""
    res = _run()
    # The script auto-creates these; their presence after one run is the
    # acceptance contract for L9.
    root = Path(__file__).resolve().parents[1]
    for sub in ("outputs/raw/jma", "outputs/lulc", "outputs/lst",
                "figures", "tables"):
        assert (root / sub).exists(), f"{sub} was not created"
    assert "Output directories" in res.stdout


def test_doc_pointer_is_present_on_failure():
    res = _run()
    if res.returncode != 0:
        assert "docs/data_acquisition.md" in res.stdout
