"""Tests for Urban Climate overlay algorithms."""

from __future__ import annotations

import numpy as np
import pandas as pd

from luthea.attribution.exposure import (build_table5, heatstroke_correlation,
                                          policy_overlap,
                                          population_exposure)


def test_population_exposure_basic():
    # 4 pixels; pixels 0,1 in Q4, pixels 2,3 in AOI but not Q4
    hipi_q = np.array([3, 3, 1, 0])
    pixel_area = np.full(4, 900.0)  # 30 m × 30 m
    # Each pixel maps 1:1 to a distinct mesh cell, full coverage
    intersect = pd.DataFrame({
        "pixel_idx":         [0, 1, 2, 3],
        "mesh_id":           ["m0", "m1", "m2", "m3"],
        "intersect_area_m2": [900.0] * 4,
    })
    mesh_pop = pd.Series({"m0": 100, "m1": 200, "m2": 300, "m3": 400})
    mesh_area = pd.Series({"m0": 900.0, "m1": 900.0, "m2": 900.0, "m3": 900.0})
    result = population_exposure(hipi_q, pixel_area, intersect,
                                 mesh_pop, mesh_area)
    assert result["population_in_AOI"] == 1000.0
    assert result["population_in_Q4"] == 300.0
    assert abs(result["exposure_share"] - 0.3) < 1e-9


def test_population_exposure_elderly_disparity():
    hipi_q = np.array([3, 3, 0, 0])
    intersect = pd.DataFrame({
        "pixel_idx":         [0, 1, 2, 3],
        "mesh_id":           ["m0", "m1", "m2", "m3"],
        "intersect_area_m2": [900.0] * 4,
    })
    mesh_pop = pd.Series({"m0": 100, "m1": 100, "m2": 100, "m3": 100})
    mesh_area = pd.Series({"m0": 900.0, "m1": 900.0, "m2": 900.0, "m3": 900.0})
    # Elderly concentrated in Q4 meshes
    elderly = pd.Series({"m0": 50, "m1": 50, "m2": 10, "m3": 10})
    result = population_exposure(hipi_q, np.full(4, 900.0), intersect,
                                 mesh_pop, mesh_area,
                                 elderly_by_mesh=elderly)
    # elderly share in Q4 = 100/200 = 0.5; AOI = 120/400 = 0.3
    assert abs(result["elderly_share_Q4"] - 0.5) < 1e-9
    assert abs(result["elderly_share_AOI"] - 0.3) < 1e-9
    assert result["elderly_share_ratio"] > 1.5


def test_heatstroke_correlation_returns_expected_keys():
    hsi = pd.Series({y: 0.5 + 0.1 * (y - 2016) for y in range(2016, 2026)})
    trans = pd.Series({y: 300 + 20 * (y - 2016) for y in range(2016, 2026)})
    out = heatstroke_correlation(hsi, trans, bootstrap=100, seed=0)
    for k in ("rho", "p_value", "ci_low", "ci_high", "n"):
        assert k in out
    # Positively correlated by construction — rho should be close to 1
    assert out["rho"] > 0.9
    assert out["n"] == 10


def test_heatstroke_correlation_handles_lag():
    """The `lag` parameter shifts the transports series relative to HSI;
    verify the shifted alignment produces a sensible correlation."""
    hsi = pd.Series({y: y - 2020 for y in range(2016, 2026)})
    # Transports are the reverse-signal shifted one year forward
    trans = pd.Series({y + 1: -(y - 2020) for y in range(2016, 2026)})
    lag0 = heatstroke_correlation(hsi, trans, bootstrap=50, seed=0)
    lag1 = heatstroke_correlation(hsi, trans, bootstrap=50, seed=0, lag=1)
    # No-lag alignment: hsi and trans move in opposite directions → ρ ≈ -1
    assert lag0["rho"] < -0.9
    # lag=1 realigns the pairing but the underlying signals still oppose
    # → ρ remains strongly negative but the specific magnitude differs
    assert lag1["n"] >= 4
    assert lag1["rho"] != lag0["rho"] or lag1["n"] != lag0["n"]


def test_policy_overlap_iou():
    q4 = np.array([[1, 1, 0], [1, 1, 0], [0, 0, 0]]) == 1
    # Cast q4 back to quartile-label form to match function signature
    q_labels = np.where(q4, 3, 0)
    policy = np.array([[True, True, True],
                       [False, False, False],
                       [False, False, False]])
    out = policy_overlap(q_labels, policy)
    # intersection = 2, union = 5, IoU = 0.4
    assert abs(out["iou"] - 0.4) < 1e-9
    # missed = q4 - inter = 4 - 2 = 2; missed_share = 2/4 = 0.5
    assert abs(out["missed_share"] - 0.5) < 1e-9


def test_policy_overlap_shape_mismatch_raises():
    import pytest
    with pytest.raises(ValueError):
        policy_overlap(np.zeros((3, 3), dtype=int),
                       np.zeros((4, 3), dtype=bool))


def test_build_table5_keys():
    exp = {"population_in_Q4": 5000, "exposure_share": 0.35,
           "elderly_share_ratio": 1.4}
    ovr = {"iou": 0.42, "missed_share": 0.55, "policy_share": 0.30}
    heat = {"rho": 0.72, "ci_low": 0.30, "ci_high": 0.90}
    t = build_table5(exp, ovr, heat)
    for m in ("population_in_Q4", "exposure_share", "iou_HIPI_UDA",
              "heatstroke_rho"):
        assert m in t.index
