"""Weather-Normalised Summer LST Composite.

WNSC_y(p) = median{ LST_norm(p, d) : d ∈ typical_days(y) }
Extreme variant uses extreme_days(y).
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import xarray as xr


def composite_year(normalised_scenes: Sequence[xr.DataArray], min_obs: int = 2
                   ) -> xr.DataArray:
    """Pixel-wise median across one year's typical (or extreme) scenes.

    Pixels with fewer than `min_obs` valid observations are set to NaN to avoid
    medians dominated by a single noisy date.
    """
    if not normalised_scenes:
        raise ValueError("composite_year: empty scene list")
    stack = xr.concat(normalised_scenes, dim="time")
    n_valid = stack.notnull().sum(dim="time")
    med = stack.median(dim="time", skipna=True)
    return med.where(n_valid >= min_obs)


def save_geotiff(da: xr.DataArray, path: Path) -> None:
    """Write DataArray as GeoTIFF. Requires rioxarray and a CRS already on `da`."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    crs = getattr(getattr(da, "rio", None), "crs", None)
    if crs is None:
        raise ValueError("save_geotiff: DataArray has no CRS — call da.rio.write_crs first")
    da.rio.to_raster(path, dtype="float32", compress="DEFLATE")
