# %% [markdown]
# # End-to-end LUTHEA synthetic-data quickstart
#
# This script generates a small synthetic AOI, applies every stage of the
# LUTHEA pipeline (Steps 2–9 of the plan), and reports the recovered LUTHI,
# HSI, bootstrap CIs, placebo p-values, baseline comparisons, and SHAP
# rankings. It serves as:
#
# 1. The Zenodo / SI quickstart for reviewers and replicators.
# 2. An integration test exercising every module together.
# 3. A demonstration that the **α/β asymmetry** locked in by Socratic
#    Q4 is recoverable when the data-generating process truly contains it.
#
# Runtime: ≈ 10 s on a laptop. No external data required.
#
# This file is dual-purpose: open it in Jupyter via *Jupytext* (cell
# markers `# %%`) or run it as a plain script:
#
#     python yamaguchi/notebooks/00_end_to_end_synthetic.py

# %% Imports
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from luthea.attribution.baselines import (assemble_comparison, matching_only,
                                            naive_state_contrast, standard_did)
from luthea.attribution.bootstrap import bootstrap_path_ci
from luthea.attribution.luthi import from_matched_pairs, hsi, path_luthi
from luthea.attribution.matching import (mahalanobis_knn,
                                          standardised_mean_diff,
                                          stable_reference_set)
from luthea.attribution.placebo import placebo_p_value
from luthea.lst.normalize import (METEO_FEATURES, fit_beta, normalise_table,
                                   reference_vector)
from luthea.lst.selection import label_days
from luthea.lulc.aggregate import aggregate_to_30m
from luthea.lulc.transitions import identify_transitions
from luthea.ml.shap_layer import (compute_shap, global_summary,
                                    path_stratified_shap,
                                    top_modulators_per_path)
from luthea.ml.xgb_attribution import (make_design_matrix, partial_r2_drop,
                                        spatial_cv_train)


# %% Configuration
SEED = 20260512
RNG = np.random.default_rng(SEED)

GRID_30M = 60                           # 60×60 30 m grid → 1.8 km × 1.8 km
GRID_10M = GRID_30M * 3                 # 180×180 underlying 10 m cells
N_SCENES_PER_EPOCH = 8                  # 4 typical + 4 extreme per epoch

# Dynamic World class codes used in this synthetic AOI
TREES, GRASS, BUILT, BARE = 1, 2, 6, 7
ALL_CLASSES = [TREES, GRASS, BUILT, BARE]

# Per-class baseline LST in °C (built > bare > grass > trees)
CLASS_BASELINE_C = {TREES: 22.0, GRASS: 25.0, BUILT: 32.0, BARE: 28.0}

# True coefficients of the meteorological response (β̂ should recover these)
TRUE_BETA = dict(t_air=0.80, rh=-0.05, wind=-0.40, sun_48h=0.15)

# Treatment effects we *should* see in LUTHI / HSI:
# α — Green→Built warms; warming extra-amplified under extreme heat
ALPHA_TYP_PER_PIXEL = 0.4     # typical-day extra warming on Green→Built pixels
ALPHA_EXT_PER_PIXEL = 2.2     # extreme-day extra warming → HSI ≈ +1.8 °C
# β — Built→Green cools; cooling collapses under extreme heat
BETA_TYP_PER_PIXEL = -1.2     # typical-day extra cooling on Built→Green pixels
BETA_EXT_PER_PIXEL = -0.2     # extreme-day cooling barely visible → |HSI| ≈ 1.0


# %% [markdown]
# ## Stage 1 — Synthetic 10 m LULC at two epochs

# %% Build LULC fields
t0_labels = RNG.choice(ALL_CLASSES, size=(GRID_10M, GRID_10M),
                       p=[0.40, 0.20, 0.25, 0.15])
t1_labels = t0_labels.copy()

mask_green = np.isin(t0_labels, [TREES, GRASS])
mask_built = t0_labels == BUILT
mask_bare = t0_labels == BARE

# Realistic transition rates (Yamaguchi-like)
green_to_built = mask_green & (RNG.random((GRID_10M, GRID_10M)) < 0.18)
bare_to_built = mask_bare & (RNG.random((GRID_10M, GRID_10M)) < 0.45)
built_to_green = mask_built & (RNG.random((GRID_10M, GRID_10M)) < 0.08)

t1_labels[green_to_built] = BUILT
t1_labels[bare_to_built] = BUILT
t1_labels[built_to_green] = TREES


