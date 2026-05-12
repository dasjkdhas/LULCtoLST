"""Optional multi-year trajectory clustering (10-year sequences → groups)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def encode_trajectories(yearly_dominant: pd.DataFrame) -> pd.Series:
    """Encode 10-year (dom_2016 … dom_2025) sequences as compact strings."""
    raise NotImplementedError


def cluster_trajectories(seqs: pd.Series, k: int = 6) -> pd.Series:
    """K-medoids over Levenshtein-style distance OR direct K-means on
    one-hot per-year embeddings. Return cluster id per pixel."""
    raise NotImplementedError
