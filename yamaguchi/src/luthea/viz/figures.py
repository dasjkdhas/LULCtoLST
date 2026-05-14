"""High-level figure builders mapped to the 7 main figures of the paper.

Manuscript reference: § H (Figure and table captions) of paper_conception.md.

Each function returns a `matplotlib.figure.Figure` and (optionally) writes
it to disk. Inputs are NumPy / pandas / xarray objects produced by the
analytical modules; figure functions never run analysis themselves.

The figures we generate here:
    Fig. 3 — LULC dynamics (3-panel): t0 map, t1 map, Sankey of flows
    Fig. 4 — WNSC change (3-panel): raw ΔLST, ΔWNSC, difference
    Fig. 5 — Path-level LUTHI bars (CENTRAL) — α/β at a glance
    Fig. 6 — Path-stratified SHAP heatmap
    Fig. 7 — HIPI top-quartile map

Fig. 1 (study area) and Fig. 2 (framework flowchart) are produced
manually (cartopy + Inkscape) and are not generated here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import matplotlib
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .maps import style_lst_cmap, style_lulc_cmap


def _save(fig: matplotlib.figure.Figure, out: Path | str | None) -> None:
    if out is None:
        return
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300, bbox_inches="tight")


# ── Fig. 3 ──────────────────────────────────────────────────────────────

def fig3_lulc_and_sankey(lulc_t0: np.ndarray, lulc_t1: np.ndarray,
                         transitions_long: pd.DataFrame,
                         out: Path | str | None = None
                         ) -> matplotlib.figure.Figure:
    """3-panel: (a) LULC at t0, (b) LULC at t1, (c) area-bar of flows.

    The full Sankey rendering uses Plotly and is delegated to
    `luthea.viz.sankey.plot_sankey`; here we draw a stacked area-bar
    fallback so the matplotlib figure is self-contained.
    """
    cmap = style_lulc_cmap()

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, arr, title in [(axes[0], lulc_t0, "LULC 2016"),
                            (axes[1], lulc_t1, "LULC 2025")]:
        _draw_lulc_map(ax, arr, cmap)
        ax.set_title(title)
        ax.axis("off")

    # Panel (c): horizontal bar of pixel-count flows, sorted desc
    df = (transitions_long
          .query("dom_start != dom_end")
          .sort_values("n_pixels", ascending=True)
          .tail(8))
    labels = [f"{int(s)}→{int(e)}" for s, e in zip(df["dom_start"], df["dom_end"])]
    axes[2].barh(labels, df["n_pixels"], color="#888")
    axes[2].set_xlabel("Pixel count")
    axes[2].set_title("Top transitions")
    axes[2].grid(axis="x", alpha=0.3)

    fig.suptitle("Figure 3 — LULC dynamics 2016 → 2025", y=1.02, fontsize=12)
    _save(fig, out)
    return fig


def _draw_lulc_map(ax, arr: np.ndarray, class_color: Mapping[int, str]) -> None:
    arr = np.asarray(arr)
    keys = sorted(class_color)
    cmap = matplotlib.colors.ListedColormap([class_color[k] for k in keys])
    bounds = [k - 0.5 for k in keys] + [keys[-1] + 0.5]
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    ax.imshow(arr, cmap=cmap, norm=norm, interpolation="nearest")


# ── Fig. 4 ──────────────────────────────────────────────────────────────

def fig4_wnsc_change(raw_delta: np.ndarray, wnsc_delta: np.ndarray,
                     out: Path | str | None = None,
                     vmin: float = -3.0, vmax: float = 3.0
                     ) -> matplotlib.figure.Figure:
    """(a) raw ΔLST 2016→2025, (b) ΔWNSC under triple control,
    (c) per-pixel difference (a) − (b), highlighting the meteorological
    inflation removed."""
    diff = np.asarray(raw_delta) - np.asarray(wnsc_delta)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, arr, title in [(axes[0], raw_delta, "(a) Raw ΔLST"),
                            (axes[1], wnsc_delta, "(b) ΔWNSC (triple control)"),
                            (axes[2], diff, "(c) Meteorological inflation removed")]:
        im = ax.imshow(arr, cmap="RdBu_r", vmin=vmin, vmax=vmax)
        ax.set_title(title)
        ax.axis("off")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="°C")

    fig.suptitle("Figure 4 — Raw vs weather-normalised LST change", y=1.02, fontsize=12)
    _save(fig, out)
    return fig


# ── Fig. 5 — CENTRAL ────────────────────────────────────────────────────

def fig5_luthi_bars(luthi_table: pd.DataFrame,
                    out: Path | str | None = None,
                    headline_paths: list[Any] | None = None
                    ) -> matplotlib.figure.Figure:
    """Path-level LUTHI bars with bootstrap 95 % CIs and placebo p.

    `luthi_table` must have one row per path and the following columns
    (plus a `path` column or path-keyed index):
        LUTHI_typ, ci_low_typ, ci_high_typ,
        LUTHI_ext, ci_low_ext, ci_high_ext,
        HSI, placebo_p
    """
    df = luthi_table.copy()
    if "path" in df.columns:
        df = df.set_index("path")
    df = df.sort_values("LUTHI_typ", ascending=True)

    paths = df.index.astype(str).to_list()
    y_pos = np.arange(len(paths))
    bar_h = 0.35

    fig, ax = plt.subplots(figsize=(8, 0.6 * len(paths) + 1.5))
    ax.barh(y_pos - bar_h / 2, df["LUTHI_typ"], height=bar_h,
            xerr=[df["LUTHI_typ"] - df["ci_low_typ"],
                  df["ci_high_typ"] - df["LUTHI_typ"]],
            color="#3a6bd9", label="Typical day", alpha=0.85,
            error_kw=dict(ecolor="black", capsize=2, lw=0.7))
    ax.barh(y_pos + bar_h / 2, df["LUTHI_ext"], height=bar_h,
            xerr=[df["LUTHI_ext"] - df["ci_low_ext"],
                  df["ci_high_ext"] - df["LUTHI_ext"]],
            color="#d94e3a", label="Extreme day", alpha=0.85,
            error_kw=dict(ecolor="black", capsize=2, lw=0.7))

    ax.axvline(0, color="black", lw=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(paths)
    ax.set_xlabel("LUTHI (°C)")
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.3)
    ax.set_title("Figure 5 — Path-level LUTHI under typical vs extreme heat")

    # HSI annotation per row
    xmax = max(df["ci_high_ext"].max(), df["ci_high_typ"].max())
    for i, p in enumerate(paths):
        hsi_v = df.loc[df.index[i], "HSI"]
        text = f"HSI={hsi_v:+.2f}"
        if "placebo_p" in df.columns and not pd.isna(df.loc[df.index[i], "placebo_p"]):
            text += f", p={df.loc[df.index[i], 'placebo_p']:.2f}"
        ax.text(xmax * 1.02, y_pos[i], text, va="center", fontsize=8)

    if headline_paths:
        for p in headline_paths:
            if str(p) in paths:
                i = paths.index(str(p))
                ax.add_patch(mpatches.Rectangle(
                    (ax.get_xlim()[0], y_pos[i] - 0.5), xmax * 2, 1.0,
                    facecolor="yellow", alpha=0.12, zorder=-1))

    fig.tight_layout()
    _save(fig, out)
    return fig


# ── Fig. 6 ──────────────────────────────────────────────────────────────

def fig6_shap(global_summary: pd.DataFrame,
              path_stratified: pd.DataFrame,
              out: Path | str | None = None,
              top_n_features: int = 8) -> matplotlib.figure.Figure:
    """(a) global mean |SHAP| bar; (b) path × feature heatmap of mean |SHAP|."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5),
                             gridspec_kw={"width_ratios": [1, 1.6]})

    # (a) global summary
    g = global_summary.head(top_n_features).iloc[::-1]
    axes[0].barh(g["feature"], g["mean_abs_shap"], color="#444")
    axes[0].set_xlabel("Mean |SHAP|")
    axes[0].set_title("(a) Global feature importance")
    axes[0].grid(axis="x", alpha=0.3)

    # (b) path × feature heatmap (excluding path one-hots themselves)
    h = (path_stratified[~path_stratified["feature"].astype(str)
                          .str.startswith("path_")]
         .pivot(index="path", columns="feature", values="mean_abs_shap"))
    h = h.loc[:, h.mean().sort_values(ascending=False).head(top_n_features).index]
    im = axes[1].imshow(h.values, aspect="auto", cmap="viridis")
    axes[1].set_xticks(range(h.shape[1]))
    axes[1].set_xticklabels(h.columns, rotation=45, ha="right")
    axes[1].set_yticks(range(h.shape[0]))
    axes[1].set_yticklabels([str(p) for p in h.index])
    axes[1].set_title("(b) Path-stratified mean |SHAP|")
    fig.colorbar(im, ax=axes[1], fraction=0.046, pad=0.04, label="Mean |SHAP|")

    fig.suptitle("Figure 6 — XGBoost SHAP attribution", y=1.02, fontsize=12)
    fig.tight_layout()
    _save(fig, out)
    return fig


