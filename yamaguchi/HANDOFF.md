# LUTHEA — Project Handoff

**Paper**: Asymmetric surface heat impacts of decadal land-use transitions
under typical versus extreme summer conditions — a causal attribution for
compact Japanese regional cities (Yamaguchi + Yonago, 2016–2025).

**Target journal**: Urban Climate (Elsevier).
**Repository branch**: `claude/remote-sensing-urban-heat-6Gh22`
**Head commit at packaging time**: `d2683ae`
**Test suite**: 92 passing.

---

## 1. What this project is, in one paragraph

Conventional remote-sensing studies correlate *what land cover a pixel is*
with its surface temperature. LUTHEA instead asks *what the pixel became*
— it attributes summer surface-heat change to individual land-use
**transition pathways**, under three simultaneous controls (a stable
same-class reference set, weather normalisation of the Landsat record, and
Mahalanobis matching on baseline covariates). The headline claim is that
these effects are **asymmetric and state-dependent**: warming pathways
(Green→Built-up) amplify under extreme heat while cooling pathways
(Built-up→Green) collapse exactly when they are most needed. Population
exposure, heatstroke context, and compact-city policy overlays turn that
into a planning argument.

---

## 2. Current status

| Component | State |
|---|---|
| Algorithm code (`src/luthea/`, 20 modules) | ✅ complete, 92 tests passing |
| End-to-end synthetic validation | ✅ recovers α = +1.81 °C, β = +1.05 °C |
| Figure renderers (Fig 3–7) | ✅ complete, exemplars in `figures/synthetic/` |
| Manuscript conception + framework | ✅ complete, pre-registered hypotheses H1–H8 |
| Data acquisition (9 assets) | ✅ complete on the operator's machine |
| Earth Engine credentials | ✅ project `qgis-earthengine-498604` |
| **Scene-count audit** | ⚠️ **blocking — see § 5** |
| Real-data pipeline run | ⛔ not started |
| Manuscript LaTeX | ⛔ not started |

---

## 3. Repository map

```
yamaguchi/
├── HANDOFF.md                     ← this file
├── README.md                      operator quick-start
├── pyproject.toml, env/environment.yml, Makefile
│
├── docs/
│   ├── data_acquisition.md        9 data assets, step-by-step, with URLs
│   └── codex_runbook.md           browser-agent runbook for acquisition
│
├── manuscript/
│   ├── paper_conception.md        abstract, hypotheses, full Methods with
│   │                              numbered equations, expected results,
│   │                              discussion, limitations, figure captions
│   └── paper_framework.md         IMRAD skeleton, word budgets, per-paragraph
│                                  claim map, evidence ledger, DoD criteria
│
├── src/luthea/
│   ├── config.py                  every threshold, epoch, CRS, seed
│   ├── cli.py                     17 subcommands
│   ├── data_ingest/               dynamic_world, landsat_st, jma, fdma,
│   │                              estat, mlit_a50, ecostress, osm, _gee
│   ├── lst/                       selection, normalize, wnsc
│   ├── lulc/                      aggregate, transitions, trajectories
│   ├── attribution/               matching, luthi, bootstrap, placebo,
│   │                              baselines, hipi, exposure
│   ├── ml/                        xgb_attribution, shap_layer, geoshapley
│   └── viz/                       figures, sankey, maps
│
├── scripts/
│   ├── check_environment.py       30-point readiness gate
│   ├── scene_inventory.py         ⚠️ statistical-power audit (see § 5)
│   ├── build_aoi_polygons.py      generates both AOI GeoJSONs
│   └── fetch_fdma.py              heatstroke workbook downloader
│
├── notebooks/
│   └── 00_end_to_end_synthetic.py 11-stage pipeline demo, ~20 s
│
├── tests/                         92 tests
├── aoi/                           Yamaguchi AOI (11.10 km²)
├── yonago/aoi/                    Yonago AOI (10.64 km²)
└── figures/synthetic/             rendered exemplars of Fig 3–7
```

---

## 4. Method in brief

Five layers, implemented end to end:

1. **Trajectory identification** — Dynamic World 10 m labels aggregated to
   the 30 m LST grid; a cell is a valid transition only if the dominant
   class share ≥ 4/9 at both epochs.
