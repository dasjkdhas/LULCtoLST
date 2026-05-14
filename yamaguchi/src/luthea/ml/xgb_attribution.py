"""Step 9 — XGBoost regression of LUTHI_pixel on a feature design matrix
that combines transition-path one-hots, baseline covariates, and
multi-scale neighbourhood class shares, evaluated under spatial 5-fold
cross-validation to avoid spatial-autocorrelation leakage.

Manuscript reference: § 3.6 (path-level ML attribution).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_XGB_PARAMS: dict[str, Any] = dict(
    n_estimators=500,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_lambda=1.0,
    random_state=20260512,
    n_jobs=-1,
    tree_method="hist",
)


def make_design_matrix(pixel_luthi: pd.Series, path_code: pd.Series,
                       covariates: pd.DataFrame
                       ) -> tuple[pd.DataFrame, pd.Series]:
    """Build (X, y) for the LUTHI regression.

    `path_code` is treated as a categorical variable and one-hot encoded
    (using path tuples or integer codes — both supported). Covariate
    columns are concatenated unchanged.
    """
    if not pixel_luthi.index.equals(covariates.index):
        common = pixel_luthi.index.intersection(covariates.index)
        pixel_luthi = pixel_luthi.loc[common]
        path_code = path_code.loc[common]
        covariates = covariates.loc[common]

    paths = path_code.astype("string")
    one_hot = pd.get_dummies(paths, prefix="path", dtype=float)

    X = pd.concat([one_hot, covariates], axis=1)
    y = pixel_luthi.copy()

    keep = X.notna().all(axis=1) & y.notna()
    return X.loc[keep], y.loc[keep]


def spatial_kfold(xy: pd.DataFrame, n_splits: int = 5,
                  seed: int = 20260512) -> np.ndarray:
    """K-means on (x, y) projected coordinates → integer fold labels.

    Using spatial clusters as folds is a common defence against
    autocorrelation-driven over-optimistic CV scores in raster regression.
    """
    from sklearn.cluster import KMeans
    coords = xy[["x", "y"]].to_numpy(float)
    km = KMeans(n_clusters=n_splits, random_state=seed, n_init=10)
    return km.fit_predict(coords)


@dataclass
class CVResult:
    cv_metrics: pd.DataFrame
    model: Any
    folds: np.ndarray
    feature_names: list[str]


def spatial_cv_train(X: pd.DataFrame, y: pd.Series, xy: pd.DataFrame,
                     n_splits: int = 5,
                     xgb_params: dict[str, Any] | None = None,
                     seed: int = 20260512) -> CVResult:
    """Train an XGBoost regressor under spatial k-fold CV and return the
    fold-by-fold metrics together with a final model retrained on **all**
    data (the headline model used for SHAP attribution)."""
    import xgboost as xgb
    from sklearn.metrics import mean_absolute_error, r2_score

    params = dict(DEFAULT_XGB_PARAMS, **(xgb_params or {}))
    folds = spatial_kfold(xy.loc[X.index], n_splits=n_splits, seed=seed)
    folds_series = pd.Series(folds, index=X.index, name="fold")

    rows = []
    for f in range(n_splits):
        train_mask = (folds_series != f).to_numpy()
        test_mask = (folds_series == f).to_numpy()
        if test_mask.sum() < 5 or train_mask.sum() < 20:
            continue
        m = xgb.XGBRegressor(**params)
        m.fit(X.iloc[train_mask], y.iloc[train_mask],
              verbose=False)
        pred = m.predict(X.iloc[test_mask])
        rows.append({
            "fold": f,
            "n_train": int(train_mask.sum()),
            "n_test": int(test_mask.sum()),
            "r2": float(r2_score(y.iloc[test_mask], pred)),
            "mae": float(mean_absolute_error(y.iloc[test_mask], pred)),
        })

    final = xgb.XGBRegressor(**params)
    final.fit(X, y, verbose=False)

    return CVResult(
        cv_metrics=pd.DataFrame(rows),
        model=final,
        folds=folds,
        feature_names=list(X.columns),
    )


def partial_r2_drop(X: pd.DataFrame, y: pd.Series, xy: pd.DataFrame,
                    feature_groups: dict[str, list[str]],
                    n_splits: int = 5, seed: int = 20260512) -> pd.Series:
    """For each named group of feature columns, refit the model with that
    group **removed** and report the drop in mean CV R² versus the full
    model. Supports H1 (trajectory > end-state in explanatory power) when
    one group is the transition one-hots and another is end-state one-hots.
    """
    base = spatial_cv_train(X, y, xy, n_splits=n_splits, seed=seed)
    full_r2 = float(base.cv_metrics["r2"].mean())

    drops = {"_full": 0.0}
    for name, cols in feature_groups.items():
        cols_to_drop = [c for c in cols if c in X.columns]
        if not cols_to_drop:
            drops[name] = np.nan
            continue
        sub = X.drop(columns=cols_to_drop)
        ablated = spatial_cv_train(sub, y, xy, n_splits=n_splits, seed=seed)
        drops[name] = full_r2 - float(ablated.cv_metrics["r2"].mean())
    return pd.Series(drops, name="partial_R2_drop")
