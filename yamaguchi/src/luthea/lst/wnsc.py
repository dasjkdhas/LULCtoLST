"""Weather-Normalised Summer LST Composite.

WNSC_y(p) = median{ LST_norm(p, d) : d ∈ typical_days(y) }
Extreme variant uses extreme_days(y).
"""

from __future__ import annotations

from pathlib import Path

import xarray as xr


def composite_year(normalised_scenes: list[xr.DataArray]) -> xr.DataArray:
    """Pixel-wise median across one year's typical (or extreme) scenes.

    NaN-aware: pixels with < 2 valid scenes return NaN to avoid spurious medians.
    """
    raise NotImplementedError


def save_geotiff(da: xr.DataArray, path: Path) -> None:
    raise NotImplementedError
