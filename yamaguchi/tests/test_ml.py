"""Unit tests for ML attribution + SHAP modules."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

xgb = pytest.importorskip("xgboost")
shap = pytest.importorskip("shap")

from luthea.ml.shap_layer import (compute_shap, global_summary,
                                    path_stratified_shap,
                                    top_modulators_per_path)
from luthea.ml.xgb_attribution import (make_design_matrix, partial_r2_drop,
                                        spatial_cv_train, spatial_kfold)


def _synth_dataset(n: int = 600, seed: int = 0):
    rng = np.random.default_rng(seed)
    path_labels = ["1->2", "1->3", "2->1", "3->3"]
    path_idx = rng.choice(len(path_labels), size=n, p=[0.4, 0.3, 0.2, 0.1])
    paths_str = [path_labels[i] for i in path_idx]
    x = rng.uniform(0, 100, n)
    y_coord = rng.uniform(0, 100, n)
    ndvi = rng.uniform(0, 0.8, n)
    pland_green = rng.uniform(0, 0.7, n)

    # True LUTHI: warming paths add a positive baseline; cooling subtract;
    # initial vegetation amplifies the magnitude.
    effect_by_path = {"1->2": 1.5, "1->3": 1.0, "2->1": -1.0, "3->3": 0.0}
    base = np.array([effect_by_path[p] for p in paths_str])
    luthi = base + 0.6 * ndvi - 0.4 * pland_green + rng.normal(0, 0.3, n)

    pixel_idx = pd.RangeIndex(n)
    pixel_luthi = pd.Series(luthi, index=pixel_idx)
    path_code = pd.Series(paths_str, index=pixel_idx, dtype="string")
    covariates = pd.DataFrame({"ndvi": ndvi, "pland_green": pland_green},
                              index=pixel_idx)
    xy = pd.DataFrame({"x": x, "y": y_coord}, index=pixel_idx)
    return pixel_luthi, path_code, covariates, xy


def test_make_design_matrix_one_hots_and_aligns():
    pixel_luthi, paths, cov, _ = _synth_dataset(n=50)
    X, y = make_design_matrix(pixel_luthi, paths, cov)
    assert len(X) == len(y) == 50
    onehot_cols = [c for c in X.columns if c.startswith("path_")]
    assert len(onehot_cols) == 4  # 4 distinct paths in synth dataset
    # one and only one path column fires per row
    assert (X[onehot_cols].sum(axis=1) == 1.0).all()
    assert "ndvi" in X.columns and "pland_green" in X.columns


def test_spatial_kfold_partitions_all_pixels():
    _, _, _, xy = _synth_dataset(n=200)
    folds = spatial_kfold(xy, n_splits=5, seed=0)
    assert folds.shape == (200,)
    assert set(np.unique(folds)).issubset({0, 1, 2, 3, 4})
    # each fold has at least some pixels (k-means rarely degenerates here)
    counts = pd.Series(folds).value_counts()
    assert (counts >= 10).all()


def test_spatial_cv_train_recovers_signal():
    pixel_luthi, paths, cov, xy = _synth_dataset(n=600, seed=1)
    X, y = make_design_matrix(pixel_luthi, paths, cov)
    res = spatial_cv_train(X, y, xy.loc[X.index],
                           n_splits=5, xgb_params={"n_estimators": 200})
    assert len(res.cv_metrics) >= 3
    # Synth signal is strong; mean CV R² should be well above 0
    assert res.cv_metrics["r2"].mean() > 0.4
    # Final model exposes the same feature ordering
    assert res.feature_names == list(X.columns)


def test_compute_shap_runs_and_has_correct_shape():
    pixel_luthi, paths, cov, xy = _synth_dataset(n=300, seed=2)
    X, y = make_design_matrix(pixel_luthi, paths, cov)
    res = spatial_cv_train(X, y, xy.loc[X.index],
                           n_splits=3, xgb_params={"n_estimators": 100})
    values = compute_shap(res.model, X)
    assert values.shape == X.shape


def test_global_summary_orders_descending():
    pixel_luthi, paths, cov, xy = _synth_dataset(n=300, seed=3)
    X, y = make_design_matrix(pixel_luthi, paths, cov)
    res = spatial_cv_train(X, y, xy.loc[X.index],
                           n_splits=3, xgb_params={"n_estimators": 100})
    values = compute_shap(res.model, X)
    summary = global_summary(values, list(X.columns))
    assert summary["mean_abs_shap"].is_monotonic_decreasing


def test_path_stratified_shap_long_format():
    pixel_luthi, paths, cov, xy = _synth_dataset(n=300, seed=4)
    X, y = make_design_matrix(pixel_luthi, paths, cov)
    res = spatial_cv_train(X, y, xy.loc[X.index],
                           n_splits=3, xgb_params={"n_estimators": 100})
    values = compute_shap(res.model, X)
    paths_aligned = paths.loc[X.index].reset_index(drop=True)
    long = path_stratified_shap(values, X, paths_aligned)
    assert set(long.columns) == {"path", "feature", "mean_abs_shap"}
    # 4 paths × N features
    assert len(long) == 4 * X.shape[1]


def test_top_modulators_excludes_path_onehots():
    pixel_luthi, paths, cov, xy = _synth_dataset(n=300, seed=5)
    X, y = make_design_matrix(pixel_luthi, paths, cov)
    res = spatial_cv_train(X, y, xy.loc[X.index],
                           n_splits=3, xgb_params={"n_estimators": 100})
    values = compute_shap(res.model, X)
    paths_aligned = paths.loc[X.index].reset_index(drop=True)
    long = path_stratified_shap(values, X, paths_aligned)
    top = top_modulators_per_path(long, exclude_path_onehots=True, top_n=2)
    assert top["feature"].astype(str).str.startswith("path_").sum() == 0
    # 4 paths × 2 features kept
    assert len(top) == 4 * 2


def test_partial_r2_drop_reports_full_baseline_zero():
    pixel_luthi, paths, cov, xy = _synth_dataset(n=400, seed=6)
    X, y = make_design_matrix(pixel_luthi, paths, cov)
    onehot_cols = [c for c in X.columns if c.startswith("path_")]
    drops = partial_r2_drop(X, y, xy.loc[X.index],
                            feature_groups={"trajectory": onehot_cols},
                            n_splits=3)
    assert abs(drops["_full"]) < 1e-9
    # Removing trajectory must reduce R² (drop > 0)
    assert drops["trajectory"] > 0
