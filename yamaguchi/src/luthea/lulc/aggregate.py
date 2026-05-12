"""Step 6 — Aggregate 10 m Dynamic World to the 30 m LST grid.

For each 30 m cell, compute:
  - PLAND_k for k in DW classes (proportion of 9 sub-pixels);
  - dominant class = argmax_k PLAND_k.
"""

from __future__ import annotations

import numpy as np
import xarray as xr


def aggregate_to_30m(dw_10m: xr.DataArray, n_classes: int = 9) -> xr.Dataset:
    """Return a Dataset with one PLAND_k DataArray per class plus 'dominant'."""
    raise NotImplementedError
