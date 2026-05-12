"""Typical / extreme summer day selection per Step 4 thresholds."""

from __future__ import annotations

import pandas as pd

from ..config import (CLOUD_AOI_MAX_PCT, CUMRAIN_48H_MAX_MM, EXT_TMAX_MIN,
                      NO_RAIN_MM, SUNSHINE_HOURS_MIN_EXT,
                      SUNSHINE_HOURS_MIN_TYP, TYP_TMAX_MAX, TYP_TMAX_MIN,
                      WIND_MAX_MS)


def label_days(daily: pd.DataFrame, cumrain_48h: pd.Series,
               overpass_wind: pd.Series, scene_cloud_pct: pd.Series) -> pd.DataFrame:
    """Return DataFrame with two boolean columns: is_typical, is_extreme.

    A day is `typical` iff
        TYP_TMAX_MIN <= t_max <= TYP_TMAX_MAX AND
        precip_mm == NO_RAIN_MM AND
        sunshine_h >= SUNSHINE_HOURS_MIN_TYP AND
        overpass_wind <= WIND_MAX_MS AND
        cumrain_48h <  CUMRAIN_48H_MAX_MM AND
        scene_cloud_pct < CLOUD_AOI_MAX_PCT.

    `extreme` swaps the t_max condition (>= EXT_TMAX_MIN) and uses
    SUNSHINE_HOURS_MIN_EXT.
    """
    raise NotImplementedError