def _to_da(arr: np.ndarray) -> xr.DataArray:
    return xr.DataArray(
        arr.astype("int16"),
        dims=("y", "x"),
        coords={"y": np.arange(arr.shape[0]), "x": np.arange(arr.shape[1])},
    )


dw_t0 = _to_da(t0_labels)
dw_t1 = _to_da(t1_labels)
print(f"[Stage 1] LULC fields generated: 10 m grid {GRID_10M}×{GRID_10M}")


# %% [markdown]
# ## Stage 2 — Aggregate to 30 m and identify transitions (Step 6)

# %% Aggregate
ds_t0 = aggregate_to_30m(dw_t0, n_classes=9, factor=3)
ds_t1 = aggregate_to_30m(dw_t1, n_classes=9, factor=3)
transitions = identify_transitions(ds_t0, ds_t1)

trans_df = (transitions[["dom_start", "dom_end", "valid"]]
            .to_dataframe()
            .reset_index(drop=True))
trans_df["pixel_id"] = trans_df.index

n_valid = int(trans_df["valid"].sum())
print(f"[Stage 2] {n_valid}/{len(trans_df)} valid 30 m pixels")
print(trans_df.loc[trans_df["valid"]]
      .groupby(["dom_start", "dom_end"]).size().sort_values(ascending=False).head(8))


# %% [markdown]
# ## Stage 3 — Synthetic meteorology and Landsat-like LST scenes

# %% Build per-scene meteo + per-pixel LST for the two epochs
def make_scene_meteo(extreme: bool, date: pd.Timestamp) -> dict:
    if extreme:
        t_max = float(RNG.uniform(35.5, 37.0))
        sunshine_h = float(RNG.uniform(9.5, 11.0))
    else:
        t_max = float(RNG.uniform(30.5, 32.5))
        sunshine_h = float(RNG.uniform(8.0, 10.0))
    return dict(
        date=date,
        t_max=t_max,
        t_air=t_max - 2.0,
        rh=float(RNG.uniform(50, 75)),
        wind=float(RNG.uniform(1.0, 2.5)),
        sun_48h=sunshine_h,
        sunshine_h=sunshine_h,
        precip_mm=0.0,
        cumrain_48h=0.0,
        overpass_wind=float(RNG.uniform(1.0, 2.5)),
        scene_cloud_pct=float(RNG.uniform(0, 4)),
        is_extreme=extreme,
    )


def build_scene(dom_field: np.ndarray, meteo: dict, treatment_field: np.ndarray
                ) -> np.ndarray:
    """Synthetic LST = class baseline + linear meteo response + treatment effect + noise."""
    base = np.zeros_like(dom_field, dtype=float)
    for cls, val in CLASS_BASELINE_C.items():
        base[dom_field == cls] = val
    meteo_term = (
        TRUE_BETA["t_air"] * (meteo["t_air"] - 26.0)
        + TRUE_BETA["rh"] * (meteo["rh"] - 60.0)
        + TRUE_BETA["wind"] * (meteo["wind"] - 1.5)
        + TRUE_BETA["sun_48h"] * (meteo["sun_48h"] - 9.0)
    )
    noise = RNG.normal(0.0, 0.30, size=base.shape)
    return base + meteo_term + treatment_field + noise


dom_start = ds_t0["dominant"].to_numpy()
dom_end = ds_t1["dominant"].to_numpy()

# Pre-compute spatial treatment fields (zero except for the transitioned pixels)
green_to_built_mask = (np.isin(dom_start, [TREES, GRASS]) & (dom_end == BUILT))
bare_to_built_mask = ((dom_start == BARE) & (dom_end == BUILT))
built_to_green_mask = ((dom_start == BUILT) & np.isin(dom_end, [TREES, GRASS]))


def treatment_field(scenario: str) -> np.ndarray:
    """Returns the per-pixel treatment additive at t1 under either scenario.

    Note: at t0 (before transition), there is no treatment field — return zeros.
    """
    f = np.zeros_like(dom_start, dtype=float)
    if scenario == "extreme":
        f[green_to_built_mask] += ALPHA_EXT_PER_PIXEL
        f[bare_to_built_mask] += ALPHA_EXT_PER_PIXEL * 0.85
        f[built_to_green_mask] += BETA_EXT_PER_PIXEL
    elif scenario == "typical":
        f[green_to_built_mask] += ALPHA_TYP_PER_PIXEL
        f[bare_to_built_mask] += ALPHA_TYP_PER_PIXEL * 0.85
        f[built_to_green_mask] += BETA_TYP_PER_PIXEL
    return f


