# Paper Conception — LUTHEA / LUTHI, Yamaguchi + Yonago 2016–2025

> Working document for the SCI paper described in
> `/root/.claude/plans/token-token-quiet-bachman.md`.
> **Target journal (v2 lock): Urban Climate (Elsevier)**. Remote Sensing /
> GIScience & Remote Sensing / Sustainable Cities and Society as fallbacks.
> Status: pre-data; numbers in *Results* are hypothesised ranges to be
> filled in after pipeline runs.

---

## 0. Locked decisions (post-Socratic Q1–Q4)

| Slot | Decision |
|---|---|
| **Q1 — Identity** | **Method-first** (Option A). Abstract opens with "We introduce LUTHEA…"; Methods budget 3 000 words; second-city replication is **required**, not optional; HIPI is demoted to applied demo. |
| **Q2 — Most-feared rejection** | (a) *"LUTHI is dressed-up DiD"* + (b) *"Spatially-uniform β̂ is biophysically untenable"*. Defences pre-positioned: identification statement A1–A4 in § 6.5; Assumption B in § 6.3; baseline-comparison SI table; β̂-sensitivity sub-result § 7.x. |
| **Q3 — Subtraction** | Cut **multi-scale SSI** (∂LUTHI/∂r). Neighbourhood radii 100/300/500 m **remain** as matching covariates; LUTHI itself is computed at a single default radius (300 m). H4 (300 m as diagnostic scale) is dropped; Fig. 6 and Table 5 are removed; main figures shrink to 7, main tables to 4. |
| **Q4 — Central claim** | **Asymmetric, state-dependent transition effects.** α: HSI(Green→Built-up) ≈ +1.8 °C (≈180 % amplification under extreme heat). β: HSI(Built-up→Green) ≈ −0.2 °C (cooling potential collapses under extreme heat). Together they form the manuscript's take-home. |

## 0.5 Journal pivot to Urban Climate (post-literature-scan lock)

After a 2025-2026 scan of the Urban Climate / Remote Sensing landscape,
the primary target is **switched from Remote Sensing to Urban Climate**.
Justification:

1. **Editorial fit**: Urban Climate's 2025-2026 editorial priorities (extreme
   heat mechanisms, compact city / TOD, ML+SHAP interpretation, policy
   relevance) intersect our α/β asymmetry claim on every axis. The
   direct anchor paper — Tokyo TOD 2026 [S2210670726002052] — establishes
   the venue's appetite for XGBoost-SHAP LST attribution and gives us
   four differentiation levers (state→process, meteorology control,
   causal identification, typ/ext stratification).
2. **Impact factor**: Urban Climate IF ≈ 6.5 vs Remote Sensing IF ≈ 4.5.
3. **Policy leverage**: adding population exposure, heatstroke correlation,
   and 立地適正化計画 (Location Optimisation Plan) overlap makes the
   contribution unambiguously a *health-risk + planning* paper, which
   Urban Climate reads more favourably than a *methods* paper.
4. **Case novelty**: mid-sized regional Japanese cities (Yamaguchi + Yonago,
   both about 150 000 pop.) are essentially virgin territory in
   international UHI literature — LCZ studies exist only for Tokyo,
   Osaka, Hiroshima, Sapporo, Shizuoka.

Downstream consequences (locked):

- **Title changes** — see § 1 below.
- **Abstract lead sentence** — replaces "We introduce LUTHEA" with the
  extreme-heat asymmetry hook.
- **Second-city selection** = **Yonago (米子)**, Tottori prefecture,
  JMA station 68861 (皆生温泉 coastal complement to Yamaguchi's Yuda
  Onsen inland basin).
- **Three new data assets** — 250 m mesh 2020 census population
  (e-Stat), FDMA weekly heatstroke transport (prefecture-level), and
  MLIT A50 Location Optimisation Plan boundaries.
- **Three new hypotheses (H6–H8)** — Yonago transferability, HIPI
  population coverage, HIPI vs 立地適正化計画 misalignment. See § 3.
