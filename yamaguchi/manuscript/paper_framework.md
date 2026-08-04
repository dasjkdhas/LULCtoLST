# Paper Framework — Skeleton Outline

> Companion to `paper_conception.md`. Where the conception document
> drafts narrative content, this file is the **structural skeleton**:
> section numbering, word budgets, per-paragraph claims, the
> figure/table evidence ledger, and the dependency graph between
> sections.
>
> Target journal: *Remote Sensing*. Target total length: ≈ 8 900 words
> (excluding references, captions, SI). Section budgets below.

---

## 0. Article identity card (post-Socratic Q1–Q4 lock)

| Field | Value |
|---|---|
| Working title | Asymmetric surface heat impacts of decadal land-use transitions under typical versus extreme summer conditions: A causal attribution for compact Japanese regional cities |
| **Journal** | **Urban Climate (Elsevier)** *— pivoted from Remote Sensing after 2025-2026 literature scan* |
| Article type | Research article |
| Reader profile | Urban-climate empiricists; policy scientists; ML + causal-inference; compact-city planners |
| One-sentence pitch (**Q1**) | "Under intensifying summer heat, urban greening's cooling potential may collapse exactly when it is most needed — we quantify this state-dependent asymmetry in compact Japanese cities and link it to population exposure and コンパクトシティ policy." |
| Most-feared rejection (**Q2**) | (a) "LUTHI is dressed-up DiD" + (b) "Spatially-uniform β̂ is biophysically untenable" — plus new (c) "correlation-only heatstroke overlay is thin" |
| Subtracted module (**Q3**) | Multi-scale SSI dropped; LUTHI computed at single 300 m default radius |
| Headline finding (**Q4**) | α: HSI(Green→Built-up) ≈ +1.8 °C (≈180 % amplification under extreme heat) + β: HSI(Built-up→Green) ≈ −0.2 °C (cooling potential collapses) — with population exposure and 立地適正化計画 misalignment as the policy payload |
| Second case city | **Yonago (米子)**, Tottori — JMA station 68861 |
| Anchor competitor to differentiate from | Tokyo TOD 2026 Urban Climate (S2210670726002052) — state-based, no meteo control, no typ/ext, no causal ID |
| Headline number to hit | Both α-prediction CI and β-prediction CI not crossing zero AND placebo p > 0.05 AND visible in Fig. 5 at a glance AND Yonago replicates (Spearman ρ ≥ 0.6) |
| Manuscript deadline (self-set) | end of Yamaguchi + Yonago pipeline + 6 weeks |

---

## 1. Logical flow (one screen)

```
Compact cities heat up under decadal LULC change.
         │
         ▼
State-based RS analyses miss the process; meteorology and confounders are not jointly controlled.
         │
         ▼  (Gap → Objectives)
Propose LUTHEA: trajectory-based, quasi-causal, weather-normalised, matched-pair attribution.
         │
         ▼  (Methods § 3.1 – 3.8)
Eq. 1–16 produce: WNSC, transitions, matched pairs, LUTHI, HSI, SSI, HIPI, CIs, placebo p.
         │
         ▼  (Results § 4.1 – 4.7)
LULC flow → WNSC change → path LUTHI ± CI → multi-scale → SHAP → HIPI → second-city replication.
         │
         ▼  (Discussion § 5)
Why state-based bias exists; why 300 m is diagnostic; what compact-city policy can do; what generalises.
         │
         ▼  (Conclusion § 7)
Trajectory + triple control + open package; transferable to any city with Dynamic World + Landsat.
```

---

## 2. IMRAD skeleton with word budgets

### Abstract (≈ 250 words)

> Already drafted in `paper_conception.md` § 2.

Structure check: 5 moves — (1) problem, (2) gap, (3) proposed framework
in one breath, (4) what we do in Yamaguchi, (5) what we release. Each
move ≈ 50 words.

### § 1 Introduction (≈ 1 100 words; 6 paragraphs)

| ¶ | ≈ words | Claim / function | Evidence pointer |
|---|---|---|---|
| 1 | 180 | Heat exposure is rising in compact mid-sized cities; policy stake. | Cite 1–2 IPCC AR6 urban climate items + Japan MLIT compact-city policy. |
| 2 | 180 | RS already does LULC×LST well: Landsat ST, NDVI/NDBI/NDWI, SUHI synthesis. | Cite 2 SUHI reviews + 2 recent ML-SHAP Asian-city papers. |
| 3 | 230 | Four unresolved gaps: state-not-process, meteorology, spatial confounding, global-only SHAP. | Cite 1 transition-matrix study, 1 weather-corrected LST study, 1 propensity-matching RS study, 1 SHAP UHI study. |
| 4 | 120 | We propose LUTHEA = trajectory + triple control + LUTHI family + HIPI. | Forward to § 3. |
| 5 | 180 | Why Yamaguchi: basin morphology, decadal but moderate LULC dynamics, JMA 81428 high-quality record, MLIT 立地適正化計画 relevance. | Forward to § 2 + 1 prior Japanese mid-city RS paper. |
| 6 | 200 | Five-bullet contribution list. | Forward to § 3 + § 4 + SI release. |

