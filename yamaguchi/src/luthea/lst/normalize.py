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


# ── β̂ sensitivity variants (defence against review-objection b) ──
# All three return dict[label, β-coefficient-dict] structures so they
# can be plugged into normalise_table without changing its signature.

def fit_beta_per_class(long_df: pd.DataFrame, class_col: str = "dom_start",
                       features: tuple[str, ...] = METEO_FEATURES
                       ) -> dict[int, dict[str, float]]:
    """Stratify the OLS fit by initial dominant class. Yields one β̂_k per
    class so that LUTHI can be recomputed with class-specific
    meteorological responses. Reported in SI Table S5."""
    out: dict[int, dict[str, float]] = {}
    for cls, grp in long_df.groupby(class_col):
        if len(grp) < len(features) + 10:
            continue
        out[int(cls)] = fit_beta(grp, features=features)
    return out


def fit_beta_gwr(long_df: pd.DataFrame, bandwidth_m: float = 500.0,
                 features: tuple[str, ...] = METEO_FEATURES) -> pd.DataFrame:
    """Geographically weighted OLS β̂(p) with a Gaussian kernel of the given
    bandwidth on AOI-projected coordinates. Returns a DataFrame indexed by
    pixel_id with one column per feature.

    Implementation note: a full SVCM is left to future work; this is the
    sensitivity-test workhorse, not the headline estimator.
    """
    raise NotImplementedError(
        "fit_beta_gwr: implementation pending. Skeleton accepts long_df "
        "with columns [pixel_id, x_proj, y_proj, lst, *features] and "
        "should iterate pixels (or a stratified grid) with a Gaussian "
        "kernel weight; see mgwr or pysal-mgwr for reference."
    )


def fit_beta_quantile(long_df: pd.DataFrame, quantile_col: str = "ndvi_t0",
                      n_bins: int = 4,
                      features: tuple[str, ...] = METEO_FEATURES
                      ) -> dict[int, dict[str, float]]:
    """Stratify the OLS fit by quantile of a baseline covariate (NDVI or
    albedo). Probes whether β̂ varies with vegetation/imperviousness
    baseline. Reported in SI Table S5."""
    bins = pd.qcut(long_df[quantile_col], q=n_bins, labels=False,
                   duplicates="drop")
    out: dict[int, dict[str, float]] = {}
    for q, grp in long_df.assign(_q=bins).groupby("_q"):
        if len(grp) < len(features) + 10:
            continue
        out[int(q)] = fit_beta(grp, features=features)
    return out


def ranking_stability(luthi_by_spec: dict[str, pd.Series]) -> pd.DataFrame:
    """Compute Spearman ρ matrix between LUTHI orderings under different β̂
    specifications. Used to support H5 (all pairwise ρ ≥ 0.85)."""
    import itertools
    specs = list(luthi_by_spec)
    out = pd.DataFrame(index=specs, columns=specs, dtype=float)
    for a, b in itertools.product(specs, repeat=2):
        common = luthi_by_spec[a].index.intersection(luthi_by_spec[b].index)
        out.loc[a, b] = (luthi_by_spec[a].loc[common]
                         .corr(luthi_by_spec[b].loc[common], method="spearman"))
    return out
