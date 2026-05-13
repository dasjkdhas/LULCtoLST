"""Step 5 — Weather-normalised LST via OLS projection."""

from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr


METEO_FEATURES = ("t_air", "rh", "wind", "sun_48h")


def fit_beta(long_df: pd.DataFrame, features: tuple[str, ...] = METEO_FEATURES
             ) -> dict[str, float]:
    """OLS of LST on meteo features. `long_df` must contain columns
    ['lst', *features]. Returns coefficient dict (no intercept reported).
    """
    needed = {"lst", *features}
    if not needed.issubset(long_df.columns):
        raise ValueError(f"fit_beta: long_df missing {needed - set(long_df.columns)}")

    sub = long_df[list(needed)].dropna()
    X = np.column_stack([np.ones(len(sub)), sub[list(features)].to_numpy(float)])
    y = sub["lst"].to_numpy(float)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return dict(zip(features, coef[1:].tolist()))


def reference_vector(meteo_table: pd.DataFrame, typical_mask: pd.Series,
                     features: tuple[str, ...] = METEO_FEATURES) -> dict[str, float]:
    return {k: float(meteo_table.loc[typical_mask, k].mean()) for k in features}


def normalise_scene(lst: xr.DataArray, day_meteo: dict[str, float],
                    beta: dict[str, float], reference: dict[str, float],
                    features: tuple[str, ...] = METEO_FEATURES) -> xr.DataArray:
    delta = sum(beta[k] * (day_meteo[k] - reference[k]) for k in features)
    out = lst - delta
    out.attrs.update(lst.attrs)
    out.attrs["weather_normalised"] = True
    out.attrs["delta_correction_c"] = float(delta)
    return out


def normalise_table(long_df: pd.DataFrame, beta: dict[str, float],
                    reference: dict[str, float],
                    features: tuple[str, ...] = METEO_FEATURES) -> pd.Series:
    """Vectorised pixel-by-day normalisation for tabular data."""
    delta = sum(beta[k] * (long_df[k] - reference[k]) for k in features)
    return long_df["lst"] - delta
