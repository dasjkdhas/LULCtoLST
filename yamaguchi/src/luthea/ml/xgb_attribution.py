"""Step 9 — XGBoost regression of LUTHI_pixel on path one-hot + covariates,
with spatial 5-fold CV.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import xgboost as xgb


def make_design_matrix(pixel_luthi: pd.Series, path_code: pd.Series,
                       covariates: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """One-hot the path code and concatenate with covariates → (X, y)."""
    raise NotImplementedError


def spatial_cv_train(X: pd.DataFrame, y: pd.Series, xy: pd.DataFrame,
                     n_splits: int = 5) -> dict:
    """Spatial KMeans cluster splits; return dict with fold metrics and a final
    model retrained on all data."""
    raise NotImplementedError
