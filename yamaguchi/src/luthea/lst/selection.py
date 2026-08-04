"""Typical / extreme summer day selection per Step 4 thresholds."""

from __future__ import annotations

import pandas as pd

from ..config import (CLOUD_AOI_MAX_PCT, CUMRAIN_48H_MAX_MM, EXT_TMAX_MIN,
                      NO_RAIN_MM, SUNSHINE_HOURS_MIN_EXT,
                      SUNSHINE_HOURS_MIN_TYP, TYP_TMAX_MAX, TYP_TMAX_MIN,
                      WIND_MAX_MS)


REQUIRED_COLUMNS = ("t_max", "precip_mm", "sunshine_h",
                    "overpass_wind", "cumrain_48h", "scene_cloud_pct")


def label_days(daily: pd.DataFrame) -> pd.DataFrame:
    """Annotate each row with is_typical, is_extreme booleans.

    Expected input columns (in addition to a DatetimeIndex):
        t_max, precip_mm, sunshine_h, overpass_wind, cumrain_48h, scene_cloud_pct
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in daily.columns]
    if missing:
        raise ValueError(f"label_days: missing columns {missing}")

    base = (
        (daily["precip_mm"] == NO_RAIN_MM)
        & (daily["overpass_wind"] <= WIND_MAX_MS)
        & (daily["cumrain_48h"] < CUMRAIN_48H_MAX_MM)
        & (daily["scene_cloud_pct"] < CLOUD_AOI_MAX_PCT)
    )

    out = daily.copy()
    # Half-open band [TYP_TMAX_MIN, TYP_TMAX_MAX) so that a day at exactly
    # 35.0 °C is 猛暑日 (extreme) only, never both strata at once.
    out["is_typical"] = (
        base
        & (daily["t_max"] >= TYP_TMAX_MIN)
        & (daily["t_max"] < TYP_TMAX_MAX)
        & (daily["sunshine_h"] >= SUNSHINE_HOURS_MIN_TYP)
    )
    out["is_extreme"] = (
        base
        & (daily["t_max"] >= EXT_TMAX_MIN)
        & (daily["sunshine_h"] >= SUNSHINE_HOURS_MIN_EXT)
    )
    return out
