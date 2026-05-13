# Paper Conception — LUTHEA / LUTHI, Yamaguchi 2016–2025

> Working document for the SCI paper described in
> `/root/.claude/plans/token-token-quiet-bachman.md`.
> Target journal: **Remote Sensing** (primary), Urban Climate /
> GIScience & Remote Sensing / Sustainable Cities and Society as fallbacks.
> Status: pre-data; numbers in *Results* are hypothesised ranges to be
> filled in after pipeline runs.

---

## 1. Title candidates

1. **LUTHEA: A Quasi-Causal Attribution Framework for Land-Use Transition-Driven Urban Heat Change Using Multi-Source Satellite Data**  *(primary)*
2. Beyond State, Toward Trajectory: A Multi-Scale Land-Use Transition Heat Impact Index (LUTHI) for Compact Japanese Cities
3. Weather-Normalised Attribution of Decadal Land-Use Transitions to Urban Heat Exposure in a Compact Japanese City
4. Disentangling Typical and Extreme Summer Heat Responses to Land-Use Transitions: A Multi-Scale Remote Sensing Framework

Decision rule: **Title 1** for *Remote Sensing* (method-first); switch to
**Title 3** if redirected to *Urban Climate* (case-driven, climate-framed).

---

## 2. Abstract (≈ 240 words, draft)

> Rapid land-use/land-cover (LULC) change in compact mid-sized cities
> reshapes urban surface heat in ways that conventional state-based
> remote-sensing analyses tend to under-resolve. We propose **LUTHEA**, a
> Land-Use Transition-based Heat Exposure Attribution framework, that
> treats LULC change as a process (trajectory) rather than a state. The
> framework integrates a per-pixel **Land-Use Transition Heat Impact Index
> (LUTHI)** computed from weather-normalised, Landsat 8/9 Collection 2
> Level-2 surface temperature against a 10 m Dynamic World–derived
> trajectory raster, with **triple control**: a Stable Reference Set
> providing per-class counterfactuals (temporal control), shared β̂
> projection of overpass-time meteorological covariates (meteorological
> control), and multi-scale Mahalanobis kNN matching on baseline
> biophysical and neighbourhood covariates (spatial control).
> Uncertainty is quantified by bootstrap 95 % confidence intervals and
> a within-class placebo test, supporting a quasi-causal interpretation.
> Path-level XGBoost attribution with stratified SHAP partitions LUTHI
> across transitions; a Heat Improvement Priority Index (HIPI) translates
> the attribution into a planning-ready raster. We apply the framework to
> the central district of Yamaguchi City, Japan (2016–2025), and provide
> a transferability check on a second compact city. We report which
> decadal transitions contributed most to summer surface heat, how
> contributions diverge between typical and extreme summer days, and
> where heat mitigation is most cost-effective. The pipeline is released
> as an open Python package applicable to any city with Dynamic World
> and Landsat coverage.

---

## 3. Core science question

> Which **decadal land-use transition pathways** have contributed most
> to changes in summer surface urban heat exposure in a compact Japanese
> city, **after controlling for inter-annual meteorological variability,
> neighbourhood landscape configuration, and pre-existing site
> characteristics**, and how do these contributions differ between
> **typical and extreme** summer days?

### Hypotheses

| ID | Statement | Test |
|---|---|---|
| H1 | Trajectory has higher explanatory power than end-state LULC for ΔLST. | XGBoost feature-importance ranking; partial R² after removing trajectory one-hot vs after removing end-state one-hot. |
| H2 | Green→Built-up and Bare→Built-up yield LUTHI > 0 with 95 % CIs not crossing zero; Built-up→Green yields LUTHI < 0. | Path-level LUTHI bootstrap CIs. |
| H3 | The extreme-vs-typical asymmetry (HSI) is positive and larger for warming transitions than for cooling transitions. | Sign + magnitude of HSI per path; paired comparison. |
| H4 | LUTHI is most diagnostic at the 300 m neighbourhood scale (intermediate). | SSI = ∂LUTHI/∂r evaluated at r = 300 m; sign change between 100 m and 500 m. |
| H5 | After triple control, the residual decadal LST trend at the city centre is materially smaller than the raw difference, indicating that prior literature overstates the LULC-only effect by failing to control meteorology. | Compare raw ΔLST vs ΔLST_norm summary statistics. |

