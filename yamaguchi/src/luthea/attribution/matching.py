"""Step 7 — Stable Reference Set construction and Mahalanobis kNN matching.

For each transition pixel in class k → j, find k nearest stable pixels
(LULC_2016 == LULC_2025 == k) by Mahalanobis distance over baseline
covariates: NDVI_2016, NDBI_2016, NDWI_2016, Albedo_2016, DEM, slope,
distance_to_water, distance_to_road, distance_to_green, plus
neighbourhood PLAND_built / PLAND_green at radii 100/300/500 m.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def stable_reference_set(transitions: pd.DataFrame) -> dict[int, pd.Index]:
    """{class_code: Index of stable pixels for that class}."""
    raise NotImplementedError


def mahalanobis_knn(transition_X: np.ndarray, reference_X: np.ndarray, k: int = 5,
                   ) -> np.ndarray:
    """Return (n_transition, k) array of reference-row indices."""
    raise NotImplementedError


def smd(matched: pd.DataFrame, covariates: list[str]) -> pd.Series:
    """Standardised mean differences for balance diagnostic; |SMD| < 0.1 ok."""
    raise NotImplementedError
