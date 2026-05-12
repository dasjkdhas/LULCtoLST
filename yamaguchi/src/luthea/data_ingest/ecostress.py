"""Optional auxiliary: ECOSTRESS L2 LSTE for extreme-day diurnal sampling.

Two access paths:
  A. GEE: NASA/ECOSTRESS/L2T_LSTE/v002 (2018+).
  B. NASA Earthdata via `earthaccess`.

Plan reference: Step 3 (auxiliary) of the plan file.
"""

from __future__ import annotations
from pathlib import Path


def list_overpasses(date_start: str, date_end: str, aoi_geojson_path: Path) -> list[dict]:
    """Return [{datetime, granule_id, cloud_pct}, ...]."""
    raise NotImplementedError


def download_granule(granule_id: str, out_dir: Path) -> Path:
    raise NotImplementedError
