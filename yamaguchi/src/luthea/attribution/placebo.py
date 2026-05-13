"""Placebo test: within-class pseudo-transitions should yield LUTHI ≈ 0.

For each stable class k:
  1. Randomly split its pixel pool into a 'treated half' and a 'reference half'.
  2. Run the same matching + LUTHI computation on these in-class halves.
  3. Repeat over many splits to build a null distribution of |LUTHI_placebo|.
  4. p-value per real path (k → j) = fraction of placebo replicates whose
     |LUTHI| equals or exceeds the observed |LUTHI(k → j)|.

A passing test (p > 0.05) supports the quasi-causal interpretation of LUTHI.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import RNG_SEED
from .matching import mahalanobis_knn


def placebo_p_value(real_path_luthi: pd.Series,
                    stable_pool: pd.DataFrame,
                    delta_lst: pd.Series,
                    cov_cols: list[str],
                    n_splits: int = 500,
                    k_neighbours: int = 5,
                    seed: int = RNG_SEED) -> pd.DataFrame:
    """`real_path_luthi` is indexed by (start_class, end_class) tuples or by
    transition_code; the test groups by start_class. `stable_pool` must
    contain columns dom_start (== dom_end) and all `cov_cols`.

    Returns DataFrame indexed by path with columns:
        placebo_mean, placebo_sd, placebo_p
    """
    rng = np.random.default_rng(seed)
    results = []

    by_class = {int(k): grp for k, grp in stable_pool.groupby("dom_start")}

    obs_by_start: dict[int, list[tuple]] = {}
    for path, value in real_path_luthi.items():
        ks = int(path[0]) if isinstance(path, tuple) else int(path) // 100
        obs_by_start.setdefault(ks, []).append((path, float(value)))

    for ks, path_values in obs_by_start.items():
        pool = by_class.get(ks)
        if pool is None or len(pool) < 2 * k_neighbours + 2:
            for path, v in path_values:
                results.append({"path": path, "placebo_mean": np.nan,
                                "placebo_sd": np.nan, "placebo_p": np.nan})
            continue

        idx_all = pool.index.to_numpy()
        cov_all = pool[cov_cols].to_numpy(float)
        d_all = delta_lst.reindex(idx_all).to_numpy(float)
        keep = ~np.isnan(cov_all).any(axis=1) & ~np.isnan(d_all)
        idx_all, cov_all, d_all = idx_all[keep], cov_all[keep], d_all[keep]

        placebo_estimates = []
        n = len(idx_all)
        for _ in range(n_splits):
            perm = rng.permutation(n)
            half = n // 2
            t_pos, c_pos = perm[:half], perm[half:half * 2]
            nn = mahalanobis_knn(cov_all[t_pos], cov_all[c_pos], k=k_neighbours)
            cf = d_all[c_pos][nn].mean(axis=1)
            placebo_estimates.append(float(np.mean(d_all[t_pos] - cf)))

        placebo = np.asarray(placebo_estimates)
        for path, value in path_values:
            p_value = float(np.mean(np.abs(placebo) >= abs(value)))
            results.append({
                "path": path,
                "placebo_mean": float(placebo.mean()),
                "placebo_sd": float(placebo.std(ddof=1)),
                "placebo_p": p_value,
            })

    return pd.DataFrame(results).set_index("path")