2. **Weather-normalised LST** — Landsat 8/9 C2 L2 ST → °C, QA-masked; a
   single shared β̂ projects out overpass meteorology; per-epoch medians
   give the WNSC composites for typical and extreme strata.
3. **Spatial conditioning** — Stable Reference Set of same-class pixels;
   Mahalanobis kNN matching on baseline biophysical + multi-scale
   neighbourhood covariates; balance required at |SMD| < 0.1.
4. **Attribution** — LUTHI per pathway (matching-augmented
   difference-in-differences), HSI as the typical↔extreme triple
   difference, bootstrap 95 % CIs, within-class placebo test, and three
   baseline estimators for comparison. Path-stratified SHAP on an XGBoost
   fit under spatial cross-validation.
5. **Application** — HIPI priority raster, population exposure (250 m
   census mesh), heatstroke correlation (prefecture-level,
   correlation-only), and 都市機能誘導区域 policy overlap.

### Key equations
Eq. 1–2′ trajectory + epoch definition · Eq. 3–5′ weather normalisation and
WNSC · Eq. 6–7 SRS and matching · Eq. 8–10 LUTHI · Eq. 11 HSI ·
Eq. 12 HIPI · Eq. 13–14 bootstrap and placebo · Eq. 15a–b exposure and
policy overlays. All written out in `manuscript/paper_conception.md` § 6.

### Pre-registered hypotheses
H1 trajectory beats end-state in partial R² · **H2 (α)** HSI(Green→Built)
≈ +1.8 °C · **H3 (β)** |HSI(Built→Green)| < 0.5 °C · H4 triple control
removes ≥ 40 % of apparent warming · H5 β̂-specification stability
ρ ≥ 0.85 · H6 Yonago replication ρ ≥ 0.6 · H7 HIPI top quartile holds
≥ 30 % of population · H8 IoU with policy zone < 0.6.

---

## 5. THE ONE BLOCKING ISSUE

The Landsat record over the Yamaguchi AOI yields **18 cloud-screened summer
scenes across ten years**, unevenly distributed (1, 2, 3, 1, 1, 1, 1, 2, 2, 4
for 2016…2025). Two consequences, both already handled in code:

**(a) Single-year composites are impossible.** Five years contribute one
scene each, below the two-observation floor. The contrast is therefore
defined between **three-year epochs**: t₀ = 2016–2018 (6 scenes),
t₁ = 2023–2025 (8 scenes), with 2019–2022 reserved for robustness.

**(b) The first scene audit returned `typical = 0` everywhere.** That was
not scarcity but three defects, now fixed:

| Defect | Fix | Commit |
|---|---|---|
| AOI cloud screen fed the scene-wide `CLOUD_COVER` property (185×180 km) instead of AOI cloud fraction | `landsat_st.aoi_cloud_percent()` reduces the QA mask over the AOI geometry | `391f04d` |
| Dead zone at 33–35 °C between the typical and extreme bands | Adopted JMA official categories: 真夏日 [30, 35) and 猛暑日 [35, ∞) | `391f04d` |
| Sunshine and wind were screened **and** regressed out in β̂ — double-counting that left ~8 % of scenes | Screening now keeps only what normalisation cannot repair (cloud, wet surface); `strict=True` preserves the old conjunction for SI Table S7 | `d2683ae` |

### → NEXT ACTION (must run on the operator's machine)

```bash
cd <repo>
export PATH=/opt/homebrew/Caskroom/miniforge/base/envs/luthea/bin:$PATH
export EE_PROJECT=qgis-earthengine-498604

git fetch origin claude/remote-sensing-urban-heat-6Gh22
git merge --ff-only origin/claude/remote-sensing-urban-heat-6Gh22   # d2683ae or later
python -m pytest yamaguchi/tests -q                                  # expect 92 passed

python yamaguchi/scripts/scene_inventory.py --city yamaguchi --json /tmp/inv_yamaguchi_v2.json
python yamaguchi/scripts/scene_inventory.py --city yonago    --json /tmp/inv_yonago_v2.json
```

