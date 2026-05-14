"""Sankey for LULC transition flows (Fig. 3b detail).

When Plotly is available, render a real Sankey to HTML; otherwise a
placeholder Figure with a textual flow listing.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def plot_sankey(transitions: pd.DataFrame, out_html: Path | str) -> None:
    """`transitions` columns: dom_start, dom_end, n_pixels."""
    out_html = Path(out_html)
    out_html.parent.mkdir(parents=True, exist_ok=True)

    try:
        import plotly.graph_objects as go
    except ImportError:
        out_html.write_text(
            "<!doctype html><h2>Sankey placeholder</h2>"
            "<p>Install plotly to render.</p>"
            f"<pre>{transitions.to_string(index=False)}</pre>",
            encoding="utf-8",
        )
        return

    classes_in = transitions["dom_start"].unique().tolist()
    classes_out = transitions["dom_end"].unique().tolist()
    nodes = [f"{int(c)} (t0)" for c in classes_in] + [f"{int(c)} (t1)" for c in classes_out]
    src_index = {c: i for i, c in enumerate(classes_in)}
    tgt_index = {c: len(classes_in) + i for i, c in enumerate(classes_out)}

    sources = transitions["dom_start"].map(src_index).to_list()
    targets = transitions["dom_end"].map(tgt_index).to_list()
    values = transitions["n_pixels"].to_list()

    fig = go.Figure(go.Sankey(
        node=dict(label=nodes, pad=20, thickness=18),
        link=dict(source=sources, target=targets, value=values),
    ))
    fig.update_layout(title="LULC transitions 2016 → 2025", font_size=11)
    fig.write_html(out_html)
