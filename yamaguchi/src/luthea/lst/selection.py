"""Typical / extreme summer day selection.

Design principle — screening and normalisation must not double-count
--------------------------------------------------------------------
LUTHEA already regresses out the overpass-time meteorological vector
(T_air, RH, wind, cumulative sunshine) when it builds the
weather-normalised LST field (§ 3.3, Eq. 4-5). Screening scenes on those
same variables *and* normalising on them removes the same signal twice:
it costs an enormous share of an already thin Landsat record while
adding no inferential protection.

Screening therefore keeps only the conditions that normalisation
**cannot** repair:

* **AOI cloud fraction** — a masked pixel has no retrieval to correct.
* **Same-day precipitation** and **48 h antecedent rainfall** — a wet
  surface is in a different evaporative regime, which is a state change
  rather than a linear meteorological offset.

Everything else (air temperature at overpass, humidity, wind, sunshine)
is handled by the β̂ projection.

Scenario strata then follow the Japan Meteorological Agency's official
categories, so the contrast is defined by climatology rather than by
tuning:

* **typical** — 真夏日: ``TYP_TMAX_MIN <= T_max < TYP_TMAX_MAX`` (30-35 °C)
* **extreme** — 猛暑日: ``T_max >= EXT_TMAX_MIN`` (>= 35 °C)

The bands are contiguous and mutually exclusive.

A ``strict=True`` mode retains the original conjunction (sunshine and
wind screens included) so the sensitivity of every downstream estimate
to this choice can be reported in the supplement.
"""

from __future__ import annotations

import pandas as pd

from ..config import (CLOUD_AOI_MAX_PCT, CUMRAIN_48H_MAX_MM, EXT_TMAX_MIN,
                      NO_RAIN_MM, SUNSHINE_HOURS_MIN_EXT,
                      SUNSHINE_HOURS_MIN_TYP, TYP_TMAX_MAX, TYP_TMAX_MIN,
                      WIND_MAX_MS)


#: Columns that must be present regardless of mode.
REQUIRED_COLUMNS = ("t_max", "precip_mm", "cumrain_48h", "scene_cloud_pct")

#: Additionally required when ``strict=True``.
STRICT_ONLY_COLUMNS = ("sunshine_h", "overpass_wind")


def retrieval_valid(daily: pd.DataFrame) -> pd.Series:
    """The screening conjunction that weather normalisation cannot repair."""
    return (
        (daily["precip_mm"] == NO_RAIN_MM)
        & (daily["cumrain_48h"] < CUMRAIN_48H_MAX_MM)
        & (daily["scene_cloud_pct"] < CLOUD_AOI_MAX_PCT)
    )


def label_days(daily: pd.DataFrame, strict: bool = False) -> pd.DataFrame:
    """Annotate each row with ``is_typical`` / ``is_extreme`` booleans.

    Parameters
    ----------
    daily
        One row per candidate scene date. Required columns:
        ``t_max``, ``precip_mm``, ``cumrain_48h``, ``scene_cloud_pct``
        (the AOI cloud percentage, **not** the scene-wide CLOUD_COVER
        property). With ``strict=True``, ``sunshine_h`` and
        ``overpass_wind`` are required as well.
    strict
        Reinstate the sunshine and wind screens. Retained for the
        supplementary sensitivity analysis; not the headline setting,
        because both variables are already regressed out during weather
        normalisation.
    """
    required = REQUIRED_COLUMNS + (STRICT_ONLY_COLUMNS if strict else ())
    missing = [c for c in required if c not in daily.columns]
    if missing:
        raise ValueError(f"label_days: missing columns {missing}")

    base = retrieval_valid(daily)
    if strict:
        base = base & (daily["overpass_wind"] <= WIND_MAX_MS)

    out = daily.copy()
    # Half-open band so a day at exactly 35.0 °C is 猛暑日 only.
    typical = (
        base
        & (daily["t_max"] >= TYP_TMAX_MIN)
        & (daily["t_max"] < TYP_TMAX_MAX)
    )
    extreme = base & (daily["t_max"] >= EXT_TMAX_MIN)

    if strict:
        typical = typical & (daily["sunshine_h"] >= SUNSHINE_HOURS_MIN_TYP)
        extreme = extreme & (daily["sunshine_h"] >= SUNSHINE_HOURS_MIN_EXT)

    out["is_typical"] = typical
    out["is_extreme"] = extreme
    return out
