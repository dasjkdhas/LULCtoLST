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

import numpy as np
import pandas as pd


JP_DAILY_COLUMN_MAP = {
    "年月日": "date",
    "平均気温(℃)": "t_mean",
    "最高気温(℃)": "t_max",
    "最低気温(℃)": "t_min",
    "降水量の合計(mm)": "precip_mm",
    "日照時間(時間)": "sunshine_h",
    "平均風速(m/s)": "wind_mean_ms",
    "最大風速(m/s)": "wind_max_ms",
    "平均湿度(％)": "rh_mean_pct",
    "平均湿度(%)": "rh_mean_pct",
    "最小相対湿度(％)": "rh_min_pct",
    "最小相対湿度(%)": "rh_min_pct",
}

JP_AMEDAS_COLUMN_MAP = {
    "年月日時分": "datetime_local",
    "気温(℃)": "t_air",
    "降水量(mm)": "precip_mm",
    "風速(m/s)": "wind_ms",
    "風向": "wind_dir",
    "日照時間(分)": "sunshine_min",
    "相対湿度(％)": "rh_pct",
    "相対湿度(%)": "rh_pct",
}


def _read_jma_csv(path: Path) -> pd.DataFrame:
    """JMA CSVs are Shift-JIS with multi-row headers; the data block typically
    starts a few rows down. We try utf-8-sig first then cp932, scan the first
    rows for the canonical header keyword '年月日'."""
    path = Path(path)
    for encoding in ("utf-8-sig", "cp932", "shift_jis"):
        try:
            raw = path.read_text(encoding=encoding).splitlines()
            break
        except UnicodeDecodeError:
            continue
    else:
        raise UnicodeDecodeError("jma", b"", 0, 1, f"could not decode {path}")

    header_row = None
    for i, line in enumerate(raw[:10]):
        if "年月日" in line:
            header_row = i
            break
    if header_row is None:
        raise ValueError(f"could not locate header row containing 年月日 in {path}")

    return pd.read_csv(path, encoding=encoding, skiprows=header_row)


def load_daily(csv_path: Path) -> pd.DataFrame:
    df = _read_jma_csv(csv_path)
    keep = {k: v for k, v in JP_DAILY_COLUMN_MAP.items() if k in df.columns}
    df = df.rename(columns=keep)[list(keep.values())]
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.tz_localize(None)
    df = df.dropna(subset=["date"]).set_index("date").sort_index()
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["cumrain_48h"] = df["precip_mm"].rolling("48h").sum()
    return df


def load_amedas_10min(csv_path: Path) -> pd.DataFrame:
    df = _read_jma_csv(csv_path)
    keep = {k: v for k, v in JP_AMEDAS_COLUMN_MAP.items() if k in df.columns}
    df = df.rename(columns=keep)[list(keep.values())]
    df["datetime_local"] = pd.to_datetime(df["datetime_local"], errors="coerce")
    df = df.dropna(subset=["datetime_local"])
    df["datetime_utc"] = (df["datetime_local"]
                          .dt.tz_localize("Asia/Tokyo", nonexistent="shift_forward",
                                          ambiguous="NaT")
                          .dt.tz_convert("UTC"))
    df = df.set_index("datetime_utc").sort_index()
    for col in ("t_air", "wind_ms", "rh_pct", "precip_mm", "sunshine_min"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def overpass_meteo(daily: pd.DataFrame, amedas: pd.DataFrame,
                   overpass_times_utc: pd.Series) -> pd.DataFrame:
    """Nearest-neighbour merge of overpass instants with AMeDAS records;
    attach the corresponding daily T_max / precip / sunshine / cumrain_48h.

    `overpass_times_utc` is a Series of pandas Timestamps (tz-aware UTC),
    typically indexed by scene_id or date.
    """
    overpass = pd.DataFrame({"overpass_utc": pd.to_datetime(overpass_times_utc, utc=True)})
    overpass = overpass.sort_values("overpass_utc")

    near = pd.merge_asof(overpass, amedas.reset_index(),
                         left_on="overpass_utc", right_on="datetime_utc",
                         direction="nearest", tolerance=pd.Timedelta("15min"))

    daily_local = daily.copy()
    daily_local.index = daily_local.index.tz_localize("Asia/Tokyo").tz_convert("UTC")
    near["overpass_date_jst"] = (near["overpass_utc"]
                                 .dt.tz_convert("Asia/Tokyo").dt.normalize())
    daily_keyed = daily.copy()
    daily_keyed.index = pd.to_datetime(daily_keyed.index).tz_localize("Asia/Tokyo")
    near = near.join(daily_keyed, on="overpass_date_jst")
    return near.set_index(overpass.index)
