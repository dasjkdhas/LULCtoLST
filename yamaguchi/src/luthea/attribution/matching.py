"""Step 7 — Stable Reference Set + Mahalanobis kNN matching.

For each transition pixel of class k → j, find the `k_neighbours` nearest
stable pixels (LULC_start == LULC_end == k) by Mahalanobis distance over
baseline covariates. Returns indices and per-covariate Standardised Mean
Difference diagnostics.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist


def stable_reference_set(transitions: pd.DataFrame) -> dict[int, np.ndarray]:
    """`transitions` must contain columns dom_start, dom_end, valid (bool).
    Returns {class_code: row_index_array} for class_code where start==end.
    """
    stable = transitions[(transitions["dom_start"] == transitions["dom_end"])
                         & transitions["valid"]]
    return {int(k): np.asarray(grp.index)
            for k, grp in stable.groupby("dom_start")}


def _inv_cov(X: np.ndarray) -> np.ndarray:
    cov = np.cov(X.T)
    if np.ndim(cov) == 0:
        cov = np.array([[float(cov)]])
    return np.linalg.pinv(cov + 1e-9 * np.eye(cov.shape[0]))


def mahalanobis_knn(transition_X: np.ndarray, reference_X: np.ndarray,
                    k: int = 5) -> np.ndarray:
    """Return (n_transition, k) integer array of reference-row indices."""
    pooled = np.vstack([transition_X, reference_X])
    VI = _inv_cov(pooled)
    d = cdist(transition_X, reference_X, metric="mahalanobis", VI=VI)
    k = min(k, reference_X.shape[0])
    return np.argpartition(d, kth=k - 1, axis=1)[:, :k]


def standardised_mean_diff(treated: pd.DataFrame, controls: pd.DataFrame,
                           covariates: list[str]) -> pd.Series:
    smd = {}
    for c in covariates:
        t, u = treated[c].to_numpy(float), controls[c].to_numpy(float)
        pooled_sd = np.sqrt(0.5 * (np.nanvar(t, ddof=1) + np.nanvar(u, ddof=1)))
        smd[c] = (np.nanmean(t) - np.nanmean(u)) / pooled_sd if pooled_sd else np.nan
    return pd.Series(smd, name="SMD")


def match_path(covariates: pd.DataFrame, transitions: pd.DataFrame,
               cov_cols: list[str], k_neighbours: int = 5
               ) -> dict[tuple[int, int], pd.DataFrame]:
    """Per-path matching driver. Returns {(k, j): matched_pairs_long_df}.

    matched_pairs_long_df columns:
        treated_idx, control_idx, neighbour_rank, distance_rank
    """
    transitions = transitions[transitions["valid"]].copy()
    srs = stable_reference_set(transitions)
    results: dict[tuple[int, int], pd.DataFrame] = {}

    for (ks, ke), grp in transitions.groupby(["dom_start", "dom_end"]):
        if int(ks) == int(ke):
            continue
        pool_idx = srs.get(int(ks))
        if pool_idx is None or len(pool_idx) < k_neighbours:
            continue
        treated_idx = grp.index.to_numpy()

        treated_X = covariates.loc[treated_idx, cov_cols].to_numpy(float)
        ref_X = covariates.loc[pool_idx, cov_cols].to_numpy(float)
        keep_t = ~np.isnan(treated_X).any(axis=1)
        keep_r = ~np.isnan(ref_X).any(axis=1)
        if keep_t.sum() == 0 or keep_r.sum() < k_neighbours:
            continue
        treated_X = treated_X[keep_t]
        ref_X = ref_X[keep_r]
        treated_idx = treated_idx[keep_t]
        pool_idx_kept = pool_idx[keep_r]

        nn = mahalanobis_knn(treated_X, ref_X, k=k_neighbours)
        rows = []
        for ti, neigh in zip(treated_idx, nn):
            for rank, n_local in enumerate(neigh):
                rows.append((ti, int(pool_idx_kept[n_local]), rank))
        results[(int(ks), int(ke))] = pd.DataFrame(
            rows, columns=["treated_idx", "control_idx", "neighbour_rank"])
    return results
