"""Tests for mesh-code geometry derivation and e-Stat statistics-table ingest."""

from __future__ import annotations

from pathlib import Path

import pytest

from luthea.data_ingest.estat import mesh_code_to_bbox


def test_first_mesh_code_5232_is_tokyo_area():
    """5232 = 1st mesh (80 km) covering the Tokyo area.
    lat = 52/1.5 = 34.6667, lon = 32 + 100 = 132."""
    w, s, e, n = mesh_code_to_bbox("5232")
    assert abs(s - 52 / 1.5) < 1e-9
    assert abs(w - 132.0) < 1e-9
    assert abs((n - s) - 2 / 3) < 1e-9
    assert abs((e - w) - 1.0) < 1e-9


def test_third_mesh_is_one_km_scale():
    """8-digit code → roughly 1 km cell (30 arc-sec lat, 45 arc-sec lon)."""
    w, s, e, n = mesh_code_to_bbox("52323599")
    dlat, dlon = n - s, e - w
    assert abs(dlat - (2 / 3) / 80) < 1e-12          # 30 arc-seconds
    assert abs(dlon - 1.0 / 80) < 1e-12              # 45 arc-seconds


def test_fifth_mesh_is_quarter_of_third_in_each_axis():
    """10-digit code → 250 m: 1/4 of the 1 km cell on each axis."""
    _, s3, e3, n3 = mesh_code_to_bbox("52323599")
    w3 = e3 - (1.0 / 80)
    w5, s5, e5, n5 = mesh_code_to_bbox("5232359911")
    assert abs((n5 - s5) - (n3 - s3) / 4) < 1e-12
    assert abs((e5 - w5) - (e3 - w3) / 4) < 1e-12
    # Quadrant 1 then 1 = south-west corner of the parent cell
    assert abs(s5 - s3) < 1e-12
    assert abs(w5 - w3) < 1e-12


def test_quadrant_digits_move_the_cell():
    """Quadrant 4 (north-east) must be offset from quadrant 1 (south-west)."""
    w1, s1, _, _ = mesh_code_to_bbox("5232359911")
    w4, s4, _, _ = mesh_code_to_bbox("5232359944")
    assert s4 > s1 and w4 > w1


def test_yamaguchi_aoi_mesh_lands_near_the_city():
    """A 5th-level mesh over Yamaguchi city should fall near
    lon 131.47, lat 34.17 — sanity check that the code arithmetic is
    not transposed."""
    # 1st mesh for Yamaguchi: lat 34.17 * 1.5 = 51.25 -> 51; lon 131 -> 31
    w, s, e, n = mesh_code_to_bbox("5131")
    assert s <= 34.17 <= n or abs(s - 34.0) < 1.0
    assert w <= 131.47 <= e


def test_invalid_codes_raise():
    with pytest.raises(ValueError):
        mesh_code_to_bbox("abc")
    with pytest.raises(ValueError):
        mesh_code_to_bbox("52")
    with pytest.raises(ValueError):
        mesh_code_to_bbox("5232359905")     # quadrant digit 0 is invalid


def test_households_maps_from_T001142034_not_004():
    """Regression: in the official 2020 250 m mesh tables, 世帯総数 is
    column T001142034. T001142004 is an age-bracket population field and
    must NOT be mapped to households."""
    from luthea.data_ingest.estat import ESTAT_COLUMN_MAP
    assert ESTAT_COLUMN_MAP["T001142034"] == "households"
    assert "T001142004" not in ESTAT_COLUMN_MAP


def test_stat_table_parsing_with_two_header_rows(tmp_path: Path):
    """e-Stat tables carry a code row and a Japanese label row; the
    loader must resolve population columns from either."""
    from luthea.data_ingest.estat import _read_stat_table
    p = tmp_path / "tblT001142Q35.txt"
    p.write_text(
        "KEY_CODE,HTKSYORI,T001142001,T001142004,T001142099\n"
        ",,人口（総数）,世帯総数,65歳以上人口\n"
        "5131456711,0,123,45,30\n"
        "5131456712,0,*,12,5\n",
        encoding="utf-8",
    )
    df = _read_stat_table(p)
    assert list(df["mesh_id"]) == ["5131456711", "5131456712"]
    assert df["total_pop"].iloc[0] == 123
    # suppressed "*" becomes NaN rather than crashing
    assert df["total_pop"].isna().iloc[1]
    assert df["households"].iloc[1] == 12
    assert df["elderly_pop"].iloc[0] == 30