scene_records = []           # rows for selection / β̂ fit
scenes_t0 = {"typical": [], "extreme": []}
scenes_t1 = {"typical": [], "extreme": []}

for epoch_label, dom_field, scene_list in [("t0", dom_start, scenes_t0),
                                            ("t1", dom_end, scenes_t1)]:
    for i in range(N_SCENES_PER_EPOCH):
        is_ext = (i % 2 == 1)
        scen = "extreme" if is_ext else "typical"
        date = pd.Timestamp(f"{2016 if epoch_label=='t0' else 2025}-07-{10 + i:02d}")
        meteo = make_scene_meteo(extreme=is_ext, date=date)

        treat = treatment_field(scen) if epoch_label == "t1" else np.zeros_like(dom_field, dtype=float)
        lst = build_scene(dom_field, meteo, treat)

        scene_list[scen].append(lst)
        scene_records.append({"epoch": epoch_label, "scenario": scen, **meteo})

print(f"[Stage 3] {len(scene_records)} synthetic LST scenes built "
      f"(2 epochs × {N_SCENES_PER_EPOCH} scenes)")


# %% [markdown]
# ## Stage 4 — Day selection (Step 4)
#
# Verify that `label_days` correctly partitions our scenes into typical /
# extreme by the configured thresholds.

# %% Run selection
meteo_df = pd.DataFrame(scene_records)
labelled = label_days(meteo_df)
print(labelled.groupby(["epoch", "scenario"])
      [["is_typical", "is_extreme"]].sum())


# %% [markdown]
# ## Stage 5 — Weather normalisation + WNSC compose (Step 5)

# %% Fit β̂ and build WNSC composites
H, W = dom_start.shape

# Build a long table of (pixel × scene) for β̂ fit.
long_rows = []
for rec, eps_field in zip(scene_records,
                          [*scenes_t0["typical"], *scenes_t0["extreme"],
                           *scenes_t1["typical"], *scenes_t1["extreme"]]):
    flat = eps_field.ravel()
    long_rows.append(pd.DataFrame({
        "pixel_id": np.arange(flat.size),
        "lst": flat,
        "t_air": rec["t_air"],
        "rh": rec["rh"],
        "wind": rec["wind"],
        "sun_48h": rec["sun_48h"],
    }))
long_df = pd.concat(long_rows, ignore_index=True)
sample = long_df.sample(n=min(30_000, len(long_df)), random_state=SEED)
beta_hat = fit_beta(sample)
print(f"[Stage 5] β̂ recovered: " +
      ", ".join(f"{k}={beta_hat[k]:+.3f}" for k in METEO_FEATURES))
print(f"           true β:    " +
      ", ".join(f"{k}={TRUE_BETA[k]:+.3f}" for k in METEO_FEATURES))

ref_mask = labelled["is_typical"]
ref_vec = reference_vector(meteo_df.assign(**{
    "t_air": meteo_df["t_air"], "rh": meteo_df["rh"],
    "wind": meteo_df["wind"], "sun_48h": meteo_df["sun_48h"],
}), ref_mask)


def normalise_field(field: np.ndarray, meteo: dict) -> np.ndarray:
    delta = sum(beta_hat[k] * (meteo[k] - ref_vec[k]) for k in METEO_FEATURES)
    return field - delta


# WNSC composite per epoch × scenario
def wnsc(scenes: list[np.ndarray], scen_records: list[dict]) -> np.ndarray:
    normed = np.stack([normalise_field(s, m)
                       for s, m in zip(scenes, scen_records)])
    return np.median(normed, axis=0)


t0_typ_records = [r for r in scene_records if r["epoch"] == "t0" and r["scenario"] == "typical"]
t0_ext_records = [r for r in scene_records if r["epoch"] == "t0" and r["scenario"] == "extreme"]
t1_typ_records = [r for r in scene_records if r["epoch"] == "t1" and r["scenario"] == "typical"]
t1_ext_records = [r for r in scene_records if r["epoch"] == "t1" and r["scenario"] == "extreme"]

WNSC_t0_typ = wnsc(scenes_t0["typical"], t0_typ_records)
WNSC_t0_ext = wnsc(scenes_t0["extreme"], t0_ext_records)
WNSC_t1_typ = wnsc(scenes_t1["typical"], t1_typ_records)
WNSC_t1_ext = wnsc(scenes_t1["extreme"], t1_ext_records)

