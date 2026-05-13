"""Step 8 — LUTHI estimator family."""

from __future__ import annotations

import numpy as np
import pandas as pd


def pixel_luthi(delta_lst_treated: np.ndarray,
                delta_lst_matched: np.ndarray) -> np.ndarray:
    """delta_lst_matched is (n_pixels, k); its row mean is the counterfactual."""
    if delta_lst_matched.ndim != 2:
        raise ValueError("delta_lst_matched must be 2-D (n_pixels, k_neighbours)")
    counterfactual = np.nanmean(delta_lst_matched, axis=1)
    return delta_lst_treated - counterfactual


def from_matched_pairs(matched: pd.DataFrame, delta_lst: pd.Series
                       ) -> pd.Series:
    """Compute pixel-level LUTHI directly from a long matched-pairs DataFrame.

    `matched` columns: treated_idx, control_idx, neighbour_rank
    `delta_lst` is a Series indexed by pixel id giving Δ(WNSC_end − WNSC_start).
    """
    counterfactual = (matched.assign(d=lambda d: delta_lst.reindex(d["control_idx"]).to_numpy())
                             .groupby("treated_idx")["d"].mean())
    treated_delta = delta_lst.reindex(counterfactual.index)
    return treated_delta - counterfactual


def path_luthi(pixel_index: pd.Series, path_code: pd.Series,
               weights: pd.Series | None = None) -> pd.Series:
    """Aggregate pixel LUTHI to path codes with optional area weights."""
    if weights is None:
        weights = pd.Series(1.0, index=pixel_index.index)
    df = pd.DataFrame({"luthi": pixel_index, "path": path_code, "w": weights}).dropna()
    grouped = df.groupby("path")
    num = grouped.apply(lambda g: float(np.average(g["luthi"], weights=g["w"])))
    return num.rename("LUTHI")


def hsi(luthi_typ: pd.Series, luthi_ext: pd.Series) -> pd.Series:
    """HSI^{k→j} = LUTHI_ext − LUTHI_typ; positive ⇒ extreme days amplify effect."""
    return (luthi_ext - luthi_typ).rename("HSI")


def ssi(luthi_by_scale: dict[int, pd.Series], r_star: int) -> pd.Series:
    """Centred finite difference dLUTHI/dr at r*.

    `luthi_by_scale` keys must include neighbours of r_star in the sorted scale
    list; e.g. for r_star=300 with scales (100, 300, 500) the derivative is
    (LUTHI(500) − LUTHI(100)) / (500 − 100).
    """
    scales = sorted(luthi_by_scale.keys())
    if r_star not in scales:
        raise ValueError(f"ssi: r_star={r_star} not in scales {scales}")
    i = scales.index(r_star)
    if i == 0 or i == len(scales) - 1:
        raise ValueError("ssi: r_star must have neighbours on both sides")
    r_lo, r_hi = scales[i - 1], scales[i + 1]
    return ((luthi_by_scale[r_hi] - luthi_by_scale[r_lo]) / (r_hi - r_lo)).rename("SSI")
