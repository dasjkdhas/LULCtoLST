"""SHAP computation, global + path-stratified."""

from __future__ import annotations

import numpy as np
import pandas as pd
import shap


def compute_shap(model, X: pd.DataFrame) -> np.ndarray:
    """TreeExplainer-based SHAP values; returns ndarray (n, p)."""
    raise NotImplementedError


def path_stratified_shap(shap_values: np.ndarray, X: pd.DataFrame,
                         path_code: pd.Series) -> pd.DataFrame:
    """Mean |SHAP| per feature, stratified by path. Long-format DataFrame."""
    raise NotImplementedError
