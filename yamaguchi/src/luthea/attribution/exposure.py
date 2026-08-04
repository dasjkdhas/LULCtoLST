"""Step 10.5 — Urban Climate policy/exposure/health overlays.

Three algorithms translate the raster HIPI (§ 3.7) into the
decision-relevant summaries reported in Fig. 7 and Table 5 of the
manuscript:

  1. `population_exposure`  — H7: how many residents live in the HIPI
     top-quartile cells; elderly-share disparity.
  2. `heatstroke_correlation` — § 4.7: Spearman ρ between annual AOI-mean
     HSI and annual prefecture-level heatstroke ambulance transports.
     Correlation-only; manuscript explicitly disclaims causal reading.
  3. `policy_overlap` — H8: IoU and missed-area share of the HIPI
     top-quartile against 都市機能誘導区域 polygons from MLIT A50.

Manuscript reference: § 3.7 exposure/heat/policy overlays; Eq. 15a-b.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


# ── 1. Population exposure (H7) ─────────────────────────────────────────

def population_exposure(hipi_quartiles: np.ndarray,
                        pixel_areas_m2: np.ndarray,
                        pixel_to_mesh_intersection: pd.DataFrame,
                        mesh_population: pd.Series,
                        mesh_area_m2: pd.Series,
                        elderly_by_mesh: pd.Series | None = None,
                        top_quartile_label: int = 3,
                        ) -> dict[str, float]:
    """Report population and elderly share resident inside HIPI top quartile.

    Parameters
    ----------
    hipi_quartiles : (H*W,) int array
        Output of `attribution.hipi.priority_quartiles`; -1 masked,
        0..3 quartile labels.
    pixel_areas_m2 : (H*W,) float array
        Area of each 30 m raster pixel (typically constant, but supports
        variable projection).
    pixel_to_mesh_intersection : DataFrame with columns
        {pixel_idx, mesh_id, intersect_area_m2}
        Pre-computed intersection table between 30 m raster pixels and
        250 m census mesh cells.
    mesh_population : Series indexed by mesh_id giving total residents.
    mesh_area_m2 : Series indexed by mesh_id giving mesh area.
    elderly_by_mesh : optional Series indexed by mesh_id giving aged-65+ count.
    top_quartile_label : integer flag for the top quartile (default 3).

    Returns
    -------
    {population_in_Q4, population_in_AOI, exposure_share,
     elderly_in_Q4, elderly_in_AOI, elderly_share_ratio}
    """
    flat_q = np.asarray(hipi_quartiles).ravel()
    in_aoi = flat_q >= 0
    in_q4 = flat_q == top_quartile_label

    df = pixel_to_mesh_intersection.copy()
    df["in_aoi"] = in_aoi[df["pixel_idx"].to_numpy()]
    df["in_q4"] = in_q4[df["pixel_idx"].to_numpy()]

    df["pop_share"] = (df["intersect_area_m2"].to_numpy() /
                      mesh_area_m2.reindex(df["mesh_id"]).to_numpy())
    df["pop_here"] = df["pop_share"] * mesh_population.reindex(df["mesh_id"]).to_numpy()

    pop_aoi = float(df.loc[df["in_aoi"], "pop_here"].sum())
    pop_q4 = float(df.loc[df["in_q4"], "pop_here"].sum())
    result: dict[str, float] = {
        "population_in_AOI": pop_aoi,
        "population_in_Q4": pop_q4,
        "exposure_share": pop_q4 / pop_aoi if pop_aoi else float("nan"),
    }

    if elderly_by_mesh is not None:
        df["eld_here"] = df["pop_share"] * elderly_by_mesh.reindex(df["mesh_id"]).to_numpy()
        eld_aoi = float(df.loc[df["in_aoi"], "eld_here"].sum())
        eld_q4 = float(df.loc[df["in_q4"], "eld_here"].sum())
        share_aoi = eld_aoi / pop_aoi if pop_aoi else float("nan")
        share_q4 = eld_q4 / pop_q4 if pop_q4 else float("nan")
        result.update({
            "elderly_in_AOI": eld_aoi,
            "elderly_in_Q4": eld_q4,
            "elderly_share_AOI": share_aoi,
            "elderly_share_Q4": share_q4,
            "elderly_share_ratio": (share_q4 / share_aoi
                                    if share_aoi else float("nan")),
        })
    return result


# ── 2. Heatstroke correlation (§ 4.7, correlation-only) ─────────────────

def heatstroke_correlation(annual_hsi: pd.Series,
                           annual_transports: pd.Series,
                           bootstrap: int = 1000,
                           seed: int = 20260512,
                           lag: int = 0) -> dict[str, float]:
    """Spearman ρ between AOI-mean HSI and prefecture-level heatstroke
    ambulance transports, with bootstrap 95 % CI.

    **Correlation-only**: the manuscript disclaims any causal reading
    because FDMA data are prefecture-level while HSI is AOI-scale
    (§ 6 Limitations).

    Parameters
    ----------
    annual_hsi : Series indexed by year (int).
    annual_transports : Series indexed by year (int).
    bootstrap : replicates for percentile CI.
    seed : RNG seed for reproducibility.
    lag : shift transports by `lag` years relative to HSI; 0 = same year.
    """
    from scipy.stats import spearmanr

    common = annual_hsi.index.intersection(annual_transports.index + lag)
    x = annual_hsi.reindex(common).to_numpy()
    y = annual_transports.reindex(common - lag).to_numpy()

    keep = ~np.isnan(x) & ~np.isnan(y)
    x, y = x[keep], y[keep]
    if len(x) < 4:
        return {"rho": float("nan"), "p_value": float("nan"),
                "ci_low": float("nan"), "ci_high": float("nan"), "n": int(len(x))}

    rho, p = spearmanr(x, y)
    rng = np.random.default_rng(seed)
    boot = np.empty(bootstrap)
    for b in range(bootstrap):
        idx = rng.integers(0, len(x), len(x))
        boot[b], _ = spearmanr(x[idx], y[idx])
    return {
        "rho": float(rho),
        "p_value": float(p),
        "ci_low": float(np.nanquantile(boot, 0.025)),
        "ci_high": float(np.nanquantile(boot, 0.975)),
        "n": int(len(x)),
    }


# ── 3. Policy overlap (H8) ──────────────────────────────────────────────

def policy_overlap(hipi_quartiles_mask: np.ndarray,
                   policy_mask: np.ndarray,
                   top_quartile_label: int = 3) -> dict[str, float]:
    """Intersection-over-union between HIPI top-quartile pixels and a
    boolean rasterisation of the 都市機能誘導区域 polygon.

    Both arrays must be aligned on the same 30 m grid.

    Returns
    -------
    {iou, missed_share, policy_share, hipi_area, policy_area,
     intersection, union}
    """
    q4 = np.asarray(hipi_quartiles_mask) == top_quartile_label
    z = np.asarray(policy_mask, dtype=bool)

    if q4.shape != z.shape:
        raise ValueError(f"shape mismatch: hipi {q4.shape} vs policy {z.shape}")

    inter = int((q4 & z).sum())
    union = int((q4 | z).sum())
    q4_area = int(q4.sum())
    z_area = int(z.sum())

    return {
        "iou": inter / union if union else float("nan"),
        "missed_share": (q4_area - inter) / q4_area if q4_area else float("nan"),
        "policy_share": inter / z_area if z_area else float("nan"),
        "hipi_area_pixels": q4_area,
        "policy_area_pixels": z_area,
        "intersection_pixels": inter,
        "union_pixels": union,
    }


# ── 4. Summary DataFrame for Table 5 ────────────────────────────────────

def build_table5(exposure: dict[str, float],
                 overlap: dict[str, float],
                 heat: dict[str, float]) -> pd.DataFrame:
    """Assemble the Urban Climate summary table (Table 5)."""
    rows = [
        ("population_in_Q4", exposure.get("population_in_Q4")),
        ("exposure_share", exposure.get("exposure_share")),
        ("elderly_share_ratio", exposure.get("elderly_share_ratio")),
        ("iou_HIPI_UDA", overlap.get("iou")),
        ("missed_share", overlap.get("missed_share")),
        ("policy_share", overlap.get("policy_share")),
        ("heatstroke_rho", heat.get("rho")),
        ("heatstroke_ci_low", heat.get("ci_low")),
        ("heatstroke_ci_high", heat.get("ci_high")),
    ]
    return (pd.DataFrame(rows, columns=["metric", "value"])
              .set_index("metric"))
