"""Integration test: run the end-to-end synthetic-data quickstart.

Slower than unit tests (~10 s) but exercises every module together,
catching cross-module interface regressions that unit tests miss.
Skipped if xgboost or shap is unavailable.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("xgboost")
pytest.importorskip("shap")

SCRIPT = Path(__file__).resolve().parents[1] / "notebooks" / "00_end_to_end_synthetic.py"


@pytest.mark.integration
def test_end_to_end_synthetic_runs_cleanly():
    res = subprocess.run([sys.executable, str(SCRIPT)],
                         capture_output=True, text=True, timeout=120)
    assert res.returncode == 0, (
        f"synthetic pipeline failed (exit {res.returncode})\n"
        f"--- stdout ---\n{res.stdout[-3000:]}\n--- stderr ---\n{res.stderr[-3000:]}"
    )
    out = res.stdout
    # Stage markers — every major step must have produced output.
    for marker in (
        "[Stage 1] LULC fields generated",
        "[Stage 2]",
        "[Stage 3]",
        "[Stage 5] β̂ recovered",
        "[Stage 6] Stable reference set sizes",
        "[Stage 7] Path-level LUTHI / HSI",
        "[Stage 7] Bootstrap 95% CI",
        "[Stage 7] Placebo p-values",
        "[Stage 8] Baseline comparison",
        "[Stage 9] Spatial CV",
        "[Stage 9] Global SHAP top features",
        "[Stage 10] Partial R²",
        "[done]",
    ):
        assert marker in out, f"missing stage marker in stdout: {marker!r}"


@pytest.mark.integration
def test_alpha_beta_asymmetry_recovered_in_synthetic_data():
    """Read the printed LUTHI table from stdout and verify the Q4 central
    claim is recovered: HSI(Green→Built) > +1.0 °C (α amplification) and
    HSI(Built→Green) > +0.5 °C (β cooling collapse, positive sign because
    cooling magnitude shrinks)."""
    import re

    res = subprocess.run([sys.executable, str(SCRIPT)],
                         capture_output=True, text=True, timeout=120)
    assert res.returncode == 0
    out = res.stdout

    # Pull the HSI column for paths (1,6) Trees→Built and (6,1) Built→Trees.
    # The line format is e.g.:   "(1, 6)      10.40      12.21  1.81"
    def hsi_for(path: str) -> float:
        # Match the path token followed by 3 floating-point numbers.
        m = re.search(
            rf"\(\s*{path[0]}\s*,\s*{path[1]}\s*\)\s+"
            r"-?\d+\.\d+\s+-?\d+\.\d+\s+(-?\d+\.\d+)",
            out,
        )
        assert m, f"could not parse HSI line for path {path}"
        return float(m.group(1))

    hsi_green_built = hsi_for("16")
    hsi_built_green = hsi_for("61")
    assert hsi_green_built > 1.0, f"α not recovered: HSI(Green→Built)={hsi_green_built}"
    assert hsi_built_green > 0.5, f"β not recovered: HSI(Built→Green)={hsi_built_green}"
