"""Tests for baseline-estimator and β̂-sensitivity helpers added under
the Socratic Q2 defence package (manuscript §§ 3.9, 4.4, 4.8)."""

import numpy as np
import pandas as pd

from luthea.attribution.baselines import (assemble_comparison, naive_state_contrast,
                                           standard_did)
from luthea.lst.normalize import (METEO_FEATURES, fit_beta_per_class,
                                  fit_beta_quantile, ranking_stability)


def test_naive_state_contrast_aggregates_by_end_class():
    end = pd.Series([1, 1, 2, 2])
    t0 = pd.Series([10.0, 12.0, 20.0, 22.0])
    t1 = pd.Series([12.0, 13.0, 24.0, 25.0])
    out = naive_state_contrast(end, t0, t1)
    assert abs(out.loc[1] - 1.5) < 1e-9
    assert abs(out.loc[2] - 3.5) < 1e-9


def test_standard_did_subtracts_stable_reference():
    ks = pd.Series([1, 1, 1, 1])
    ke = pd.Series([1, 2, 2, 1])
    t0 = pd.Series([10.0, 10.0, 11.0, 9.0])
    t1 = pd.Series([11.0, 13.0, 14.0, 10.5])
    out = standard_did(ks, ke, t0, t1)
    # stable (k=1,k=1) delta mean = (1.0 + 1.5)/2 = 1.25
    # transition (1,2) delta mean = (3.0 + 3.0)/2 = 3.0
    # DiD = 3.0 - 1.25 = 1.75
    assert abs(out.iloc[0] - 1.75) < 1e-9
    assert out.index[0] == (1, 2)


def test_assemble_comparison_layout():
    luthi = pd.Series({(1, 2): 0.8, (1, 3): 0.5})
    did = pd.Series({(1, 2): 1.2, (1, 3): 0.7})
    mo = pd.Series({(1, 2): 0.9, (1, 3): 0.6})
    naive = pd.Series({2: 1.5, 3: 1.0})
    out = assemble_comparison(luthi, naive, did, mo)
    assert list(out.columns) == ["naive_state_contrast", "standard_did",
                                  "matching_only", "LUTHI"]
    row_12 = out[out.index.map(lambda t: t == (1, 2))].iloc[0]
    assert abs(row_12["naive_state_contrast"] - 1.5) < 1e-9


def test_fit_beta_per_class_returns_class_keyed_dict():
    rng = np.random.default_rng(0)
    n = 2000
    df = pd.DataFrame({
        "dom_start": rng.integers(0, 3, n),
        "t_air": rng.normal(28, 3, n),
        "rh": rng.normal(60, 10, n),
        "wind": rng.normal(2, 1, n),
        "sun_48h": rng.normal(16, 4, n),
    })
    df["lst"] = 0.8 * df["t_air"] + rng.normal(0, 0.5, n)
    out = fit_beta_per_class(df)
    assert set(out.keys()).issubset({0, 1, 2})
    for beta in out.values():
        assert "t_air" in beta and beta["t_air"] > 0.5


def test_fit_beta_quantile_strata():
    rng = np.random.default_rng(0)
    n = 2000
    df = pd.DataFrame({
        "ndvi_t0": rng.uniform(0, 0.8, n),
        "t_air": rng.normal(28, 3, n),
        "rh": rng.normal(60, 10, n),
        "wind": rng.normal(2, 1, n),
        "sun_48h": rng.normal(16, 4, n),
    })
    df["lst"] = 0.8 * df["t_air"] + rng.normal(0, 0.5, n)
    out = fit_beta_quantile(df, n_bins=4)
    assert len(out) == 4
    for beta in out.values():
        assert "t_air" in beta


def test_ranking_stability_identity_and_inverse():
    a = pd.Series([1.0, 2.0, 3.0, 4.0], index=list("PQRS"))
    b = pd.Series([1.1, 1.9, 3.1, 3.9], index=list("PQRS"))
    c = pd.Series([4.0, 3.0, 2.0, 1.0], index=list("PQRS"))
    rho = ranking_stability({"glob": a, "perclass": b, "gwr": c})
    assert abs(rho.loc["glob", "glob"] - 1.0) < 1e-9
    assert rho.loc["glob", "perclass"] > 0.95
    assert rho.loc["glob", "gwr"] < -0.95