### § 2 Study area and data (≈ 800 words)

| Sub | ≈ words | Content |
|---|---|---|
| 2.1 Study areas — Yamaguchi + Yonago | 260 | Coordinates and climate normals (JMA 81428 for Yamaguchi, 68861 for Yonago); dual AOI definition (both central districts with their onsen quarters and 中心商店街); basin (Yamaguchi) vs coastal (Yonago) morphology contrast used as robustness dimension. Fig. 1 (two-panel). |
| 2.2 Satellite data | 220 | Table 1: Dynamic World V1 (10 m), Landsat 8/9 C2 L2 ST (30 m), ECOSTRESS (auxiliary), ESA WorldCover (cross-validation), MODIS (background). |
| 2.3 Meteorological, socio-economic, and policy data | 320 | JMA daily + AMeDAS 10-min for both stations; GSI DEM 5 m; OSM roads; GSW water. **New for Urban Climate**: e-Stat 250 m mesh 2020 census population + elderly share; FDMA weekly heatstroke ambulance transports for Yamaguchi and Tottori prefectures 2016–2025; MLIT 国土数値情報 A50 立地適正化計画 都市機能誘導区域 boundaries for both cities. |

### § 3 Methods (≈ 2 900 words; updated post-Urban-Climate pivot)

| Sub | ≈ words | Anchor equations | Figure / SI |
|---|---|---|---|
| 3.1 Framework overview | 210 | — | Fig. 2 flowchart |
| 3.2 Trajectory identification | 220 | Eq. 1–2 | Fig. 3 (in § 4.1) |
| 3.3 Weather-normalised LST + **Assumption B** | 440 | Eq. 3–5′ | SI Fig. S1 β̂ (forward ref to § 4.4) |
| 3.4 Stable Reference Set + matching | 360 | Eq. 6–7 | SI Fig. S2 love plot |
| 3.5 LUTHI / HSI + **A1–A4 identification statement** | 580 | Eq. 8–11 | Fig. 5 |
| 3.6 Path-level SHAP attribution | 240 | spatial 5-fold CV | Fig. 6 |
| 3.7 HIPI + **exposure / heatstroke / policy overlay** *(expanded)* | 320 | Eq. 12, Eq. 15a-b | Fig. 7 |
| 3.8 Uncertainty quantification | 320 | Eq. 13–14 | Fig. 5 CI bars + SI Table S2 |
| 3.9 Baseline-estimator comparisons | 210 | — | SI Table S4 |

§ 3.5 must contain the A1–A4 paragraph (defence against objection a).
§ 3.3 must contain the Assumption B paragraph (defence against
objection b) with forward reference to § 4.4. Multi-scale LUTHI(r) and
SSI are mentioned in a single sentence as "deferred to methodological
supplement" (post-Q3).

### § 4 Results (≈ 2 000 words, 9 subsections — H6-H8 added)

| Sub | ≈ words | Headline number(s) — pre-registered | Asset |
|---|---|---|---|
| 4.1 LULC dynamics 2016 → 2025 | 180 | net Built-up Δ%, Green Δ%, dominant flows | Fig. 3, Table 3 |
| 4.2 Raw vs weather-normalised LST trend | 190 | raw ΔLST ≈ +1.0 °C, ΔWNSC ≈ +0.4 °C, ratio ≤ 0.6 (H4) | Fig. 4 |
| 4.3 Path-level LUTHI — *central result (α, β)* | 340 | LUTHI(Green→Built-up): typ +1.0, ext +2.8 °C; HSI +1.8 °C. LUTHI(Built-up→Green): typ −1.2, ext −0.3 °C; \|HSI\| < 0.5 °C | Fig. 5, Table 4 |
| 4.4 β̂ specification sensitivity (defence b) | 200 | Spearman ρ ≥ 0.85 across 4 β̂ specs (H5) | SI Table S5 |
| 4.5 Path-stratified SHAP | 200 | top-3 covariates modulating HSI per path | Fig. 6 |
| **4.6 HIPI + population exposure + policy overlay** (**Urban Climate hook**) | 320 | Population exposure share ≥ 0.30 (H7); IoU(Q₄, Z) < 0.6 & missed ≥ 0.25 (H8) | Fig. 7 (three panels), Table 5 |
| **4.7 Heatstroke correlation (correlation-only)** | 160 | Spearman ρ(HSI\_year, transports\_year) reported with CI; no causal claim | SI Table S6, Fig. 7b |
| 4.8 Yonago replication (H6) | 240 | Path LUTHI ρ ≥ 0.6; HSI sign agreement on ≥ 4 of top-5 paths | SI Table S3, SI Fig. S3 |
| 4.9 Baseline-estimator comparison (defence a) | 170 | Asymmetry of α and β invisible under naïve / DiD / matching-only | SI Table S4 |

