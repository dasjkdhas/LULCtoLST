"""Tests for HIPI algorithm and the seven figure renderers.

Figure tests render to a temporary directory and check that the file is
produced with non-trivial size; deeper visual regression is out of scope.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless for CI

import numpy as np
import pandas as pd
import pytest

from luthea.attribution.hipi import (compute_hipi, hipi_summary,
                                       priority_quartiles)
from luthea.viz.figures import (fig3_lulc_and_sankey, fig4_wnsc_change,
                                  fig5_luthi_bars, fig6_shap, fig7_hipi)


def _synth_4_inputs(n: int = 400, seed: int = 0):
    rng = np.random.default_rng(seed)
    return (
        rng.normal(30, 2, n),       # WNSC °C
        rng.uniform(0, 0.6, n),     # PLAND_Green
        rng.normal(0.5, 0.3, n),    # HSI local
        rng.uniform(0, 1, n),       # walkability
    )


# ── HIPI ────────────────────────────────────────────────────────────────

def test_compute_hipi_returns_normalised_weights():
    a, b, c, d = _synth_4_inputs()
    hipi, w = compute_hipi(a, b, c, d)
    assert hipi.shape == a.shape
    assert abs(w.sum() - 1.0) < 1e-9
    assert (w >= 0).all()


def test_compute_hipi_sign_correction():
    """If we deliberately invert all inputs the PCA-loading sign must
    flip back so that 'high HIPI' still tracks priority direction."""
    a, b, c, d = _synth_4_inputs(seed=1)
    hipi_pos, w_pos = compute_hipi(a, b, c, d)
    # Flipping every input inverts the matrix; PCA loadings flip sign;
    # the sign correction restores positive weights summing to 1.
    hipi_neg, w_neg = compute_hipi(-a, -b, -c, -d)
    assert abs(w_neg.sum() - 1.0) < 1e-9
    assert (w_neg >= 0).all()


def test_compute_hipi_supplied_weights():
    a, b, c, d = _synth_4_inputs(seed=2)
    hipi, w = compute_hipi(a, b, c, d, weights=np.array([2.0, 1.0, 1.0, 0.0]))
    assert np.allclose(w, [0.5, 0.25, 0.25, 0.0])


def test_priority_quartiles_top_quartile_share():
    rng = np.random.default_rng(3)
    hipi = rng.normal(0, 1, 1000)
    q = priority_quartiles(hipi)
    # Without a built mask, all pixels are ranked: top quartile is ~25 %.
    share = (q == 3).sum() / q.size
    assert 0.20 < share < 0.30


def test_priority_quartiles_with_built_mask():
    rng = np.random.default_rng(4)
    hipi = rng.normal(0, 1, 1000)
    mask = np.zeros(1000, dtype=bool)
    mask[:200] = True
    q = priority_quartiles(hipi, mask)
    assert (q[~mask] == -1).all()
    assert (q[mask] >= 0).all()


def test_hipi_summary_columns():
    rng = np.random.default_rng(5)
    hipi = rng.normal(0, 1, 600)
    s = hipi_summary(hipi)
    for k in ["Q1", "Q2", "Q3", "Q4", "share_top_quartile"]:
        assert k in s.index


# ── Figures ─────────────────────────────────────────────────────────────

def test_fig3_lulc_and_sankey_writes_file(tmp_path: Path):
    rng = np.random.default_rng(6)
    t0 = rng.integers(0, 9, size=(40, 40))
    t1 = rng.integers(0, 9, size=(40, 40))
    trans_df = pd.DataFrame({
        "dom_start": [1, 1, 6, 6, 7],
        "dom_end":   [6, 2, 1, 6, 6],
        "n_pixels":  [120, 30, 25, 200, 60],
    })
    out = tmp_path / "fig3.png"
    fig = fig3_lulc_and_sankey(t0, t1, trans_df, out=out)
    assert out.stat().st_size > 5000
    assert fig.axes  # panels rendered


def test_fig4_wnsc_change_writes_file(tmp_path: Path):
    rng = np.random.default_rng(7)
    raw = rng.normal(1.0, 0.5, (40, 40))
    wnsc = rng.normal(0.4, 0.4, (40, 40))
    out = tmp_path / "fig4.png"
    fig4_wnsc_change(raw, wnsc, out=out)
    assert out.stat().st_size > 5000


def test_fig5_luthi_bars_writes_file(tmp_path: Path):
    df = pd.DataFrame({
        "path": ["1->6", "6->1", "7->6", "1->2"],
        "LUTHI_typ":  [1.0, -1.2, 0.8, 0.3],
        "ci_low_typ": [0.6, -1.5, 0.5, 0.0],
        "ci_high_typ":[1.4, -0.9, 1.1, 0.6],
        "LUTHI_ext":  [2.8, -0.3, 2.0, 0.4],
        "ci_low_ext": [2.4, -0.6, 1.6, 0.1],
        "ci_high_ext":[3.2, 0.0,  2.4, 0.7],
        "HSI":        [1.8, 0.9, 1.2, 0.1],
        "placebo_p":  [0.01, 0.03, 0.02, 0.5],
    })
    out = tmp_path / "fig5.png"
    fig5_luthi_bars(df, out=out, headline_paths=["1->6", "6->1"])
    assert out.stat().st_size > 5000


def test_fig6_shap_writes_file(tmp_path: Path):
    g = pd.DataFrame({"feature": ["path_a", "ndvi", "albedo", "dem"],
                      "mean_abs_shap": [1.5, 0.8, 0.5, 0.3]})
    long = pd.DataFrame([
        {"path": "1->6", "feature": "ndvi",   "mean_abs_shap": 0.5},
        {"path": "1->6", "feature": "albedo", "mean_abs_shap": 0.3},
        {"path": "1->6", "feature": "dem",    "mean_abs_shap": 0.1},
        {"path": "6->1", "feature": "ndvi",   "mean_abs_shap": 0.7},
        {"path": "6->1", "feature": "albedo", "mean_abs_shap": 0.2},
        {"path": "6->1", "feature": "dem",    "mean_abs_shap": 0.4},
    ])
    out = tmp_path / "fig6.png"
    fig6_shap(g, long, out=out)
    assert out.stat().st_size > 5000


def test_fig7_hipi_writes_file(tmp_path: Path):
    rng = np.random.default_rng(8)
    hipi = rng.normal(0, 1, (40, 40))
    quartiles = priority_quartiles(hipi)
    out = tmp_path / "fig7.png"
    fig7_hipi(hipi, quartiles, walk_lines=[
        (np.array([5, 35]), np.array([10, 30]))
    ], out=out)
    assert out.stat().st_size > 5000


# ── Sankey ──────────────────────────────────────────────────────────────

def test_plot_sankey_writes_html(tmp_path: Path):
    from luthea.viz.sankey import plot_sankey
    df = pd.DataFrame({
        "dom_start": [1, 1, 6],
        "dom_end":   [6, 2, 1],
        "n_pixels":  [120, 30, 25],
    })
    out = tmp_path / "sankey.html"
    plot_sankey(df, out)
    content = out.read_text(encoding="utf-8")
    assert "Sankey" in content or "sankey" in content