Report **three blocks** from each run: the per-scene table, the **filter
attrition table**, and the epoch summary with its strict-mode columns.

**Do not adjust any threshold before reading the attrition table.** If any
criterion shows `nan > 0`, that is a data-join defect and must be fixed
upstream, not compensated for by loosening a cut-point. Only if the
attrition table is clean and a cell is still short should the remediation
ladder be climbed, in the order the script prints.

---

## 6. Data assets (all acquired, on the operator's machine)

| # | Asset | Location | Verified |
|---|---|---|---|
| 1 | Yamaguchi AOI | `aoi/yamaguchi_center.geojson` | 11.10 km² |
| 2 | Yamaguchi JMA daily 81428 | `outputs/raw/jma/yamaguchi_daily.csv` | ✅ |
| 3 | Yamaguchi AMeDAS 10-min | `outputs/raw/jma/yamaguchi_10min.csv` | ✅ |
| 4 | Yonago AOI | `yonago/aoi/yonago_center.geojson` | 10.64 km² |
| 5 | Yonago JMA daily 68861 | `yonago/outputs/raw/jma/yonago_daily.csv` | 3 653 rows |
| 6 | Yonago AMeDAS 10-min | `yonago/outputs/raw/jma/yonago_10min.csv` | 175 680 rows |
| 7 | e-Stat 250 m census | `outputs/raw/estat/{yamaguchi,tottori}_250m_pop_2020/` | 22 458 / 8 913 meshes |
| 8 | MLIT A50 policy zones | `outputs/raw/mlit_a50/prefectures/` | 320 shapefiles |
| 9 | FDMA heatstroke | `outputs/raw/fdma/` | ✅ |

**`outputs/raw/` is not in this package** — it is large, and it lives on the
operator's machine. The archive contains code, documents, and the AOI
definitions only.

### Two accepted data gaps
- **Tottori (code 31) is absent from the MLIT A50-20 release.** The H8
  policy overlay is therefore reported for Yamaguchi only. No substitute
  boundary was fabricated. Documented in Limitations.
- **FDMA reports prefecture × week, not municipality × week.** All
  heatstroke analysis is correlation-only and explicitly disclaims causal
  reading.

---

## 7. Remaining work

| Phase | Task | Blocked by |
|---|---|---|
| A | Scene inventory audit (§ 5) | nothing — **do this first** |
| B | Threshold decision from the attrition evidence | A |
| C | `luthea ingest-dw` / `ingest-lst` live Drive export | B, plus explicit human authorisation |
| D | Download rasters from Drive into `outputs/{lulc,lst}/` | C |
| E | Run Steps 5–10 of the pipeline, produce real LUTHI/HSI | D |
| F | Yonago replication (H6) | E |
| G | Render Fig 1–7 with real data; build Tables 1–5 | E, F |
| H | Write LaTeX manuscript, Methods first | G |
| I | Submit to Urban Climate | H |

Recommended writing order once numbers exist: § 3 Methods → § 4 Results →
§ 5 Discussion → § 6 Limitations → § 7 Conclusion → § 1 Introduction →
Abstract → SI.

---

## 8. Working agreements observed so far

- `src/luthea/` is modified only by the upstream author, never by the
  acquisition agent.
- No non-`--dry-run` ingest without explicit human authorisation.
- `outputs/raw/` and `figures/synthetic/` are never reset, checked out, or
  cleaned.
- Every ingest subcommand that spends quota exposes `--dry-run`; a
  regression test enforces this.
- Data gaps are reported as gaps. No substitute or synthetic stand-in is
  ever put in place of a missing official dataset.

---

## 9. Reproducing the synthetic demo (no external data required)

```bash
pip install -e yamaguchi/
python yamaguchi/notebooks/00_end_to_end_synthetic.py
```

Runs all 11 stages in ~20 s and writes Fig 3–7 to
`yamaguchi/figures/synthetic/`. On synthetic data with a known
ground truth it recovers HSI(Green→Built) = +1.81 °C against a planted
+1.8 °C, and HSI(Built→Green) = +1.05 °C against a planted +1.0 °C —
which is the evidence that the estimator chain is wired correctly.
