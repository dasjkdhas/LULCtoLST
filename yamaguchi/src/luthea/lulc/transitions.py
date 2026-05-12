"""Two-period transition identification (2016 ↔ 2025) at 30 m."""

from __future__ import annotations

import xarray as xr

from ..config import DOMINANT_PLAND_MIN


def identify_transitions(ds_start: xr.Dataset, ds_end: xr.Dataset) -> xr.Dataset:
    """Return Dataset with:
       - dom_start, dom_end (uint8 class codes);
       - transition_code (uint16, dom_start * 100 + dom_end);
       - valid (bool, |Δ PLAND_dominant| ≥ DOMINANT_PLAND_MIN at both ends).
    Pixels with valid == False are labelled 'mixed/unchanged'.
    """
    raise NotImplementedError
