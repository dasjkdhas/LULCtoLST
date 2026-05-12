"""Step 5 — Weather-normalised LST.

Model:
    LST_pixel ~ T_air + RH + wind + sun_48h
fit by OLS across all pixels × all qualifying scenes, returning
β̂ shared across the AOI. Then per-pixel correction:
    LST_norm = LST_pixel - β̂ᵀ (X_day - X̄)

X̄ is the typical-day mean of the meteorological vector.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
import xarray as xr


METEO_FEATURES = ("t_air", "rh", "wind", "sun_48h")


def fit_beta(long_df: pd.DataFrame) -> dict[str, float]:
    """Fit OLS on a long DataFrame of columns
    [pixel_id, date, lst, t_air, rh, wind, sun_48h]. Return β̂ dict."""
    raise NotImplementedError


def normalise_scene(lst: xr.DataArray, day_meteo: dict[str, float],
                    beta: dict[str, float], reference: dict[str, float]) -> xr.DataArray:
    """Return LST_norm scene = lst - sum_k beta_k * (day_meteo[k] - reference[k])."""
    delta = sum(beta[k] * (day_meteo[k] - reference[k]) for k in METEO_FEATURES)
    return lst - delta


def reference_vector(meteo_table: pd.DataFrame, typical_mask: pd.Series) -> dict[str, float]:
    """Mean meteorological vector across typical-day rows."""
    return {k: float(meteo_table.loc[typical_mask, k].mean()) for k in METEO_FEATURES}
