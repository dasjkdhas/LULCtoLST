"""Step 8 — LUTHI estimator family.

Pixel-level:
    LUTHI_p = (LST~_p,t1 - LST~_p,t0) - mean_{q ∈ M(p)} (LST~_q,t1 - LST~_q,t0)

Path-level:
    LUTHI^{k→j} = Σ w_p · LUTHI_p / Σ w_p,     weights w_p = effective area share.

Scenario-stratified: typical / extreme; multi-scale: r ∈ {100, 300, 500} m.

Derived indices:
    HSI^{k→j} = LUTHI_ext - LUTHI_typ
    SSI^{k→j} = ΔLUTHI(r)/Δr at r*
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def pixel_luthi(delta_lst_treated: np.ndarray, delta_lst_matched: np.ndarray,
               ) -> np.ndarray:
    """delta_lst_matched: (n_pixels, k) → row mean is the counterfactual."""
    return delta_lst_treated - delta_lst_matched.mean(axis=1)


def path_luthi(pixel_luthi: pd.Series, path_code: pd.Series,
              weights: pd.Series) -> pd.Series:
    """Area-weighted aggregation per path code."""
    df = pd.DataFrame({"luthi": pixel_luthi, "path": path_code, "w": weights})
    num = df.groupby("path").apply(lambda g: (g["luthi"] * g["w"]).sum())
    den = df.groupby("path")["w"].sum()
    return num / den


def hsi(luthi_typ: pd.Series, luthi_ext: pd.Series) -> pd.Series:
    return luthi_ext - luthi_typ


def ssi(luthi_by_scale: dict[int, pd.Series], r_star: int = 300) -> pd.Series:
    """Centred finite difference dLUTHI/dr at r*."""
    raise NotImplementedError