delta_typ = (WNSC_t1_typ - WNSC_t0_typ).ravel()
delta_ext = (WNSC_t1_ext - WNSC_t0_ext).ravel()
print(f"[Stage 5] ΔWNSC stats — typ: mean={delta_typ.mean():+.2f} sd={delta_typ.std():.2f}"
      f"; ext: mean={delta_ext.mean():+.2f} sd={delta_ext.std():.2f}")


# %% [markdown]
# ## Stage 6 — Stable Reference Set + Mahalanobis matching (Step 7)

# %% Build covariates and match
covariates = pd.DataFrame({
    "ndvi_t0": RNG.uniform(0.1, 0.7, len(trans_df)),       # synthetic NDVI baseline
    "albedo_t0": RNG.uniform(0.10, 0.25, len(trans_df)),
    "dem": RNG.uniform(0, 50, len(trans_df)),
}, index=trans_df.index)

trans_df = trans_df.set_index("pixel_id")
covariates.index = trans_df.index

srs = stable_reference_set(trans_df)
print(f"[Stage 6] Stable reference set sizes: " +
      ", ".join(f"class={k}:{len(v)}" for k, v in srs.items()))


def build_matched(scenario: str) -> tuple[pd.DataFrame, pd.Series]:
    delta = pd.Series(delta_typ if scenario == "typical" else delta_ext,
                      index=trans_df.index, name="delta")
    matches_rows = []
    for (ks, ke), grp in trans_df[trans_df["valid"]].groupby(["dom_start", "dom_end"]):
        if int(ks) == int(ke):
            continue
        pool_idx = srs.get(int(ks))
        if pool_idx is None or len(pool_idx) < 5:
            continue
        treated_idx = grp.index.to_numpy()
        treated_X = covariates.loc[treated_idx].to_numpy(float)
        ref_X = covariates.loc[pool_idx].to_numpy(float)
        nn = mahalanobis_knn(treated_X, ref_X, k=5)
        for ti, neigh in zip(treated_idx, nn):
            for rank, n_local in enumerate(neigh):
                matches_rows.append((ti, int(pool_idx[n_local]), rank))
    return pd.DataFrame(matches_rows,
                        columns=["treated_idx", "control_idx", "neighbour_rank"]), delta


matched_typ, delta_typ_s = build_matched("typical")
matched_ext, delta_ext_s = build_matched("extreme")
print(f"[Stage 6] matched pairs: typ={len(matched_typ)} rows, ext={len(matched_ext)} rows")


# %% [markdown]
# ## Stage 7 — LUTHI / HSI / bootstrap / placebo (Step 8)

# %% Compute LUTHI per scenario
luthi_typ_px = from_matched_pairs(matched_typ, delta_typ_s)
luthi_ext_px = from_matched_pairs(matched_ext, delta_ext_s)

# Tag each treated pixel with its path tuple
path_lookup = (trans_df[["dom_start", "dom_end"]]
               .apply(lambda r: (int(r["dom_start"]), int(r["dom_end"])), axis=1))
paths_typ = path_lookup.reindex(luthi_typ_px.index)
paths_ext = path_lookup.reindex(luthi_ext_px.index)

luthi_typ_path = path_luthi(luthi_typ_px, paths_typ)
luthi_ext_path = path_luthi(luthi_ext_px, paths_ext)
hsi_path = hsi(luthi_typ_path, luthi_ext_path)

print("[Stage 7] Path-level LUTHI / HSI:")
print(pd.concat({"LUTHI_typ": luthi_typ_path,
                 "LUTHI_ext": luthi_ext_path,
                 "HSI": hsi_path}, axis=1).round(2))

# Bootstrap CI on the typical-scenario headline
boot_typ = bootstrap_path_ci(luthi_typ_px, paths_typ, B=200, seed=SEED)
boot_ext = bootstrap_path_ci(luthi_ext_px, paths_ext, B=200, seed=SEED)
print("[Stage 7] Bootstrap 95% CI (typ):")
print(boot_typ.round(2))
print("[Stage 7] Bootstrap 95% CI (ext):")
print(boot_ext.round(2))

# Placebo
stable_pool_df = trans_df[trans_df["dom_start"] == trans_df["dom_end"]].copy()
stable_pool_df = stable_pool_df.join(covariates)
placebo = placebo_p_value(
    real_path_luthi=luthi_ext_path,
    stable_pool=stable_pool_df,
    delta_lst=delta_ext_s,
    cov_cols=["ndvi_t0", "albedo_t0", "dem"],
    n_splits=80,
    k_neighbours=5,
    seed=SEED,
)
print("[Stage 7] Placebo p-values (extreme):")
print(placebo.round(3))


