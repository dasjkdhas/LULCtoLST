"""FDMA (消防庁) weekly heatstroke ambulance transport parser.

Data source: https://www.fdma.go.jp/disaster/heatstroke/post4.html
Granularity: **prefecture × week** — a hard limitation acknowledged in
the manuscript § 6 (Limitations). This module only *loads* the data; the
correlation analysis lives in `attribution.exposure.heatstroke_correlation`.

The FDMA release format has drifted over 2016–2025:
  - 2016–2019: PDF-only or embedded Excel tables inside PDF
  - 2020–2022: XLSX with per-prefecture columns
  - 2023–2025: XLSX with a fully normalised long schema

The loader normalises everything to a long DataFrame with columns
    [year, iso_week, prefecture, transports]
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


PREFECTURE_NAME_MAP = {
    "山口": "Yamaguchi", "山口県": "Yamaguchi",
    "鳥取": "Tottori",   "鳥取県": "Tottori",
    "岡山": "Okayama",   "岡山県": "Okayama",
    "広島": "Hiroshima", "広島県": "Hiroshima",
    "島根": "Shimane",   "島根県": "Shimane",
    # Extend as needed for adjacent prefectures.
}


def _read_workbook(path: Path) -> list[pd.DataFrame]:
    """Read every sheet of an FDMA workbook, returning each as a DataFrame."""
    try:
        book = pd.read_excel(path, sheet_name=None, header=None)
    except Exception as exc:
        raise RuntimeError(
            f"{path.name}: could not read as XLSX. If the file is a PDF, "
            "use tabula-py or manual conversion before rerunning."
        ) from exc
    return list(book.values())


def load_weekly_workbook(path: Path,
                         year: int | None = None,
                         prefectures: Iterable[str] | None = None
                         ) -> pd.DataFrame:
    """Parse one FDMA workbook and return a long DataFrame.

    Parameters
    ----------
    path : XLSX path.
    year : if omitted, inferred from the filename `heatstroke_YYYY.xlsx`.
    prefectures : subset to keep (default: retain everything the file
        contains that maps into `PREFECTURE_NAME_MAP`).
    """
    path = Path(path)
    if year is None:
        stem = path.stem
        year = int("".join(c for c in stem if c.isdigit())[:4])

    sheets = _read_workbook(path)
    rows: list[dict] = []
    for sheet in sheets:
        header_row = _locate_header_row(sheet)
        if header_row is None:
            continue
        headers = sheet.iloc[header_row].astype(str).tolist()
        body = sheet.iloc[header_row + 1:].reset_index(drop=True)
        for i, col_label in enumerate(headers):
            pref_key = _match_prefecture(col_label)
            if pref_key is None:
                continue
            if prefectures and pref_key not in prefectures:
                continue
            for j, val in body.iloc[:, i].items():
                if pd.isna(val):
                    continue
                try:
                    n = int(val)
                except (TypeError, ValueError):
                    continue
                rows.append({
                    "year": year,
                    "iso_week": int(j) + 1,
                    "prefecture": pref_key,
                    "transports": n,
                })
    return pd.DataFrame(rows).drop_duplicates(
        subset=["year", "iso_week", "prefecture"])


def _locate_header_row(sheet: pd.DataFrame) -> int | None:
    for idx in range(min(len(sheet), 10)):
        line = " ".join(str(v) for v in sheet.iloc[idx].astype(str))
        if "都道府県" in line or any(p in line for p in PREFECTURE_NAME_MAP):
            return idx
    return None


def _match_prefecture(label: str) -> str | None:
    label = str(label).strip()
    for jp, en in PREFECTURE_NAME_MAP.items():
        if label.startswith(jp) or label == en:
            return en
    return None


def annual_transports(dir_path: Path | str,
                      prefecture: str) -> pd.Series:
    """Sum weekly transports to an annual series for one prefecture.

    Reads every `heatstroke_YYYY.xlsx` under `dir_path`, extracts the
    named prefecture, and returns Series indexed by year (int)."""
    dir_path = Path(dir_path)
    rows: dict[int, int] = {}
    for p in sorted(dir_path.glob("heatstroke_*.xlsx")):
        try:
            df = load_weekly_workbook(p, prefectures={prefecture})
        except RuntimeError:
            continue
        if df.empty:
            continue
        y = int(df["year"].iloc[0])
        rows[y] = int(df["transports"].sum())
    return pd.Series(rows, name=f"transports_{prefecture}").sort_index()
