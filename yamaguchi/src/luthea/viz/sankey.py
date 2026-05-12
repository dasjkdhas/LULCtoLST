"""Sankey for LULC transition flows (Fig.3b)."""

from __future__ import annotations
from pathlib import Path
import pandas as pd


def plot_sankey(transitions: pd.DataFrame, out_html: Path) -> None:
    """Use plotly.graph_objects.Sankey to render flows of pixel counts."""
    raise NotImplementedError