### § 5 Discussion (≈ 1 500 words, 6 paragraphs — reordered for Urban Climate)

| ¶ | ≈ words | Argument |
|---|---|---|
| 1 | 260 | **Mechanism of α/β asymmetry** — moisture-limited cooling of vegetation under heatwave regimes; latent-heat decoupling; how the DDD identification of HSI (A4) turns this observation into an estimated effect size. |
| 2 | 220 | **State vs process bias quantification** — recompute naïve mean-LST-by-class on identical pixels; report the systematic under-estimation of extreme-day warming. Compare to Tokyo TOD 2026's state-based finding. |
| 3 | 260 | **Compact city policy implications** — greening protection must be built into infill under the 立地適正化計画 framework; specific paragraph on how the IoU(Q₄, Z) < 0.6 finding maps to 都市機能誘導区域 revision. |
| 4 | 260 | **Population exposure and equity** — H7 result reframed as "who bears the α risk"; elderly-share disparity; caveat on health inference limits (correlation-only heatstroke overlay). |
| 5 | 260 | **Yonago generalisation and heterogeneity** — same α/β signs across basin (Yamaguchi) and coastal (Yonago) morphologies; boundary-layer / coastal-breeze differences discussed. |
| 6 | 240 | **Open methodological frontier** — spatially-varying β, hierarchical Bayesian extension, hourly LST via ECOSTRESS fusion, extending to health causal chain with municipality-level data if it becomes available. |

### § 6 Limitations (≈ 400 words, 5 bullets)

Already enumerated in `paper_conception.md` § 9. Keep tight, one
mitigation sentence per bullet.

### § 7 Conclusion (≈ 250 words, 1 paragraph)

Drafted in `paper_conception.md` § 10. End with the open-package
reproducibility sentence.

---

## 3. Per-paragraph claim map (Introduction in full + abbreviated Discussion)

> Each paragraph is reduced to one declarative sentence that the
> finished paragraph must defend. Tested by reading the column down
> end-to-end: it should read as a self-contained argument.

### § 1 Introduction

1. "Compact mid-sized cities are heating up while their LULC redistributes under compact-city policy — a tractable testbed."
2. "Remote sensing has matured on LULC × LST description but treats LULC as a state."
3. "Four un-controlled confounders inflate state-based attribution: process, meteorology, spatial mismatch, global ML."
4. "We propose LUTHEA, a trajectory-based quasi-causal framework, formalised as a LUTHI family."
5. "Yamaguchi's basin compactness, decadal-but-moderate LULC dynamics, and 立地適正化計画 anchor the case."
6. "Contributions: framework, indices, SHAP, HIPI, transferability, open package."

### § 5 Discussion (compressed)

1. "State-based contrasts overstate transition impact by ≈ X°C on the same data."
2. "Warming paths intensify under extreme heat; cooling paths do not symmetrically deepen — supporting moisture-limited mechanisms."
3. "300 m emerges as the diagnostic neighbourhood, consistent with LCZ blending."
4. "Compact-city policy is heat-coherent only when green corridors are protected during infill."
5. "LUTHEA's equations are city-neutral; only the AOI, station id, and class taxonomy must be re-specified."
6. "Spatially-varying β and Bayesian extensions remove the remaining identification residuals."

---

## 4. Evidence ledger (which asset supports which claim)