---

## 4. Contributions (Introduction's last paragraph, in order)

1. A *quasi-causal* attribution framework for LULC-driven urban heat
   change, departing from state-based correlational designs by enforcing
   temporal, meteorological, and spatial controls jointly.
2. A new index family — **LUTHI** with typical/extreme stratification,
   multi-scale neighbourhood variants, and derived **HSI** (heat-stress
   sensitivity) and **SSI** (scale sensitivity) — accompanied by formal
   inference (bootstrap CI + placebo test).
3. Path-level SHAP attribution that reveals which baseline conditions
   modulate the heat impact of each individual transition pathway.
4. A planning-ready Heat Improvement Priority Index (**HIPI**) tying the
   attribution to actionable mitigation siting.
5. An open-source Python implementation and a transferability check on a
   second compact city, supporting generalisation beyond the case study.

---

## 5. Introduction — argument map

**Paragraph 1 — hook.** Compact cities are increasingly exposed to
summer heat extremes; mid-sized regional capitals in Japan (in the
コンパクトシティ policy frame) provide a controlled testbed for
understanding how decadal LULC redistribution shapes surface heat.

**Paragraph 2 — what the literature has done well.** Landsat-based
surface temperature (LST), correlational LULC×LST analysis, and recent
ML+SHAP studies have converged on a robust descriptive picture of urban
heat islands and their relation to imperviousness and vegetation.

**Paragraph 3 — what the literature still under-resolves.** Four gaps:
(i) heat attribution is dominated by *state* contrasts, not *process*
trajectories; (ii) inter-annual meteorological variability is usually
treated by date selection alone, not by explicit normalisation; (iii)
spatial confounding between transition pixels and the rest of the
landscape is rarely controlled with matching designs; (iv) ML
explanations are reported globally, obscuring path-specific modulation.

**Paragraph 4 — what we do.** Introduce LUTHEA / LUTHI / HIPI in two
sentences each.

**Paragraph 5 — why Yamaguchi.** Compact basin morphology; stable but
not stagnant LULC dynamics; well-documented meteorology (JMA 81428);
policy relevance to 立地適正化計画. Limited prior international
visibility makes the case substantively novel.

**Paragraph 6 — contributions (Section 4 list).**

---

## 6. Methods (full draft — drop straight into manuscript Sec 3)

### 6.1 Framework overview

LUTHEA is a five-layer pipeline (Fig. 2). Let
- $p$ index 30 m grid cells inside the AOI $\Omega$;
- $t_0 = 2016$, $t_1 = 2025$;
- $k, j$ index Dynamic World class labels with $k = j$ denoting "stable".

**Layer 1 — Trajectory identification.** Each $p$ is assigned a transition
code $(k_p^{t_0}, k_p^{t_1})$ from sub-pixel-aggregated Dynamic World
class shares (Eq. 1–2). **Layer 2 — Weather-normalised LST construction.**
Each surviving Landsat scene is projected onto a reference meteorological
state, producing $\widetilde{\text{LST}}_{p,d}$ (Eq. 3–4); annual
typical-day and extreme-day medians yield the WNSC fields (Eq. 5).
**Layer 3 — Spatial confounder conditioning.** For every transition pixel
we draw matched neighbours from the Stable Reference Set under
Mahalanobis distance over baseline covariates (Eq. 6–7) and verify
balance via standardised mean differences. **Layer 4 — Attribution.** The
LUTHI estimator (Eq. 8–11) and its derived indices HSI (Eq. 12) and SSI
(Eq. 13) are computed at pixel and path level, with bootstrap percentile
CIs and a placebo test (Section 6.7). **Layer 5 — Application.** A Heat
Improvement Priority Index ranks 30 m cells by their marginal mitigation
potential (Eq. 14).