# %% [markdown]
# ## Stage 8 — Baseline-estimator comparison (defence a; SI Table S4)

# %% Run baselines on the same pixels
flat_index = trans_df.index
lst_t0_typ = pd.Series(WNSC_t0_typ.ravel(), index=flat_index, name="lst_t0")
lst_t1_typ = pd.Series(WNSC_t1_typ.ravel(), index=flat_index, name="lst_t1")
lst_t0_ext = pd.Series(WNSC_t0_ext.ravel(), index=flat_index, name="lst_t0")
lst_t1_ext = pd.Series(WNSC_t1_ext.ravel(), index=flat_index, name="lst_t1")

naive = naive_state_contrast(trans_df["dom_end"], lst_t0_typ, lst_t1_typ)
did = standard_did(trans_df["dom_start"], trans_df["dom_end"],
                   lst_t0_typ, lst_t1_typ, valid=trans_df["valid"])
mo = matching_only(covariates, trans_df, cov_cols=["ndvi_t0", "albedo_t0", "dem"],
                   lst_t0=lst_t0_typ, lst_t1=lst_t1_typ, k_neighbours=5)

cmp = assemble_comparison(luthi_typ_path, naive, did, mo)
print("[Stage 8] Baseline comparison (typical scenario):")
print(cmp.round(2))


# %% [markdown]
# ## Stage 9 — XGBoost + path-stratified SHAP (Step 9)

# %% Train and explain
pixel_luthi_combined = pd.concat([luthi_typ_px.rename("LUTHI"),
                                  luthi_ext_px.rename("LUTHI")])
# Use only the typical-scenario predictions to keep this stage tight
pixel_luthi_train = luthi_typ_px.rename("LUTHI")

paths_str = paths_typ.astype(str)
cov_for_ml = covariates.reindex(pixel_luthi_train.index)
X, y = make_design_matrix(pixel_luthi_train, paths_str, cov_for_ml)

xy_grid = pd.DataFrame({
    "x": np.tile(np.arange(W), H)[X.index.values],
    "y": np.repeat(np.arange(H), W)[X.index.values],
}, index=X.index)

cv = spatial_cv_train(X, y, xy_grid, n_splits=5,
                      xgb_params={"n_estimators": 200})
print(f"[Stage 9] Spatial CV — mean R² = {cv.cv_metrics['r2'].mean():.3f} "
      f"(n folds = {len(cv.cv_metrics)})")

shap_vals = compute_shap(cv.model, X)
print("[Stage 9] Global SHAP top features:")
print(global_summary(shap_vals, list(X.columns)).head(6))

long_shap = path_stratified_shap(shap_vals, X, paths_str)
top = top_modulators_per_path(long_shap, exclude_path_onehots=True, top_n=3)
print("[Stage 9] Top-3 modulators per path:")
print(top)


# %% [markdown]
# ## Stage 10 — H1 test: trajectory > end-state in partial R²

# %% Partial R² ablation
traj_cols = [c for c in X.columns if c.startswith("path_")]
drops = partial_r2_drop(X, y, xy_grid,
                        feature_groups={"trajectory_one_hots": traj_cols},
                        n_splits=5)
print(f"[Stage 10] Partial R² drop when trajectory one-hots removed: "
      f"{drops['trajectory_one_hots']:.3f}")


# %% [markdown]
# ## Summary — what should be visible
#
# When the script runs end-to-end without error and prints:
#
# * β̂ recovered within ~0.05 of TRUE_BETA on every coefficient — Stage 5 sanity;
# * LUTHI(Green→Built, typ) close to ALPHA_TYP_PER_PIXEL (~+0.4 °C);
# * LUTHI(Green→Built, ext) close to ALPHA_EXT_PER_PIXEL (~+2.2 °C);
# * HSI(Green→Built) > +1.0 °C — α confirmed;
# * LUTHI(Built→Green, typ) ≈ BETA_TYP_PER_PIXEL (~−1.2 °C);
# * LUTHI(Built→Green, ext) ≈ BETA_EXT_PER_PIXEL (~−0.2 °C);
# * |HSI(Built→Green)| ≈ +1.0 °C with positive sign — β confirmed (cooling collapses);
# * placebo p-values for both α and β headline paths > 0.05;
# * spatial CV R² > 0.4;
# * partial R² drop when removing trajectory one-hots > 0;
#
# then the full pipeline is operationally consistent and the α/β central
# claim is *recoverable from data* — which is the soft prerequisite
# before any real-data Yamaguchi run.

print("\n[done] Synthetic end-to-end pipeline ran to completion.")