# ── Fig. 7 ──────────────────────────────────────────────────────────────

def fig7_hipi(hipi: np.ndarray, quartiles: np.ndarray,
              walk_lines: list[tuple[np.ndarray, np.ndarray]] | None = None,
              out: Path | str | None = None) -> matplotlib.figure.Figure:
    """Two-panel: continuous HIPI raster on the left, top-quartile mask
    overlaid with optional pedestrian-axis line strings on the right."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    im0 = axes[0].imshow(hipi, cmap="magma")
    axes[0].set_title("(a) HIPI (continuous)")
    axes[0].axis("off")
    fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04, label="HIPI (z-units)")

    quartile_map = np.where(quartiles == 3, 1.0, np.nan)
    axes[1].imshow(np.zeros_like(hipi), cmap="Greys", vmin=0, vmax=1)
    axes[1].imshow(quartile_map, cmap="Reds", vmin=0, vmax=1, alpha=0.85)
    axes[1].set_title("(b) Top-quartile priority cells")
    axes[1].axis("off")

    if walk_lines:
        for xs, ys in walk_lines:
            axes[1].plot(xs, ys, color="cyan", lw=2, alpha=0.85)

    fig.suptitle("Figure 7 — Heat Improvement Priority Index", y=1.02, fontsize=12)
    fig.tight_layout()
    _save(fig, out)
    return fig
