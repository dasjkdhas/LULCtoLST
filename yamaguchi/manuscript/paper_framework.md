# Paper Framework — Skeleton Outline

> Companion to `paper_conception.md`. Where the conception document
> drafts narrative content, this file is the **structural skeleton**:
> section numbering, word budgets, per-paragraph claims, the
> figure/table evidence ledger, and the dependency graph between
> sections.
>
> Target journal: *Remote Sensing*. Target total length: ≈ 8 500 words
> (excluding references, captions, SI). Section budgets below sum to
> ≈ 8 700 — trim during revision.

---

## 0. Article identity card

| Field | Value |
|---|---|
| Working title | LUTHEA: A Quasi-Causal Attribution Framework for Land-Use Transition-Driven Urban Heat Change Using Multi-Source Satellite Data |
| Journal | Remote Sensing (MDPI) |
| Article type | Research article |
| Reader profile | Remote-sensing methodologists; urban-climate empiricists; ML + causal-inference cross-over |
| One-sentence pitch | We replace state-based LULC×LST correlations with a quasi-causal, trajectory-based attribution that survives weather + spatial confounder controls and a placebo test. |
| Headline number to hit | ≥ 1 transition path with bootstrap CI not crossing zero AND placebo p > 0.05 in both typical *and* extreme scenarios |
| Manuscript deadline (self-set) | end of Yamaguchi pipeline + 6 weeks |

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

### § 2 Study area and data (≈ 750 words)

| Sub | ≈ words | Content |
|---|---|---|
| 2.1 Study area | 250 | Coordinates, climate normals (JMA 81428), AOI definition (山口駅 – 中央商店街 – 県庁 – 湯田温泉), basin geometry, OSM basemap. Fig. 1. |
| 2.2 Satellite data | 250 | Table 1: Dynamic World V1 (10 m, yearly mode), Landsat 8/9 C2 L2 ST (30 m), ECOSTRESS (auxiliary), ESA WorldCover (cross-validation), MODIS (background only). Justify exclusions. |
| 2.3 Meteorological and ancillary data | 250 | JMA 81428 daily + AMeDAS 10-min schema, GSI DEM 5 m / ALOS AW3D30, OSM roads, GSW water mask, OSM/基盤地図 buildings. |

### § 3 Methods (≈ 2 500 words)

| Sub | ≈ words | Anchor equations | Figure |
|---|---|---|---|
| 3.1 Framework overview | 200 | — | Fig. 2 flowchart |
| 3.2 Trajectory identification | 250 | Eq. 1–2 | Fig. 3 (in § 4.1) |
| 3.3 Weather-normalised LST | 380 | Eq. 3–5′ | SI Fig. S1 β̂ |
| 3.4 Stable Reference Set + matching | 380 | Eq. 6–7 | SI Fig. S2 love plot |
| 3.5 LUTHI index family | 460 | Eq. 8–13 | Fig. 5, Fig. 6 |
| 3.6 Path-level SHAP attribution | 260 | spatial 5-fold CV | Fig. 7 |
| 3.7 Heat Improvement Priority Index | 220 | Eq. 14 | Fig. 8 |
| 3.8 Uncertainty quantification | 350 | Eq. 15–16 | Fig. 5 CI bars + SI Table S2 |

Inside § 3.5 keep the dedicated paragraph rebutting the "this is just
difference-in-differences" reading (four-point argument: meteorology,
matching, multi-scale conditioning, placebo).

### § 4 Results (≈ 1 800 words, 7 subsections, each 1 figure or table)

| Sub | ≈ words | Headline number(s) — to be filled | Asset |
|---|---|---|---|
| 4.1 LULC dynamics 2016 → 2025 | 220 | net Built-up Δ%, Green Δ%, dominant flows | Fig. 3, Table 3 |
| 4.2 Raw vs weather-normalised LST trend | 250 | raw ΔLST, ΔWNSC; reduction factor | Fig. 4 |
| 4.3 Path-level LUTHI | 340 | LUTHI_typ, LUTHI_ext per path with 95 % CI and placebo p | Fig. 5, Table 4 |
| 4.4 Multi-scale + SSI | 260 | r*, sign and magnitude of SSI per path | Fig. 6, Table 5 |
| 4.5 Path-stratified SHAP | 250 | top-3 modulating covariates per warming path | Fig. 7 |
| 4.6 HIPI top-quartile map | 220 | % AOI flagged; intersection with pedestrian axis length | Fig. 8 |
| 4.7 Second-city transferability | 260 | Spearman ρ of path LUTHI rankings | SI Table S3, SI Fig. S3 |

### § 5 Discussion (≈ 1 500 words, 6 paragraphs)

| ¶ | ≈ words | Argument |
|---|---|---|
| 1 | 280 | Quantify the bias of state-based analysis: rerun naïve mean-LST-by-class contrast on the same pixels, report magnitude vs LUTHI. |
| 2 | 260 | Asymmetry under extreme heat (HSI signs); plausible biophysics (surface moisture, roughness, latent decoupling). |
| 3 | 220 | Why 300 m is the diagnostic scale; relate to LCZ and boundary-layer blending. |
| 4 | 260 | Policy implication for コンパクトシティ — preserving green corridors while compacting elsewhere. |
| 5 | 240 | What generalises (Eq. 1–16, package), what doesn't (Yamaguchi-specific parameters). |
| 6 | 240 | Open methodological frontier — spatially-varying β, hierarchical Bayesian extension, hourly LST via ECOSTRESS fusion. |

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
| State-vs-process bias quantification | Fig. 4 + Discussion ¶ 1 sidebar table | not produced |
| Green→Built-up LUTHI positive, CI > 0 | Fig. 5, Table 4 (paths × scenario) | not produced |
| HSI asymmetry | Fig. 5 (paired), Table 4 column HSI | not produced |
| 300 m diagnostic scale | Fig. 6 + Table 5 + SSI column | not produced |
| Path-modulating covariates | Fig. 7 path-stratified SHAP | not produced |
| HIPI overlaps pedestrian axis | Fig. 8 + AOI walk-line GIS layer | not produced |
| Method generalises to second city | SI Table S3 + SI Fig. S3 | not produced |
| β̂ has expected signs | SI Fig. S1 / SI Table S1 | not produced |
| Matching balance achieved | SI Fig. S2 love plot | not produced |
| Placebo passes for headline paths | Table 4 placebo p column | not produced |

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
