"""Tests for OLS-based LST normalisation."""

import numpy as np
import pandas as pd

from luthea.lst.normalize import (METEO_FEATURES, fit_beta, normalise_table,
                                  reference_vector)


def test_fit_beta_recovers_linear_signal():
    rng = np.random.default_rng(0)
    n = 4000
    df = pd.DataFrame({
        "t_air": rng.normal(28, 3, n),
        "rh": rng.normal(60, 10, n),
        "wind": rng.normal(2, 1, n),
        "sun_48h": rng.normal(16, 4, n),
    })
    true_beta = dict(t_air=0.8, rh=-0.05, wind=-0.6, sun_48h=0.15)
    df["lst"] = (df[list(METEO_FEATURES)] * pd.Series(true_beta)).sum(axis=1) \
                + 10 + rng.normal(0, 0.5, n)
    beta_hat = fit_beta(df)
    for k, v in true_beta.items():
        assert abs(beta_hat[k] - v) < 0.05, f"{k}: {beta_hat[k]} vs {v}"


def test_normalise_table_zero_at_reference_means():
    df = pd.DataFrame({
        "lst": [25.0, 27.0],
        "t_air": [28.0, 30.0],
        "rh": [60.0, 60.0],
        "wind": [2.0, 2.0],
        "sun_48h": [16.0, 16.0],
    })
    beta = dict(t_air=1.0, rh=0.0, wind=0.0, sun_48h=0.0)
    ref = dict(t_air=28.0, rh=60.0, wind=2.0, sun_48h=16.0)
    out = normalise_table(df, beta, ref)
    assert abs(out.iloc[0] - 25.0) < 1e-9
    assert abs(out.iloc[1] - 25.0) < 1e-9


def test_reference_vector_uses_typical_mask():
    df = pd.DataFrame({"t_air": [25, 30, 35], "rh": [60, 70, 80],
                       "wind": [1, 2, 3], "sun_48h": [10, 15, 20]})
    mask = pd.Series([True, True, False])
    ref = reference_vector(df, mask)
    assert ref["t_air"] == 27.5
