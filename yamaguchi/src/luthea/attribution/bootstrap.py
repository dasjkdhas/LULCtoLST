"""Bootstrap percentile 95% CI for path-level LUTHI.

Each replicate re-samples treated transition pixels with replacement and
re-aggregates to path level using stored weights.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import BOOTSTRAP_B, RNG_SEED


def bootstrap_path_ci(pixel_luthi: pd.Series, path_code: pd.Series,
                      weights: pd.Series | None = None,
                      B: int = BOOTSTRAP_B, seed: int = RNG_SEED,
                      alpha: float = 0.05) -> pd.DataFrame:
    if weights is None:
        weights = pd.Series(1.0, index=pixel_luthi.index)
    df = pd.DataFrame({"luthi": pixel_luthi, "path": path_code, "w": weights}).dropna()
    rng = np.random.default_rng(seed)

    paths = df["path"].unique()
    estimates = {p: np.empty(B) for p in paths}
    by_path = {p: g.reset_index(drop=True) for p, g in df.groupby("path")}

    for b in range(B):
        for p, g in by_path.items():
            idx = rng.integers(0, len(g), len(g))
            sub = g.iloc[idx]
            estimates[p][b] = np.average(sub["luthi"], weights=sub["w"])

    rows = []
    for p, draws in estimates.items():
        est = df.loc[df["path"] == p].pipe(
            lambda x: np.average(x["luthi"], weights=x["w"]))
        rows.append({
            "path": p,
            "est": float(est),
            "ci_low": float(np.quantile(draws, alpha / 2)),
            "ci_high": float(np.quantile(draws, 1 - alpha / 2)),
        })
    return pd.DataFrame(rows).set_index("path")