### 6.2 Trajectory identification

Dynamic World V1 yearly mode composites at 10 m are reduced to 30 m by
$3 \times 3$ block aggregation. Let $C$ be the set of classes; for each
30 m cell $p$ and class $k \in C$,

$$
\text{PLAND}_{k,p}^{(y)} = \frac{1}{9} \sum_{p' \in B_3(p)}
\mathbb{1}\bigl[\text{DW}_{p'}^{(y)} = k\bigr], \quad y \in \{t_0, t_1\}. \tag{1}
$$

The dominant class is $\kappa_p^{(y)} = \arg\max_k \text{PLAND}_{k,p}^{(y)}$.
We retain a cell only when

$$
\text{PLAND}_{\kappa_p^{(y)}, p}^{(y)} \geq 4/9 \quad \text{at both } y. \tag{2}
$$

This dominant-share threshold (≈ 0.44) suppresses mixed pixels whose
dominant label is statistically fragile. The transition code of $p$ is the
ordered pair $(\kappa_p^{t_0}, \kappa_p^{t_1})$.

### 6.3 Weather-normalised LST

Landsat 8/9 Collection 2 Level-2 ST scenes are converted to °C using

$$
\text{LST}_{p,d} = 0.00341802 \cdot \text{ST\_B10}_{p,d} + 149.0 - 273.15, \tag{3}
$$

after masking via QA_PIXEL (cloud, cloud shadow, cirrus, dilated cloud).
Let $\mathbf{X}_d = (T_{\text{air}}, \text{RH}, \text{wind},
\text{sun}_{48h})_d$ be the AMeDAS-derived overpass-time meteorological
vector for date $d$. We pool all qualifying summer scenes 2016–2025 and
fit a single ordinary least-squares model,

$$
\text{LST}_{p,d} = \alpha_p + \boldsymbol\beta^\top \mathbf{X}_d + \varepsilon_{p,d}, \tag{4}
$$

where $\boldsymbol\beta$ is shared across the AOI to avoid over-fitting
per-pixel slopes. Let $\bar{\mathbf{X}}$ be the typical-day mean of
$\mathbf{X}_d$. The weather-normalised LST is

$$
\widetilde{\text{LST}}_{p,d} = \text{LST}_{p,d}
- \hat{\boldsymbol\beta}^\top (\mathbf{X}_d - \bar{\mathbf{X}}). \tag{5}
$$

We aggregate per year by the within-scenario pixel-wise median:

$$
\text{WNSC}_{p}^{(y, s)} =
\operatorname{median}\bigl\{ \widetilde{\text{LST}}_{p,d} :
d \in \mathcal{D}_s(y) \bigr\}, \quad s \in \{\text{typ}, \text{ext}\}. \tag{5'}
$$

Cells with fewer than two valid scenes in a (year, scenario) pair are set
to NaN.

### 6.4 Stable Reference Set and matching

The Stable Reference Set (SRS) for class $k$ is

$$
\mathcal{S}_k = \bigl\{ p : \kappa_p^{t_0} = \kappa_p^{t_1} = k,
\ \text{PLAND}_{k,p}^{(t_0)}, \text{PLAND}_{k,p}^{(t_1)} \geq 4/9 \bigr\}. \tag{6}
$$

For each treated pixel $p^* \in T_{k\to j} = \{p : (\kappa_p^{t_0},
\kappa_p^{t_1}) = (k, j), k \ne j\}$, we collect a $k$-nearest neighbour
matched set $M(p^*) \subset \mathcal{S}_k$ via

$$
M(p^*) = \arg\min_{Q \subset \mathcal{S}_k,\ |Q| = K}
\sum_{q \in Q} \sqrt{(\mathbf{z}_{p^*} - \mathbf{z}_q)^\top
\Sigma^{-1} (\mathbf{z}_{p^*} - \mathbf{z}_q)}, \tag{7}
$$

where $\mathbf{z}_p$ stacks baseline biophysical covariates
(NDVI$_{t_0}$, NDBI$_{t_0}$, NDWI$_{t_0}$, albedo$_{t_0}$, DEM, slope,
distance-to-water, distance-to-road, distance-to-green) and multi-scale
neighbourhood class shares (PLAND_Built$_{100m}$, PLAND_Green$_{100m}$,
…, PLAND_Built$_{500m}$, PLAND_Green$_{500m}$). $\Sigma$ is the pooled
covariance estimated on $T_{k\to j} \cup \mathcal{S}_k$. We use $K = 5$.
Balance is reported via per-covariate standardised mean differences
between treated and matched pools; we require $|\mathrm{SMD}| < 0.1$
post-matching (Loehlin convention), tightening covariates or shrinking
the caliper if not met.

### 6.5 LUTHI index family

Define pixel-level temporal differences

$$
\Delta_{p}^{(s)} =
\text{WNSC}_{p}^{(t_1, s)} - \text{WNSC}_{p}^{(t_0, s)}. \tag{8}
$$

For a treated pixel $p^* \in T_{k\to j}$ under scenario $s$,

$$
\text{LUTHI}_{p^*}^{(s)} = \Delta_{p^*}^{(s)}
- \frac{1}{|M(p^*)|} \sum_{q \in M(p^*)} \Delta_{q}^{(s)}. \tag{9}
$$

Path-level estimates use effective-area weights $w_{p^*}$ (the
dominant-class sub-pixel share at $t_1$):

$$
\text{LUTHI}^{k \to j}_{(s)} =
\frac{\sum_{p^* \in T_{k\to j}} w_{p^*} \cdot \text{LUTHI}_{p^*}^{(s)}}
{\sum_{p^* \in T_{k\to j}} w_{p^*}}. \tag{10}
$$

The multi-scale variant repeats Eq. 7–10 under three neighbourhood radii
$r \in \mathcal{R} = \{100, 300, 500\}$ m:

$$
\text{LUTHI}^{k \to j}_{(s)}(r), \quad r \in \mathcal{R}. \tag{11}
$$

Two derived indices:

$$
\text{HSI}^{k \to j}(r) =
\text{LUTHI}^{k \to j}_{(\text{ext})}(r) - \text{LUTHI}^{k \to j}_{(\text{typ})}(r). \tag{12}
$$

$$
\text{SSI}^{k \to j}_{(s)} \big|_{r^*} =
\frac{\text{LUTHI}^{k \to j}_{(s)}(r^+) - \text{LUTHI}^{k \to j}_{(s)}(r^-)}
{r^+ - r^-}, \tag{13}
$$

where $r^\pm$ are the neighbours of $r^*$ in $\mathcal{R}$.

### 6.6 Heat Improvement Priority Index (HIPI)

Let $z(\cdot)$ denote AOI-wide standardisation. For each currently
built-up cell $p$,

$$
\text{HIPI}_p = w_1 \, z(\text{WNSC}_p^{(t_1,\text{typ})})
            + w_2 \, z(-\text{PLAND}_{\text{Green},p}^{(300m)})
            + w_3 \, z(\text{HSI}_{p}^{\text{local}})
            + w_4 \, z(\rho_{\text{walk}, p}). \tag{14}
$$

Weights are taken from the loadings of the first principal component of
the four standardised inputs (data-driven default); a sensitivity table
reports HIPI under alternative weight schemes. Cells are ranked into
quartiles and the top quartile defines the heat improvement priority
zone.

### 6.7 Uncertainty quantification

Inference for path-level LUTHI uses a non-parametric bootstrap. Let
$B = 1000$; in each replicate $b$ we resample treated pixels with
replacement within each path and recompute Eq. 10, yielding empirical
quantiles for the percentile $1 - \alpha$ CI:

$$
[\text{LUTHI}^{k \to j}_{(s)}]_{1-\alpha} =
\bigl[ Q_{\alpha/2}(\hat\theta^*_b), \ Q_{1-\alpha/2}(\hat\theta^*_b) \bigr]. \tag{15}
$$

A within-class **placebo test** validates the quasi-causal interpretation:
for each class $k$ we randomly split $\mathcal{S}_k$ into a pseudo-treated
half and a pseudo-control half, run Eq. 7–9, and accumulate a null
distribution of $|\text{LUTHI}^{\text{placebo}}|$. The placebo $p$-value
for a real path is

$$
p^{\text{plc}}_{k \to j, s} =
\Pr_{\text{splits}}\bigl(|\text{LUTHI}^{\text{placebo}, (s)}_{k}|
\geq |\text{LUTHI}^{k \to j}_{(s)}| \bigr). \tag{16}
$$

We treat $p^{\text{plc}} > 0.05$ as a passing diagnostic; failures
indicate residual confounding and trigger re-specification (additional
covariates, tighter caliper, or stratification).

### 6.8 Path-level SHAP attribution

A gradient-boosted regressor $\hat{f}(\mathbf{x}) \approx
\text{LUTHI}_{p^*}^{(s)}$ is trained with features $\mathbf{x}$ stacking
a transition-code one-hot, $\mathbf{z}_{p^*}$ from Eq. 7, and
neighbourhood class shares at $\mathcal{R}$. We use 5-fold *spatial*
cross-validation (K-means folds on $(x_p, y_p)$ coordinates) to avoid
spatial-autocorrelation leakage. Global and path-stratified SHAP values
are reported. Optional GeoShapley (when compute permits) maps spatial
interaction effects.

---

## 7. Expected Results — structure

Each subsection is pre-committed to a figure/table.

**7.1 LULC dynamics (Fig. 3, Table 3).** Net land transitions and
sub-pixel dominance shifts. Hypothesised: Built-up +X %, Agriculture
−Y %, Bare −Z %; minor flows between Green and Crops.

**7.2 Weather-normalised LST (Fig. 4, SI Fig. S1 β̂ coefficients).** Raw
ΔLST 2016→2025 vs ΔWNSC. Hypothesised: raw +0.8–1.5 °C, normalised
+0.3–0.7 °C, demonstrating substantial meteorological inflation.

**7.3 LUTHI per path (Fig. 5, Table 4).** Bar chart with bootstrap 95 %
CIs and placebo $p$ for both typical and extreme scenarios.
Hypothesised:
- Green→Built-up: +1.0 to +2.0 °C (typ), +1.5 to +3.0 °C (ext);
- Bare→Built-up: similar or slightly larger in ext;
- Built-up→Green: −0.5 to −1.5 °C (typ), asymmetrically attenuated in ext;
- Built-up→Built-up: ~0 °C (sanity check).

**7.4 Multi-scale LUTHI and SSI (Fig. 6, Table 5).** LUTHI(r) curves;
identify r* where SSI peaks (hypothesis: r* = 300 m).

**7.5 Path-stratified SHAP (Fig. 7).** Show that initial PLAND_Green and
distance-to-water modulate Green→Built-up impact strongly but barely
affect Built-up→Built-up.

**7.6 HIPI map (Fig. 8).** Top-quartile cells overlaid on the
山口駅 ↔ 湯田温泉 pedestrian axis. Discuss which segments of the
中央商店街 receive highest priority and why.

**7.7 Transferability (SI table + 1 SI figure).** Replicate Section 7.3
on the second case city. Report Spearman rank correlation of path-level
LUTHI rankings across the two cities.

---

## 8. Discussion — talking points

1. **Why state-based analysis under-resolves the heat signal.** Compare
   our LUTHI estimates against a naïve "mean LST by dominant class"
   contrast on the same pixels; quantify the bias.
2. **Asymmetry of warming and cooling transitions under extreme heat.**
   Mechanistic discussion: latent heat decoupling, low soil moisture
   regimes, surface roughness changes.
3. **Why 300 m is the diagnostic neighbourhood scale.** Boundary-layer
   blending arguments; consistency with prior LCZ work.
4. **Compactness vs intensification.** Implication for コンパクトシティ
   policy: net compaction with greenway protection vs unconstrained infill.
5. **Generalisability.** What part of the framework is city-specific
   (AOI, JMA station id, compactness) vs city-neutral (Eqs. 1–16)?
6. **Comparison to thermal sharpening / DTM-based downscaling.** Note
   that our 30 m grid avoids sharpening artefacts entirely by aligning
   to native Landsat ST.

---

## 9. Limitations

1. Two-period transition framing (2016 ↔ 2025) — we mitigate via the
   stability check that uses 10-year trajectories internally, but the
   reported LUTHI is endpoint-anchored.
2. Dynamic World class confusion in mixed pixels — partly addressed by
   the dominant-PLAND threshold and cross-validation against ESA
   WorldCover 2020/2021.
3. β̂ assumes a globally shared meteorological response; spatial
   heterogeneity in this slope (e.g. impervious cores vs vegetated
   pockets) is not modelled. Future work can adopt a hierarchical
   spatially varying coefficient model.
4. Placebo test relies on random within-class splits; correlated spatial
   structure may inflate within-class variance, biasing the test toward
   accepting larger LUTHI as significant. We report block-cluster
   placebos in the SI as a robustness check.
5. ECOSTRESS is used only as an auxiliary diurnal cross-check, not in
   the LUTHI computation, due to irregular revisits and coarser
   ground sampling.

---

## 10. Conclusion (one-paragraph anchor for the manuscript)

> Treating LULC change as a process rather than a state, and conditioning
> the attribution on overpass-time meteorology and pre-existing
> biophysical context, materially sharpens the inferred contribution of
> individual urban transitions to summer surface heat. In Yamaguchi's
> central district, [N] of [M] identified transition pathways pass our
> placebo and bootstrap tests; the largest single contribution comes
> from [path] under extreme summer conditions, and the largest mitigation
> potential is identified along the central pedestrian axis. The LUTHEA
> framework, its LUTHI / HSI / SSI / HIPI index family, and the
> accompanying open-source implementation are directly applicable to
> any city with concurrent Dynamic World and Landsat coverage.

---

## 11. Figure and table captions (drop-in)

- **Fig. 1.** Study area: Yamaguchi central district. (a) Location within
  Yamaguchi Prefecture; (b) AOI polygon over OSM basemap with key
  landmarks (Yamaguchi Station, Yuda Onsen, central shopping street,
  prefectural office); (c) DEM and JMA station 81428.
- **Fig. 2.** LUTHEA five-layer framework flowchart.
- **Fig. 3.** (a) Dominant LULC class at t₀ and t₁; (b) Sankey diagram of
  pixel-count flow between classes; (c) net area change per class.
- **Fig. 4.** (a) Raw ΔLST 2016→2025; (b) ΔWNSC under triple control;
  (c) per-pixel difference between (a) and (b), highlighting the
  meteorological inflation removed.
- **Fig. 5.** Path-level LUTHI bars with bootstrap 95 % CIs and placebo
  *p*-values; typical (blue) and extreme (red) scenarios side by side.
- **Fig. 6.** Multi-scale LUTHI(r) curves for the top 6 paths; r* and
  SSI overlay.
- **Fig. 7.** (a) Global SHAP beeswarm; (b) path-stratified SHAP heat-map.
- **Fig. 8.** HIPI top-quartile cells over the pedestrian axis; inset
  showing one priority corridor at street level.

| Table | Content |
|---|---|
| 1 | Data sources: product, native resolution, temporal coverage, role |
| 2 | Day-selection thresholds and final dates (typical + extreme) |
| 3 | Transition paths: area, pixel count, validity rate |
| 4 | Path LUTHI (typ / ext / HSI) with bootstrap CI and placebo *p* |
| 5 | Multi-scale LUTHI(r) and SSI |

---

## 12. Reference search brief

Because specific citations must be verified rather than fabricated,
the following list points to **themes** to search for in Web of Science /
Scopus, ranked by priority. The first search per theme should yield
2–6 anchor papers that survive the gap analysis in Section 5.

| Theme | Search terms |
|---|---|
| Landsat C2 L2 ST validation | "Landsat Collection 2" "surface temperature" "validation" "single-channel" |
| Surface urban heat island (SUHI) reviews | "surface urban heat island" "review" Voogt Oke |
| Dynamic World benchmarking | "Dynamic World" "land cover" 2022 OR 2023 OR 2024 |
| LULC × LST in Asian cities | "land use" "land surface temperature" "urban" Japan OR Korea OR China |
| Transition matrix × UHI | "land cover change" "transition" "surface temperature" |
| Difference-in-differences in remote sensing | "difference-in-differences" "remote sensing" |
| Causal inference / propensity matching for environmental remote sensing | "propensity score" "remote sensing" "land cover" |
| ML + SHAP for UHI driver attribution | "SHAP" "land surface temperature" |
| GeoShapley | "GeoShapley" 2023 OR 2024 |
| Landscape metrics × LST at multiple buffers | "landscape metrics" "buffer" "LST" |
| Compact city / コンパクトシティ urban climate | "compact city" "urban climate" Japan |
| Yamaguchi or Yamaguchi-like mid-sized Japanese cities | "Yamaguchi" OR "Tottori" OR "Matsue" "urban heat" |
| ECOSTRESS urban applications | "ECOSTRESS" "urban" "heat" |
| Heat extremes and urban morphology in Japan | "heatwave" "urban" Japan "JMA" |

Recommended anchor count: 60–80 references in the final manuscript;
20 of these should be in the last three years to demonstrate currency.

---

## 13. Submission strategy

1. **First submission**: *Remote Sensing* (MDPI). Cover letter
   emphasises (a) methodological generality, (b) open-source release,
   (c) replication on a second city.
2. If desk-rejected or returned for major revision focused on case-
   specificity, redirect to *Urban Climate*, restructuring the
   manuscript with stronger Discussion of policy implications and
   trimming Methods detail to an appendix.
3. *GIScience & Remote Sensing* and *IJAEOG* are backup methods-friendly
   outlets.
4. Pre-print the manuscript on EarthArXiv on first submission; freeze
   the code repository and mint a Zenodo DOI before submission.

---

## 14. Outstanding items before drafting begins

| Item | Owner | Blocker |
|---|---|---|
| Hand-draw AOI polygon `aoi/yamaguchi_center.geojson` | user | — |
| JMA station 81428 daily + AMeDAS 10-min CSV download (2016–2025) | user | manual UI |
| Confirm Landsat path/row covering Yamaguchi (suspected 112/035) | user | check GEE scene list |
| Select second case city for transferability (米子 vs 松江) | user | preference |
| Implement GEE ingestion (`data_ingest/dynamic_world.py`, `landsat_st.py`) | assistant | next code commit |
| Implement ML / SHAP and HIPI (`ml/`, `viz/figures.fig8_hipi`) | assistant | next code commit |
| First end-to-end pipeline run on small AOI | both | after the four items above |

When all rows above are closed, manuscript writing begins with
Methods (Section 6), then Results (Section 7), then Discussion / Limits
/ Conclusion, then Introduction (last), then Abstract (last).