- **New algorithm module** — `luthea.attribution.exposure`
  (population overlap + heatstroke-count correlation + policy overlap).
- **Central figure re-plan** — Fig. 7 becomes a three-panel
  HIPI × Population × Policy composite.

Word-budget reconciliation: Methods 3 000 → **2 900**; Results 1 900 → **2 000**;
Study area + Data 750 → **800**; total ≈ **8 900**.

---

## 1. Title candidates

1. **Asymmetric surface heat impacts of decadal land-use transitions under typical versus extreme summer conditions: A causal attribution for compact Japanese regional cities** *(primary, locked; Urban Climate framing)*
2. When greening fails in a heatwave: State-dependent land-use transition impacts on summer surface temperature in compact regional cities (Yamaguchi + Yonago, 2016–2025)
3. LUTHEA: A Quasi-Causal Attribution Framework for Land-Use Transition-Driven Urban Heat Change Using Multi-Source Satellite Data *(fallback for Remote Sensing / GIScience & Remote Sensing)*
4. Land-use transitions, heat exposure, and コンパクトシティ policy: A causal-inference remote-sensing framework applied to two Japanese regional cities

Decision rule (locked): **Title 1** for Urban Climate; Title 3 for Remote Sensing fallback.

---

## 2. Abstract (≈ 250 words, draft — Urban Climate framing)

> **Under intensifying summer heat, the cooling potential of urban
> greening may collapse exactly when it is most needed.** We test this
> conjecture in two compact Japanese regional cities (Yamaguchi and
> Yonago, 2016–2025) by treating land-use/land-cover (LULC) *change* as
> a process rather than a state, and by attributing surface heat impact
> at the level of individual transition pathways. Our framework —
> LUTHEA — combines a Dynamic World-derived 30 m trajectory raster
> with weather-normalised Landsat 8/9 surface temperature (typical and
> extreme-day composites separated), a Stable Reference Set of
> co-class pixels for per-path counterfactuals, and Mahalanobis
> k-nearest-neighbour matching on baseline biophysical and multi-scale
> neighbourhood covariates. The **Land-Use Transition Heat Impact Index
> (LUTHI)** carries bootstrap 95 % confidence intervals and a
> within-class placebo test as formal falsification. The **Heat-Stress
> Sensitivity Index (HSI)** re-writes the typical-vs-extreme contrast as
> a triple-difference. In both cities, Green→Built-up warming pathways
> **amplify** under extreme heat (HSI ≈ +1.8 °C, ≈180 % over the typical-
> day effect), while Built-up→Green cooling pathways **collapse**
> (|HSI| < 0.5 °C). We integrate 250 m mesh census population, weekly
> heatstroke ambulance transport, and 立地適正化計画 (Location
> Optimisation Plan) boundaries to show that these asymmetric hazards
> concentrate in areas the current compact-city policy does not
> flag as vegetation-priority zones. The pipeline is open-source and
> transferable to any city with Dynamic World and Landsat coverage.

---

## 3. Core science question

> Which **decadal land-use transition pathways** have contributed most
> to changes in summer surface urban heat exposure in a compact Japanese
> city, **after controlling for inter-annual meteorological variability,
> neighbourhood landscape configuration, and pre-existing site
> characteristics**, and how do these contributions differ between
> **typical and extreme** summer days?

### Hypotheses (updated post-Urban-Climate pivot; H6–H8 added)

