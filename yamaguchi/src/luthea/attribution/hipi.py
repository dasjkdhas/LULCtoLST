"""Step 10 — Heat Improvement Priority Index (HIPI).

Manuscript reference: § 3.7 / § 6.6, Eq. 12.

HIPI ranks 30 m cells by their marginal mitigation potential, combining
four standardised inputs:

    HIPI_p = w1 · z(WNSC_typ_p)
           + w2 · z(-PLAND_Green_300m_p)
           + w3 · z(HSI_local_p)
           + w4 · z(walkability_p)

Default weights come from the loadings of the first principal component
of the four standardised inputs; arbitrary weights may be supplied for
sensitivity analysis. A sign correction guarantees that high HIPI
corresponds to "high mitigation priority" regardless of which side PCA
chose for PC1.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


HIPI_INPUT_NAMES = ("WNSC_typ", "neg_PLAND_Green", "HSI_local", "walkability")


def _zscore(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    sigma = np.nanstd(x, ddof=1)
    if sigma == 0:
        return np.zeros_like(x)
    return (x - np.nanmean(x)) / sigma


def compute_hipi(wnsc_typ: np.ndarray, pland_green_300m: np.ndarray,
                 hsi_local: np.ndarray, walkability: np.ndarray,
                 weights: np.ndarray | None = None,
                 use_pca: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Compute HIPI per pixel.

    Parameters
    ----------
    wnsc_typ : array
        Weather-normalised summer LST at t1 under the typical scenario.
    pland_green_300m : array
        Neighbourhood green-space share at 300 m radius (will be negated).
    hsi_local : array
        Local heat-stress sensitivity (HSI) attached to each pixel.
    walkability : array
        Pedestrian density / walk-axis exposure proxy.
    weights : array of length 4, optional
        If supplied, used directly (after L1 normalisation). Overrides PCA.
    use_pca : bool
        If True and `weights is None`, derive weights from PC1 loadings of
        the standardised input matrix. Sign-corrected so that HIPI grows
        with priority.

    Returns
    -------
    hipi : array, shape = wnsc_typ.shape
    weights_used : array of length 4
        L1-normalised weights actually applied (positive values).
    """
    z_wnsc = _zscore(wnsc_typ)
    z_neg_green = _zscore(-np.asarray(pland_green_300m, dtype=float))
    z_hsi = _zscore(hsi_local)
    z_walk = _zscore(walkability)

    inputs = np.column_stack([z_wnsc, z_neg_green, z_hsi, z_walk])

    if weights is not None:
        w = np.asarray(weights, dtype=float)
    elif use_pca:
        w = _pca_first_loading(inputs)
    else:
        w = np.array([0.25, 0.25, 0.25, 0.25])

    # Sign correction: each input is constructed so that "higher = more
    # priority". If the loading vector is overall negative, flip it.
    if w.sum() < 0:
        w = -w

    # L1-normalise so weights are positive and sum to 1
    w_abs = np.abs(w)
    if w_abs.sum() == 0:
        w_norm = np.full(4, 0.25)
    else:
        w_norm = w_abs / w_abs.sum()

    hipi = inputs @ w_norm
    return hipi.reshape(np.asarray(wnsc_typ).shape), w_norm


def _pca_first_loading(matrix: np.ndarray) -> np.ndarray:
    """First-PC loading vector via NumPy SVD (no sklearn dependency)."""
    X = np.asarray(matrix, dtype=float)
    X = X - np.nanmean(X, axis=0)
    X = np.where(np.isnan(X), 0.0, X)
    _, _, vt = np.linalg.svd(X, full_matrices=False)
    return vt[0]


def priority_quartiles(hipi: np.ndarray, mask_built: np.ndarray | None = None
                       ) -> np.ndarray:
    """Return integer 0..3 labels (3 = top quartile = highest priority).

    `mask_built` restricts the ranking to currently-built pixels per the
    manuscript's definition; non-built pixels receive -1.
    """
    arr = np.asarray(hipi, dtype=float)
    out = np.full(arr.shape, -1, dtype=np.int8)
    if mask_built is None:
        idx = np.ones(arr.shape, dtype=bool)
    else:
        idx = np.asarray(mask_built, dtype=bool)
    flat = arr[idx]
    if flat.size == 0:
        return out
    q = np.nanquantile(flat, [0.25, 0.50, 0.75])
    labels = np.digitize(flat, q)  # 0..3
    out[idx] = labels.astype(np.int8)
    return out


def hipi_summary(hipi: np.ndarray, mask_built: np.ndarray | None = None
                 ) -> pd.Series:
    """Compact diagnostic: count per quartile + share of AOI flagged top."""
    quartiles = priority_quartiles(hipi, mask_built)
    counts = pd.Series(quartiles[quartiles >= 0]).value_counts().sort_index()
    counts.index = [f"Q{int(i) + 1}" for i in counts.index]
    total = counts.sum()
    counts["share_top_quartile"] = float(counts.get("Q4", 0)) / total if total else np.nan
    return counts