| Claim or argument | Required asset | Status |
|---|---|---|
| **α: Green→Built-up amplifies under extreme heat (HSI > 0)** | Fig. 5 + Table 4 HSI col | not produced |
| **β: Built-up→Green cooling collapses under extreme heat (\|HSI\| small)** | Fig. 5 + Table 4 HSI col | not produced |
| State-vs-process bias quantification | SI Table S4 + Discussion ¶ 2 sidebar | not produced |
| Triple control removes ≥ 40 % of apparent decadal warming (H4) | Fig. 4 + side metric | not produced |
| H1 — trajectory > end-state in partial R² | Fig. 6 SHAP + partial-R² table | not produced |
| H5 — LUTHI rankings stable across β̂ specs (Spearman ρ ≥ 0.85) | SI Table S5 | not produced |
| **H6 — Yonago replicates (Spearman ρ ≥ 0.6 + sign agreement ≥ 4/5)** | SI Table S3 + SI Fig. S3 | not produced |
| **H7 — HIPI top-quartile covers ≥ 30 % population + elevated elderly share** | Fig. 7a + Table 5 | not produced |
| **H8 — IoU(HIPI top-quartile, 都市機能誘導区域) < 0.6 with missed area ≥ 25 %** | Fig. 7c + Table 5 | not produced |
| Heatstroke correlation (correlation-only context) | Fig. 7b + SI Table S6 | not produced |
| LUTHI vs baseline estimators differ in detecting α/β asymmetry | SI Table S4 | not produced |
| Matching balance achieved (\|SMD\| < 0.1) | SI Fig. S2 love plot | not produced |
| Placebo passes for headline paths (p > 0.05) | Table 4 placebo *p* col | not produced |

---

## 5. Section dependency graph (writing order)

```
3.2 trajectory        ──┐
3.3 weather-normalised ─┼─► 3.4 SRS + matching ─► 3.5 LUTHI family ─┐
3.7 HIPI                │                                            │
                        │                                            ▼
                        └──────────────► 3.6 path-stratified SHAP ──► 4 Results
                                                                     │
                                                                     ▼
                                                          5 Discussion → 6 Limits → 7 Conclusion
                                                                     │
                            (write last)         ◄────────────────── 1 Intro / Abstract
```

Recommended writing order: § 3 → § 4 → § 5 → § 6 → § 7 → § 1 → Abstract → SI.
Rationale: Methods stabilise the vocabulary; Results commit the
numbers; Discussion and Intro then frame those numbers honestly.

---

## 6. Submission checklist (Remote Sensing template)

- [ ] LaTeX template `Definitive_Article_Template` from MDPI Remote Sensing
- [ ] Author affiliations finalised
- [ ] Each figure ≤ 17 cm wide, 300 dpi PNG/PDF, colour-blind-safe palette
- [ ] All equations numbered (1–16)
- [ ] Data and code availability statement: Zenodo DOI of `luthea` package + GEE asset paths
- [ ] Funding statement, conflicts of interest, author contributions (CRediT)
- [ ] ORCID for every author
- [ ] Cover letter < 300 words emphasising (a) trajectory novelty, (b) triple control, (c) open package, (d) transferability
- [ ] Suggested reviewers (≥ 3 — must be outside the project)
- [ ] SI: love plot, β̂ table, multi-scale full table, second-city full results, placebo robustness with block clusters

---

## 7. Working file map

```
yamaguchi/manuscript/
├── paper_conception.md      ← narrative draft, 530 lines, fully written
├── paper_framework.md       ← THIS FILE — IMRAD skeleton + ledger
├── (to add) main.tex        ← LaTeX manuscript (Remote Sensing template)
├── (to add) supplementary.tex
├── (to add) refs.bib        ← collected from § 12 reference search brief
└── (to add) figures/        ← rendered PDFs/PNGs from luthea.viz
```

---

## 8. Definition of done — section-level acceptance criteria

| Section | Done when … |
|---|---|
| § 2 | AOI polygon + Table 1 finalised; figure 1 rendered. |
| § 3 | All 16 equations numbered, cross-references to code commit hashes in `luthea/` modules. |
| § 4 | All 7 sub-results have a hypothesised → observed comparison sentence. |
| § 5 | Each of 6 paragraphs cites at least one Fig/Table in § 4. |
| § 6 | Each limitation has a mitigation/SI pointer. |
| § 7 | One sentence each for: what's new, what was found, what generalises, what's released. |
| Abstract | 5-move structure with each move ≤ 60 words. |

---

## 9. Open framework-level questions for the user

1. Confirm the title-1 vs title-3 choice — depends on whether you want
   "method" (Remote Sensing) or "case + policy" (Urban Climate) framing
   to dominate.
2. Second-city pick: 米子 / 松江 / 鳥取 — which one? Affects § 4.7
   wording and the SI replication run.
3. Author list and CRediT roles — needed before § 6 Discussion is
   finalised.
4. Funding statement / grant numbers — required by Remote Sensing.
5. Whether the open-package release will accompany submission (Zenodo
   DOI minted at submission) or after acceptance.