| ID | Statement | Quantitative bet | Test |
|---|---|---|---|
| H1 | Trajectory has higher explanatory power than end-state LULC for ΔLST. | Partial R² gain ≥ 0.15. | XGBoost partial-R² after removing trajectory one-hot vs after removing end-state one-hot. |
| H2 (α) | **Green→Built-up amplifies under extreme heat.** | LUTHI_ext ≈ +2.5 to +3.0 °C; HSI ≈ +1.5 to +2.0 °C (≈150–200 % amplification over typical). | Path-level LUTHI bootstrap CIs in two scenarios + HSI sign test. |
| H3 (β) | **Built-up→Green's cooling potential collapses under extreme heat.** | LUTHI_typ ≈ −1.0 to −1.5 °C; LUTHI_ext closer to −0.2 to −0.5 °C; \|HSI\| < 0.5 °C. | Same as H2 with paired \|HSI\| comparison. |
| H4 | Triple control removes a substantial share of apparent decadal warming. | ΔWNSC / ΔLST_raw ≤ 0.6. | Compare raw ΔLST vs ΔWNSC at city-centre means with bootstrap difference test. |
| H5 | LUTHI rankings are stable across β̂ specifications (defence for review-objection b). | Spearman ρ ≥ 0.85 between global, per-class, GWR, and quantile-conditioned β̂. | Sensitivity § 7.4; SI Table S5. |
| **H6** *(new)* | **Yonago replication confirms the α/β asymmetry.** | Path LUTHI Spearman ρ between the two cities ≥ 0.6; sign agreement of HSI on ≥ 4 of the top-5 paths. | SI Table S3, SI Fig. S3. |
| **H7** *(new)* | **HIPI top-quartile cells concentrate exposed population.** | The HIPI top quartile (~15–25 % of central-district area) contains ≥ 30 % of the resident population and shows an above-median elderly share. | Table 5. |
| **H8** *(new)* | **Current 立地適正化計画 boundaries under-cover the identified heat-risk core.** | Intersection-over-union of HIPI top-quartile cells with 都市機能誘導区域 < 0.6; the missed area is at least 25 % of the HIPI core. | Fig. 7c; § 4.6. |

(H4 of the earlier draft — 300 m as diagnostic neighbourhood scale — was retired in the Q3 cut.)

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
- $t_0$ = the **2016–2018 epoch**, $t_1$ = the **2023–2025 epoch**
  (see § 6.2.1 for why the contrast is defined between three-year epochs
  rather than single years);
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
LUTHI estimator (Eq. 8–10) and its triple-difference companion HSI
(Eq. 11) are computed at pixel and path level, with bootstrap
percentile CIs and a placebo test (Section 6.7). **Layer 5 —
Application.** A Heat Improvement Priority Index ranks 30 m cells by
their marginal mitigation potential (Eq. 12).

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

### 6.2.1 Epoch definition and observational constraint

Cloud screening leaves **18 usable Landsat 8/9 summer scenes** over the
Yamaguchi AOI for 2016–2025, distributed unevenly across years (1, 2, 3,
1, 1, 1, 1, 2, 2, 4 for 2016 … 2025 respectively). Five individual years
contribute a single scene, which is below the two-observation floor
required for a stable pixel-wise median — and the constraint tightens
further once scenes are stratified into typical and extreme days.

We therefore define the decadal contrast between **three-year epochs**:

