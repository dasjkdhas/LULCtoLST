"""Placebo test: within-class pseudo-transitions should yield LUTHI ≈ 0.

Procedure:
  1. Within each stable class k, randomly split pixels into two equal halves.
  2. Treat one half as 'treated' and the other as 'reference pool'.
  3. Run the same matching + LUTHI computation.
  4. Repeat over many random splits; p-value = fraction of |LUTHI_placebo|
     ≥ observed |LUTHI_real|.

A passing test (p > 0.05) is required to support the quasi-causal claim.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import RNG_SEED


def placebo_p_value(real_path_luthi: pd.Series, stable_pool: pd.DataFrame,
                    n_splits: int = 500, seed: int = RNG_SEED) -> pd.Series:
    raise NotImplementedError
