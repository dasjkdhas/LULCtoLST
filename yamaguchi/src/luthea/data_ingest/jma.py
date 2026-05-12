"""JMA / AMeDAS data wrangling for Yamaguchi station.

The JMA download UI does not expose a clean API; treat raw CSVs as inputs.

Workflow:
  1. User manually downloads daily values and 10-min values from
     https://www.data.jma.go.jp/obd/stats/etrn/index.php
     (station: 山口, 観測所番号 81428).
  2. Save raw CSVs under yamaguchi/outputs/raw/jma/.
  3. Functions below normalise schema, parse Japanese headers,
     convert to UTC-aware timestamps, and join with Landsat overpass times.

Plan reference: Step 4 of the plan file.
"""

from __future__ import annotations
from pathlib import Path

import pandas as pd


JP_COLUMN_MAP = {
    "年月日": "date",
    "平均気温(℃)": "t_mean",
    "最高気温(℃)": "t_max",
    "最低気温(℃)": "t_min",
    "降水量の合計(mm)": "precip_mm",
    "日照時間(時間)": "sunshine_h",
    "平均風速(m/s)": "wind_mean_ms",
    "平均湿度(%)": "rh_mean_pct",
}


def load_daily(csv_path: Path) -> pd.DataFrame:
    """Read raw JMA daily-value CSV → normalised DataFrame indexed by date."""
    raise NotImplementedError


def load_amedas_10min(csv_path: Path) -> pd.DataFrame:
    """Read AMeDAS 10-min CSV → DataFrame with UTC-aware timestamps."""
    raise NotImplementedError


def overpass_meteo(daily: pd.DataFrame, amedas: pd.DataFrame,
                   overpass_times_utc: pd.Series) -> pd.DataFrame:
    """Nearest-neighbour merge of overpass instants with AMeDAS records;
    attach the corresponding daily T_max / precip / sunshine."""
    raise NotImplementedError
