"""Weather-Normalised Summer LST Composite.

WNSC_y(p) = median{ LST_norm(p, d) : d ∈ typical_days(y) }
Extreme variant uses extreme_days(y).
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import xarray as xr

from ..config import MIN_SCENES_PER_EPOCH_SCENARIO


def composite_year(normalised_scenes: Sequence[xr.DataArray], min_obs: int = 2
                   ) -> xr.DataArray:
    """Pixel-wise median across one year's typical (or extreme) scenes.

    Pixels with fewer than `min_obs` valid observations are set to NaN to avoid
    medians dominated by a single noisy date.

    .. note::
       For the Yamaguchi/Yonago record this is **not** the headline
       estimator — five individual years contribute only one scene each,
       so single-year composites collapse to NaN. Use
       :func:`composite_epoch` for the t0/t1 contrast; this function is
       retained for the per-year trend figure and for study areas with a
       denser record.
    """
    if not normalised_scenes:
        raise ValueError("composite_year: empty scene list")
    stack = xr.concat(normalised_scenes, dim="time")
    n_valid = stack.notnull().sum(dim="time")
    med = stack.median(dim="time", skipna=True)
    return med.where(n_valid >= min_obs)


def composite_epoch(scenes_by_year: Mapping[int, Sequence[xr.DataArray]],
                    epoch_years: Sequence[int],
                    min_obs: int = MIN_SCENES_PER_EPOCH_SCENARIO
                    ) -> tuple[xr.DataArray, dict]:
    """Pixel-wise median across every scene in a multi-year epoch.

    This is the headline WNSC estimator. Pooling three years restores the
    per-pixel observation count that single-year compositing cannot reach
    with a sparse cloud-screened Landsat record.

    Parameters
    ----------
    scenes_by_year : mapping year -> list of weather-normalised scenes
        already filtered to one scenario (typical **or** extreme).
    epoch_years : the years belonging to this epoch, e.g. ``EPOCH_EARLY``.
    min_obs : minimum valid observations per pixel.

    Returns
    -------
    (composite, provenance) where `provenance` records the contributing
    year counts and the total scene count, for the manuscript's Table 2.
    """
    scenes: list[xr.DataArray] = []
    per_year: dict[int, int] = {}
    for y in epoch_years:
        got = list(scenes_by_year.get(y, []))
        per_year[int(y)] = len(got)
        scenes.extend(got)

    provenance = {
        "epoch_years": [int(y) for y in epoch_years],
        "scenes_per_year": per_year,
        "n_scenes": len(scenes),
        "min_obs": int(min_obs),
        "sufficient": len(scenes) >= min_obs,
    }
    if not scenes:
        raise ValueError(
            f"composite_epoch: no scenes for epoch {tuple(epoch_years)}")

    stack = xr.concat(scenes, dim="time")
    n_valid = stack.notnull().sum(dim="time")
    med = stack.median(dim="time", skipna=True)
    return med.where(n_valid >= min_obs), provenance


def save_geotiff(da: xr.DataArray, path: Path) -> None:
    """Write DataArray as GeoTIFF. Requires rioxarray and a CRS already on `da`."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    crs = getattr(getattr(da, "rio", None), "crs", None)
    if crs is None:
        raise ValueError("save_geotiff: DataArray has no CRS — call da.rio.write_crs first")
    da.rio.to_raster(path, dtype="float32", compress="DEFLATE")
