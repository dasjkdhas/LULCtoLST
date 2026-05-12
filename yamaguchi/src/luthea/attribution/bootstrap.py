"""Bootstrap CI for path-level LUTHI.

Block-bootstrap over transition pixels (B = BOOTSTRAP_B); each replicate also
re-samples the matched reference pool. Returns percentile 95% CI per path.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import BOOTSTRAP_B, RNG_SEED


def bootstrap_path_ci(pixel_luthi: pd.Series, path_code: pd.Series,
                      weights: pd.Series, B: int = BOOTSTRAP_B,
                      seed: int = RNG_SEED) -> pd.DataFrame:
    """Return DataFrame indexed by path with columns [est, ci_low, ci_high]."""
    raise NotImplementedError