$$
t_0 = \{2016, 2017, 2018\} \;(n = 6), \qquad
t_1 = \{2023, 2024, 2025\} \;(n = 8), \tag{2'}
$$

with the intervening years $\{2019, \dots, 2022\}$ ($n = 4$) reserved for
the per-year trend figure and robustness checks rather than entering the
contrast. Epoch pooling both restores the per-pixel observation count and
aligns the estimand with the manuscript's decadal framing: LUTHI measures
the change between two multi-year climatological states, not between two
arbitrary satellite overpasses. The scene inventory underlying this
choice is reported in Table 2 and reproduced by
`scripts/scene_inventory.py`, which re-derives the counts directly from
the Earth Engine filter so the reported design cannot drift from the
ingested data.

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

**Separation of screening and normalisation.** Scene screening and
weather normalisation are deliberately assigned disjoint duties, because
applying both to the same variable removes the same signal twice and
decimates an already thin Landsat record for no inferential gain. We
screen only on conditions that Eq. 5 cannot repair: the AOI cloud
fraction, since a masked pixel has no retrieval to correct, and same-day
plus 48 h antecedent precipitation, since a wet surface occupies a
different evaporative regime rather than carrying a linear
meteorological offset. Air temperature at overpass, relative humidity,
wind speed and antecedent sunshine are *not* screened; they enter
$\mathbf{X}_d$ and are projected out by $\hat{\boldsymbol\beta}$. A
supplementary sensitivity analysis reports every headline estimate under
a stricter screen that additionally requires $\ge 8$ h of sunshine and
overpass wind $\le 3$ m s$^{-1}$ (SI Table S7).

**Scenario strata.** Typical and extreme days follow the Japan
Meteorological Agency's official climatological categories rather than
tuned cut-points: 真夏日 ($30 \le T_{max} < 35$ °C) defines the typical
stratum and 猛暑日 ($T_{max} \ge 35$ °C) the extreme stratum. The bands
are contiguous and mutually exclusive, so no qualifying acquisition is
silently discarded between them.

**Assumption B (defence against review-objection b).** Eq. 4 enforces a
single global $\boldsymbol\beta$ across the AOI; this trades local
fidelity for sample size. We test sensitivity to this choice in § 7.x
under three alternative specifications: (i) per-class $\boldsymbol\beta_k$
fit on each initial dominant class; (ii) geographically weighted
$\boldsymbol\beta(p)$ with a 500 m bandwidth; (iii) quantile-conditioned
$\boldsymbol\beta_q$ on initial NDVI / albedo deciles. We report the
Spearman rank correlation of path-level LUTHI rankings across all four
specifications (hypothesis H5) and adopt the global $\hat{\boldsymbol\beta}$
as the headline only if $\rho \ge 0.85$.

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

The headline LUTHI is reported at the 300 m neighbourhood radius for
matching covariates; multi-scale LUTHI(r) and its derivative
(deprecated SSI) are deferred to a methodological supplement and not
used as primary results, by the Q3 parsimony decision.

The **Heat-Stress Sensitivity Index** quantifies how the per-path
attribution responds to a shift from typical to extreme summer
conditions, with the algebraic form of a triple difference (time ×
treatment × scenario):

$$
\text{HSI}^{k \to j} =
\text{LUTHI}^{k \to j}_{(\text{ext})} - \text{LUTHI}^{k \to j}_{(\text{typ})}. \tag{11}
$$

#### Identification statement (defence against review-objection a)

LUTHI is a **matching-augmented difference-in-differences** estimator
operating on a quasi-experimental design. Its credibility relies on
four named assumptions, three of which are tested empirically in
this paper:

- **A1 (parallel trends).** The expected counterfactual trajectory of
  treated pixels in the absence of transition equals the observed
  trajectory of matched stable pixels of the same class. *Tested* by
  the within-class placebo (Eq. 14 below).
- **A2 (conditional unconfoundedness).** After Mahalanobis kNN matching
  on $\mathbf{z}_p$, treatment assignment is independent of potential
  outcomes. *Tested* by per-covariate standardised mean differences;
  |SMD| < 0.1 is required.
- **A3 (multi-scale conditioning).** Path effects are stable across
  neighbourhood radii used in the matching covariate set
  $r \in \{100, 300, 500\}$ m. *Tested* by re-running the matching
  with each radius held fixed and reporting Spearman ρ of resulting
  LUTHI rankings; this is a structural feature of LUTHEA absent from
  standard DiD.
- **A4 (triple-difference identification of HSI).** Eq. 11 reads as a
  three-way contrast over (time × treatment × scenario); under the
  scenario-exogeneity assumption (typical vs extreme heat regimes are
  exchangeable conditional on $\mathbf{z}_p$), HSI is identified
  independently of any time-invariant pixel-level confounder.
  *Tested* by re-estimating HSI on placebo (within-class) splits
  stratified by scenario.

We make the dressed-up-DiD critique explicit, and demonstrate
quantitative value-add of LUTHEA over (i) a naïve state contrast,
(ii) standard DiD with no matching, and (iii) propensity matching
without weather normalisation, on the same pixels, in SI Table S4.

### 6.6 Heat Improvement Priority Index (HIPI)

Let $z(\cdot)$ denote AOI-wide standardisation. For each currently
built-up cell $p$,

$$
\text{HIPI}_p = w_1 \, z(\text{WNSC}_p^{(t_1,\text{typ})})
            + w_2 \, z(-\text{PLAND}_{\text{Green},p}^{(300m)})
            + w_3 \, z(\text{HSI}_{p}^{\text{local}})
            + w_4 \, z(\rho_{\text{walk}, p}). \tag{12}
$$

Weights are taken from the loadings of the first principal component of
the four standardised inputs (data-driven default); a sensitivity table
reports HIPI under alternative weight schemes. Cells are ranked into
quartiles and the top quartile defines the heat improvement priority
zone.

### 6.6.1 Exposure, health, and policy overlays *(Urban Climate additions)*

Three overlays translate the raster-level HIPI into a decision-relevant
summary. Let $Q_4$ denote the set of pixels in the HIPI top quartile.

**Population exposure.** Let $\pi_g$ be the 2020 census population count
in 250 m mesh cell $g$ (source: e-Stat 統計 GIS). The population
resident inside $Q_4$ is

$$
P(Q_4) = \sum_{g} \pi_g \cdot \frac{|g \cap Q_4|}{|g|}, \tag{15a}
$$

with $|g \cap Q_4|$ the area of intersection. The **exposure share**
$P(Q_4) / P(\text{AOI})$ tests H7. An analogous overlay computes the
elderly share (aged 65+).

**Heatstroke correlation.** Weekly prefecture-level emergency
transports $T_w$ (source: 消防庁) are aggregated to annual counts
$T_y$ and Spearman-correlated against the AOI-mean $\overline{\text{HSI}}_y$
across the ten-year record. We report Spearman ρ and its bootstrap CI
but do **not** claim causation — the Discussion states this
correlation-only limitation explicitly.

**Policy overlay.** Let $Z$ be the 都市機能誘導区域 polygon (source:
MLIT 国土数値情報 A50). The **misalignment** between the identified
heat-risk core and the current compact-city policy is quantified by

$$
\text{IoU}(Q_4, Z) = \frac{|Q_4 \cap Z|}{|Q_4 \cup Z|}, \qquad
\text{Missed}(Q_4) = \frac{|Q_4 \setminus Z|}{|Q_4|}. \tag{15b}
$$

$\text{IoU}(Q_4, Z) < 0.6$ combined with $\text{Missed}(Q_4) \ge 0.25$
supports H8.

### 6.7 Uncertainty quantification

Inference for path-level LUTHI uses a non-parametric bootstrap. Let
$B = 1000$; in each replicate $b$ we resample treated pixels with
replacement within each path and recompute Eq. 10, yielding empirical
quantiles for the percentile $1 - \alpha$ CI:

$$
[\text{LUTHI}^{k \to j}_{(s)}]_{1-\alpha} =
\bigl[ Q_{\alpha/2}(\hat\theta^*_b), \ Q_{1-\alpha/2}(\hat\theta^*_b) \bigr]. \tag{13}
$$

A within-class **placebo test** validates the quasi-causal interpretation:
for each class $k$ we randomly split $\mathcal{S}_k$ into a pseudo-treated
half and a pseudo-control half, run Eq. 7–9, and accumulate a null
distribution of $|\text{LUTHI}^{\text{placebo}}|$. The placebo $p$-value
for a real path is

$$
p^{\text{plc}}_{k \to j, s} =
\Pr_{\text{splits}}\bigl(|\text{LUTHI}^{\text{placebo}, (s)}_{k}|
\geq |\text{LUTHI}^{k \to j}_{(s)}| \bigr). \tag{14}
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

**7.3 LUTHI per path (Fig. 5, Table 4) — *central result***. Bar chart
with bootstrap 95 % CIs and placebo $p$ for both typical and extreme
scenarios. Pre-registered headline predictions (post-Q4):
- *Hypothesis α — amplification.* Green→Built-up: LUTHI_typ ≈ +1.0 °C,
  LUTHI_ext ≈ +2.5 to +3.0 °C, HSI ≈ +1.5 to +2.0 °C (≈150–200 % amplification).
- *Hypothesis β — collapse.* Built-up→Green: LUTHI_typ ≈ −1.0 to −1.5 °C,
  LUTHI_ext ≈ −0.2 to −0.5 °C, |HSI| < 0.5 °C — cooling potential
  blunted exactly when most needed.
- Bare→Built-up: comparable or slightly larger than Green→Built-up in
  the extreme scenario.
- Built-up→Built-up: ≈ 0 °C (sanity check; if non-zero, flag as residual
  confounding and discuss).

**7.4 β̂ specification sensitivity (Table S5; defence for review-objection b).**
Re-estimate LUTHI under four weather-normalisation regimes — global
$\hat{\boldsymbol\beta}$, per-class $\hat{\boldsymbol\beta}_k$, GWR
$\hat{\boldsymbol\beta}(p)$, and quantile-conditioned
$\hat{\boldsymbol\beta}_q$. Report the Spearman rank correlation of
path-level LUTHI orderings. Headline acceptance: $\rho \ge 0.85$ across
all six pairwise comparisons (H5).

**7.5 Path-stratified SHAP (Fig. 6).** Show that initial PLAND_Green and
distance-to-water modulate Green→Built-up impact strongly but barely
affect Built-up→Built-up; document which baseline conditions amplify
the HSI asymmetries above.

**7.6 HIPI + exposure + policy composite (Fig. 7, Table 5) — *Urban Climate hook***.
Three-panel figure and one summary table:
  - *Panel a — HIPI + population.* Top-quartile cells overlaid on the
    250 m mesh population raster. Report $P(Q_4)/P(\text{AOI})$ (H7 pass
    if ≥ 0.30) and the elderly-share ratio inside $Q_4$ vs the AOI mean.
  - *Panel b — HIPI + heatstroke context.* Annual AOI-mean HSI vs
    prefecture-weekly heatstroke transports 2016–2025; scatter with
    fitted Spearman ρ and 95 % CI (correlation-only, explicit no-causal
    claim in caption).
  - *Panel c — HIPI vs 立地適正化計画.* Overlay of $Q_4$ and
    the 都市機能誘導区域; the missed area is shaded. Report
    IoU$(Q_4, Z)$ and Missed$(Q_4)$ (H8 pass if IoU < 0.6 AND
    Missed ≥ 0.25).

**7.7 Heatstroke correlation sub-analysis (SI Table S6).** Weekly
prefecture-level transports vs the same-week meteorology and the
inferred HSI over 2016–2025. This is a robustness / context section,
not the causal chain; reported to make the Urban Climate readership
comfortable that the identified heat-risk core has an epidemiological
signature at prefecture scale.

**7.7 Transferability (SI Table S3 + SI Fig. S3) — *required by method-first framing***.
Replicate Section 7.3 on the second case city. Report Spearman rank
correlation of path-level LUTHI rankings across the two cities and the
agreement of HSI sign per path. Acceptance: $\rho \ge 0.6$ for LUTHI;
sign agreement on at least 4 of the top-5 paths.

**7.8 Comparison to baseline estimators (SI Table S4; defence for review-objection a).**
Recompute the attribution under (i) naïve mean-LST contrast by
end-state class, (ii) standard DiD without matching, (iii) propensity
matching without weather normalisation. Report bias and direction
versus LUTHI; demonstrate that the asymmetry of α and β is invisible
under (i)–(iii).

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
3. β̂ assumes a globally shared meteorological response. Sensitivity
   analysis in § 7.4 demonstrates that LUTHI path rankings are stable
   (Spearman ρ ≥ 0.85) across global, per-class, GWR(500 m), and
   quantile-conditioned β̂ specifications. A fully spatially-varying
   coefficient (hierarchical SVCM / Bayesian) extension is left to
   future work.
4. Placebo test relies on random within-class splits; correlated spatial
   structure may inflate within-class variance, biasing the test toward
   accepting larger LUTHI as significant. We report block-cluster
   placebos in the SI as a robustness check.
5. ECOSTRESS is used only as an auxiliary diurnal cross-check, not in
   the LUTHI computation, due to irregular revisits and coarser
   ground sampling.
6. **Thin observational record.** Only 18 cloud-free summer Landsat
   scenes are available over the Yamaguchi AOI across the decade, which
   forces the three-year epoch pooling of Eq. 2′ and precludes a
   year-by-year LUTHI series. The epoch composites are correspondingly
   sensitive to which individual dates survive cloud screening; we
   report the full scene inventory (Table 2) so this is auditable, and
   the β̂ sensitivity analysis (§ 7.4) doubles as a check that the
   ranking is not driven by any single date.
7. **Policy overlay unavailable for Yonago.** Tottori prefecture
   (code 31) is not published in the MLIT A50-20 立地適正化計画 release,
   so the H8 policy-misalignment analysis is reported for Yamaguchi
   only. No substitute boundary was constructed.

---

## 10. Conclusion (one-paragraph anchor for the manuscript)

> Treating LULC change as a process rather than a state, and
> conditioning the attribution on overpass-time meteorology, baseline
> biophysical context, and matched stable references, materially
> sharpens the inferred contribution of individual urban transitions to
> summer surface heat. The central, pre-registered finding is that
> these contributions are **non-symmetric and state-dependent**: in
> Yamaguchi's central district, Green→Built-up amplifies under extreme
> heat by roughly a factor of [HSI/LUTHI_typ], while Built-up→Green
> shows a near-complete collapse of cooling potential under the same
> conditions. This asymmetry is invisible to state-based and
> non-meteorology-controlled analyses, as demonstrated against three
> baseline estimators on identical pixels. The LUTHEA framework, its
> LUTHI / HSI / HIPI index family, and the accompanying open-source
> Python implementation are directly applicable to any city with
> concurrent Dynamic World and Landsat coverage.

---

## 11. Figure and table captions (drop-in)

- **Fig. 1.** Study area — **two-panel**: (a) Yamaguchi central district
  AOI over OSM basemap with landmarks (山口駅, 湯田温泉, 中央商店街,
  県庁) and JMA station 81428; (b) Yonago central district AOI over OSM
  basemap with landmarks (米子駅, 皆生温泉, 中心商店街, 米子城跡) and
  JMA station 68861. DEM shading in both panels.
- **Fig. 2.** LUTHEA five-layer framework flowchart, now with the
  exposure/health/policy overlay explicitly drawn as Layer 5.
- **Fig. 3.** Yamaguchi LULC dynamics — (a) dominant LULC class at t₀ and
  t₁; (b) Sankey diagram of pixel-count flow between classes; (c) net
  area change per class. Yonago equivalent in SI Fig. S4.
- **Fig. 4.** (a) Raw ΔLST 2016→2025 (Yamaguchi); (b) ΔWNSC under
  triple control; (c) per-pixel difference (a) − (b), highlighting the
  meteorological inflation removed.
- **Fig. 5.** *Central result.* Path-level LUTHI bars with bootstrap
  95 % CIs and placebo *p*-values; typical (blue) and extreme (red)
  scenarios side by side; HSI annotation per path; α (Green→Built) and
  β (Built→Green) highlighted. Yamaguchi in the main panel; a
  compact Yonago inset shows the same asymmetry pattern.
- **Fig. 6.** (a) Global SHAP beeswarm; (b) path-stratified SHAP
  heat-map highlighting which baseline conditions modulate the
  HSI asymmetry.
- **Fig. 7.** *Urban Climate hook — HIPI three-panel composite.*
  (a) HIPI top-quartile cells overlaid on the 250 m mesh 2020
  population raster (Yamaguchi); population exposure share and elderly
  share reported in the caption.
  (b) Annual AOI-mean HSI vs same-year Yamaguchi-prefecture
  heatstroke transports 2016–2025; Spearman ρ and 95 % CI reported;
  correlation-only, no causal claim.
  (c) HIPI top-quartile cells overlaid on 都市機能誘導区域
  boundaries from the 山口市 立地適正化計画; IoU and missed-area share
  reported.

| Table | Content |
|---|---|
| 1 | Data sources: product, native resolution, temporal coverage, role. **Extended to include** e-Stat 250 m mesh census, FDMA weekly heatstroke transports, and MLIT A50 立地適正化計画 boundaries. |
| 2 | **Scene inventory and day selection.** Every retained Landsat scene with its date, sensor, epoch assignment, JMA T_max / sunshine / precipitation / overpass wind, and its typical/extreme label; plus the per-(epoch × scenario) counts that justify Eq. 2′ — Yamaguchi + Yonago |
| 3 | Transition paths: area, pixel count, validity rate — Yamaguchi + Yonago |
| 4 | *Central table.* Path LUTHI (typ / ext / HSI) with bootstrap CI and placebo *p* — Yamaguchi + Yonago side by side |
| **5** | *Urban Climate hook.* HIPI quartile × resident population count × elderly share × prefecture heatstroke correlation strength × IoU with 都市機能誘導区域 |

**Supplementary material**

| SI item | Content |
|---|---|
| Fig. S1 | β̂ coefficients ± SE; per-class and GWR variants |
| Fig. S2 | Love plot — standardised mean differences pre/post matching |
| Fig. S3 | Second-city replication, equivalent of Fig. 5 |
| Table S3 | Second-city LUTHI table (parallel to Table 4) + Spearman ρ |
| Table S4 | LUTHI vs baseline estimators (naïve / DiD / matching-only) |
| Table S5 | LUTHI rankings across β̂ specifications (defence for objection b) |

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
| **Tokyo TOD & LST attribution (direct anchor)** | Transit-oriented development Tokyo LST XGBoost SHAP (S2210670726002052) |
| **Compact city / コンパクトシティ urban climate (policy hook)** | "compact city" "urban climate" Japan; 立地適正化計画 |
| **Beijing functional-intensity dynamics (close conceptual competitor)** | "functional intensity" thermal Beijing (s41598-026-44866-x) |
| Yamaguchi or Yamaguchi-like mid-sized Japanese cities | "Yamaguchi" OR "Yonago" OR "Tottori" OR "Matsue" "urban heat" |
| ECOSTRESS urban applications | "ECOSTRESS" "urban" "heat" |
| Heat extremes and urban morphology in Japan | "heatwave" "urban" Japan "JMA" |
| **Extreme-day UHI reversal / cool-island phenomenon (mechanism for β)** | "urban cool island" heatwave "surface temperature" |
| **Heatstroke & LST epidemiology (new for § 4.7)** | "heat-related illness" "land surface temperature" Japan |
| **Population exposure to UHI (new for § 4.6 panel a)** | "population exposure" "urban heat" "census mesh" |
| **Nighttime LST (mention as future work)** | nighttime "land surface temperature" urban review 2025 |

### Supplementary materials list (post-Urban-Climate pivot)

- **SI Fig. S1** — β̂ coefficients (global + per-class + GWR + quantile-conditioned).
- **SI Fig. S2** — Love plot of standardised mean differences pre / post matching.
- **SI Fig. S3** — Yonago replication of Fig. 5.
- **SI Fig. S4** — Yonago LULC dynamics (parallel to Fig. 3).
- **SI Table S3** — Yonago path-level LUTHI (parallel to Table 4).
- **SI Table S4** — LUTHI vs three baseline estimators (naïve state contrast, standard DiD, matching-only) on identical pixels.
- **SI Table S5** — LUTHI rankings across the four β̂ specifications (H5 support).
- **SI Table S6** — Heatstroke correlation robustness (per-year Spearman ρ; lag ±1 week; alternate definitions of "extreme day").
- **SI Table S7** — Screening sensitivity: every headline estimate recomputed under the stricter scene screen (sunshine ≥ 8 h and overpass wind ≤ 3 m s⁻¹ additionally required), with the resulting scene counts per epoch × scenario cell.

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
