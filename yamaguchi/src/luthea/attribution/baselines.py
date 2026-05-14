"""Baseline attribution estimators for SI Table S4 (defence against
review-objection a: "LUTHI is dressed-up DiD").

Three baselines are run on the **same pixels** that feed LUTHI, and the
SI table shows that the central α/β asymmetry is invisible to all of
them — quantitatively demonstrating LUTHEA's value-add.

Baselines:
  1. `naive_state_contrast` — mean LST per end-state class, two-period
     difference. No matching, no meteorology, no transition concept.
  2. `standard_did` — pixel-level difference-in-differences with no
     matching. Treatment indicator = transitioned (1) vs stable (0)
     within each class; ΔLST_treated - ΔLST_stable per class.
  3. `matching_only` — same Mahalanobis kNN matching as LUTHEA but
     **without** the weather-normalisation step (Eq. 4–5 in the
     manuscript). Acts as the meteorology-control isolation test.

Each returns a Series indexed by transition path with the estimator's
value, allowing the SI table to align columns side-by-side with LUTHI.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .matching import mahalanobis_knn, stable_reference_set


def naive_state_contrast(end_class: pd.Series, lst_t0: pd.Series,
                         lst_t1: pd.Series) -> pd.Series:
    """ΔLST mean per end-state class — the simplest possible baseline."""
    delta = lst_t1 - lst_t0
    out = delta.groupby(end_class).mean()
    out.name = "naive_state_contrast"
    return out


def standard_did(dom_start: pd.Series, dom_end: pd.Series,
                 lst_t0: pd.Series, lst_t1: pd.Series,
                 valid: pd.Series | None = None) -> pd.Series:
    """Per-path DiD with no matching: ΔLST_treated - ΔLST_stable (within
    class k, pooled). Treatment = (k != j); control = (k == j) within
    the same starting class."""
    df = pd.DataFrame({
        "dom_start": dom_start.to_numpy(),
        "dom_end": dom_end.to_numpy(),
        "delta": (lst_t1 - lst_t0).to_numpy(),
    })
    if valid is not None:
        df = df[valid.to_numpy().astype(bool)]

    stable = df[df["dom_start"] == df["dom_end"]]
    stable_mean = stable.groupby("dom_start")["delta"].mean()

    rows = []
    for (ks, ke), g in df.groupby(["dom_start", "dom_end"]):
        if int(ks) == int(ke):
            continue
        if int(ks) not in stable_mean.index:
            continue
        rows.append({
            "path": (int(ks), int(ke)),
            "standard_did": float(g["delta"].mean() - stable_mean.loc[int(ks)]),
        })
    return pd.DataFrame(rows).set_index("path")["standard_did"]


def matching_only(covariates: pd.DataFrame, transitions: pd.DataFrame,
                  cov_cols: list[str], lst_t0: pd.Series, lst_t1: pd.Series,
                  k_neighbours: int = 5) -> pd.Series:
    """Same matching design as LUTHEA but skip the weather-normalisation
    step. Highlights how much of LUTHI's signal is meteorology-driven
    de-noising versus pure spatial matching."""
    delta = lst_t1 - lst_t0
    transitions = transitions[transitions["valid"]].copy()
    srs = stable_reference_set(transitions)
    out = {}
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
        treated_X, ref_X = treated_X[keep_t], ref_X[keep_r]
        treated_idx = treated_idx[keep_t]
        pool_idx_kept = pool_idx[keep_r]

        nn = mahalanobis_knn(treated_X, ref_X, k=k_neighbours)
        cf = delta.reindex(pool_idx_kept).to_numpy()[nn].mean(axis=1)
        treated_delta = delta.reindex(treated_idx).to_numpy()
        out[(int(ks), int(ke))] = float(np.nanmean(treated_delta - cf))

    if not out:
        return pd.Series([], name="matching_only", dtype=float)
    idx = pd.Index(list(out.keys()), name="path", tupleize_cols=False)
    return pd.Series(list(out.values()), index=idx, name="matching_only")


def assemble_comparison(luthi: pd.Series, naive: pd.Series,
                        did: pd.Series, mo: pd.Series) -> pd.DataFrame:
    """Stack the four estimators into the SI Table S4 layout.

    `luthi` is the headline LUTHI per path (typical scenario).
    `naive` is keyed by end-state class; we broadcast by `end_class`.
    `did`, `mo` are keyed by transition path tuple.
    """
    df = pd.DataFrame({"LUTHI": luthi, "standard_did": did, "matching_only": mo})
    end = pd.Series([k[1] for k in df.index], index=df.index, name="end")
    df["naive_state_contrast"] = naive.reindex(end).to_numpy()
    return df[["naive_state_contrast", "standard_did", "matching_only", "LUTHI"]]
