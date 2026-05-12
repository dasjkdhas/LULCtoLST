# Yamaguchi LUTHEA pipeline

Implements the **L**and-**U**se **T**ransition-based **H**eat **E**xposure
**A**ttribution framework for the central district of Yamaguchi City, Japan
(2016–2025). The companion second case city scaffold is under `../yonago/`.

The detailed reasoning, methodology, and step-by-step plan live in:
**`/root/.claude/plans/token-token-quiet-bachman.md`** — read it first.

---

## Quick start

```bash
# 1. Create environment (pick one)
mamba env create -f env/environment.yml
# or:
pip install -e .[gee,nasa,causal,viz]

conda activate luthea

# 2. Authenticate
earthengine authenticate          # opens browser
earthaccess login                 # NASA Earthdata; needed only for ECOSTRESS

# 3. Verify
python -c "import ee; ee.Initialize(); print(ee.Number(42).getInfo())"
```

---

## Pipeline (mirrors plan Steps 0–14)

| Step | Module / Command | Input | Output |
|---|---|---|---|
| 1 | hand-drawn in QGIS | — | `aoi/yamaguchi_center.geojson` |
| 2 | `luthea ingest-dw` | AOI | `outputs/lulc/dw_lulc_YYYY.tif` |
| 3 | `luthea ingest-lst` | AOI | `outputs/lst/lst_YYYYMMDD.tif` |
| 4 | `luthea ingest-jma` + `select-days` | raw JMA CSV under `outputs/raw/jma/` | `outputs/lst/selected_dates.csv` |
| 5 | `luthea normalise-lst` + `wnsc` | LST scenes + meteo | `outputs/lst/wnsc_YYYY.tif`, `wnsc_ext_YYYY.tif` |
| 6 | `luthea aggregate-lulc` + `transitions` | DW LULC | `outputs/lulc/transitions_2016_2025.tif` |
| 7 | `luthea match` | covariates + transitions | `outputs/matching/matched_pairs.parquet` |
| 8 | `luthea luthi` + `bootstrap` + `placebo` | WNSC + matching | `outputs/luthi/luthi_results.csv` |
| 9 | `luthea ml-attribute` | LUTHI + covariates | `outputs/ml/xgb_model.pkl`, `shap_values.parquet` |
| 10 | `luthea hipi` | WNSC + neighbourhood | `outputs/hipi/hipi.tif` |
| 12 | `luthea figures` | all of the above | `figures/fig{1..8}.png` |

`luthea all` will eventually chain everything; for now each subcommand prints a
TODO until the underlying functions are filled in.

---

## Data you must supply by hand

These cannot be auto-downloaded:

1. **AOI polygon** of the central district (`aoi/yamaguchi_center.geojson`).
   Draw in QGIS over an OSM basemap; include 山口駅 / 湯田温泉 / 中央商店街 / 県庁;
   target area 8–15 km². CRS = EPSG:4326.
2. **JMA daily CSV** for station 山口 (観測所番号 81428), period 2016-01-01 to
   2025-12-31. Save at `outputs/raw/jma/yamaguchi_daily.csv`.
3. **AMeDAS 10-min CSV** for the same station and period, restricted to summer
   months. Save at `outputs/raw/jma/yamaguchi_10min.csv`.
4. *(optional)* Training/validation polygons if you intend to run a local
   `sits`/RF refinement of Dynamic World; save under `outputs/raw/samples/`.

Everything else is pulled in code from GEE or NASA Earthdata.

---

## Reproducibility contract

- `config.py` holds every threshold, station ID, CRS, and seed.
- All randomness goes through `numpy.random.default_rng(seed=RNG_SEED)`.
- All intermediate products are written as GeoTIFF (raster) or Parquet
  (tabular) under `outputs/`, gitignored by default — re-runnable from
  `config.py` alone.

---

## Methodology one-pager

**Triple control (the manuscript's headline):**

1. *Temporal control* — a Stable Reference Set of co-class pixels supplies a
   counterfactual ΔLST for each transition pixel.
2. *Meteorological control* — overpass-time AMeDAS covariates are projected
   out of pixel-level LST via a shared β̂, producing a Weather-Normalised
   Summer LST Composite (WNSC).
3. *Spatial control* — Mahalanobis kNN matching on baseline biophysical and
   multi-scale neighbourhood covariates enforces SMD < 0.1 between treated
   transition pixels and reference pixels.

**LUTHI** (Land-Use Transition Heat Impact Index) is then a difference-in-
differences estimator over matched pairs, computed pixel-wise, aggregated
to path level (weighted by effective area), and stratified by scenario
(typical / extreme) and neighbourhood radius (100 / 300 / 500 m).
Inference: bootstrap percentile 95% CI + within-class placebo test.

**SHAP** is applied path-stratified to disentangle which baseline conditions
modulate each transition's heat impact.

**HIPI** (Heat Improvement Priority Index) translates the attribution into
a planning-ready raster: priority quartiles ranked by WNSC × low PLAND_Green
× HSI × pedestrian density.

---

## Status (2026-05-12)

- [x] Repository scaffold (this commit).
- [ ] AOI polygon.
- [ ] GEE / Earthdata authentication on operator's machine.
- [ ] Data ingestion modules implemented.
- [ ] Algorithm modules implemented.
- [ ] Figures and tables generated.
- [ ] Manuscript drafted.
- [ ] Submitted to *Remote Sensing*.
