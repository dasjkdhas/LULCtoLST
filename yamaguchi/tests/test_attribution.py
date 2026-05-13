"""Tests for matching, LUTHI core, bootstrap, and placebo."""

import numpy as np
import pandas as pd

from luthea.attribution.bootstrap import bootstrap_path_ci
from luthea.attribution.luthi import (from_matched_pairs, hsi, path_luthi,
                                       pixel_luthi, ssi)
from luthea.attribution.matching import (mahalanobis_knn,
                                          standardised_mean_diff,
                                          stable_reference_set)
from luthea.attribution.placebo import placebo_p_value


def test_pixel_luthi_subtraction():
    treated = np.array([1.0, 2.0, 3.0])
    matched = np.array([[0.5, 0.5], [1.0, 1.0], [0.0, 0.0]])
    out = pixel_luthi(treated, matched)
    assert np.allclose(out, [0.5, 1.0, 3.0])


def test_path_luthi_weighted_aggregation():
    luthi = pd.Series([1.0, 3.0, 5.0])
    paths = pd.Series([10, 10, 20])
    w = pd.Series([1.0, 3.0, 1.0])
    out = path_luthi(luthi, paths, w)
    assert abs(out.loc[10] - (1 * 1 + 3 * 3) / 4) < 1e-9
    assert out.loc[20] == 5.0


def test_hsi():
    typ = pd.Series([0.5, 1.0], index=["A", "B"])
    ext = pd.Series([1.5, 1.2], index=["A", "B"])
    h = hsi(typ, ext)
    assert np.allclose(h.values, [1.0, 0.2])


def test_ssi_deprecated_but_still_correct():
    """SSI was retired from the headline analysis (Q3 lock); the function
    survives for the methodological supplement and must still compute the
    centred finite difference correctly, while emitting DeprecationWarning."""
    import warnings
    by_scale = {
        100: pd.Series([1.0], index=["A"]),
        300: pd.Series([2.0], index=["A"]),
        500: pd.Series([2.5], index=["A"]),
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        s = ssi(by_scale, r_star=300)
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    assert abs(s.loc["A"] - (2.5 - 1.0) / 400) < 1e-9


def test_mahalanobis_knn_basic():
    rng = np.random.default_rng(0)
    ref = rng.normal(0, 1, size=(50, 4))
    treated = rng.normal(0, 1, size=(5, 4))
    nn = mahalanobis_knn(treated, ref, k=3)
    assert nn.shape == (5, 3)
    assert nn.min() >= 0 and nn.max() < 50


def test_stable_reference_set_groups_by_class():
    df = pd.DataFrame({
        "dom_start": [1, 1, 2, 2, 3],
        "dom_end":   [1, 2, 2, 2, 1],
        "valid":     [True, True, True, True, True],
    })
    srs = stable_reference_set(df)
    assert set(srs[1]) == {0}
    assert set(srs[2]) == {2, 3}
    assert 3 not in srs


def test_standardised_mean_diff_zero_on_identical():
    df = pd.DataFrame({"a": np.arange(10), "b": np.arange(10) * 2.0})
    smd = standardised_mean_diff(df, df.copy(), ["a", "b"])
    assert np.allclose(smd.values, 0.0)


def test_from_matched_pairs_basic():
    delta = pd.Series([2.0, 0.5, 1.0, 0.8, 1.2], index=[10, 20, 30, 40, 50])
    matched = pd.DataFrame({
        "treated_idx": [10, 10, 30, 30],
        "control_idx": [20, 40, 40, 50],
        "neighbour_rank": [0, 1, 0, 1],
    })
    out = from_matched_pairs(matched, delta)
    assert abs(out.loc[10] - (2.0 - (0.5 + 0.8) / 2)) < 1e-9
    assert abs(out.loc[30] - (1.0 - (0.8 + 1.2) / 2)) < 1e-9


def test_bootstrap_ci_brackets_point_estimate():
    rng = np.random.default_rng(0)
    n = 200
    luthi = pd.Series(rng.normal(1.0, 0.5, n))
    paths = pd.Series(np.repeat([10, 20], n // 2))
    out = bootstrap_path_ci(luthi, paths, B=200, seed=0)
    assert (out["ci_low"] < out["est"]).all()
    assert (out["est"] < out["ci_high"]).all()


def test_placebo_pvalue_runs_and_returns_path_index():
    rng = np.random.default_rng(0)
    n = 60
    stable = pd.DataFrame({
        "dom_start": [1] * n,
        "dom_end":   [1] * n,
        "ndvi": rng.normal(0.3, 0.1, n),
        "ndbi": rng.normal(0.1, 0.05, n),
    }, index=np.arange(n))
    delta = pd.Series(rng.normal(0, 0.5, n), index=stable.index)
    real = pd.Series({(1, 2): 0.05})
    out = placebo_p_value(real, stable, delta, ["ndvi", "ndbi"],
                          n_splits=50, k_neighbours=3, seed=0)
    assert (1, 2) in list(out.index)
    p = out["placebo_p"].iloc[0]
    assert 0.0 <= p <= 1.0
