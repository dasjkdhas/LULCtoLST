"""Tests for typical/extreme day selection."""

import pandas as pd
import pytest

from luthea.lst.selection import label_days, retrieval_valid


def _row(t_max, sunshine_h=10.0, wind=1.0, precip=0.0, cumrain=0.0, cloud=0.0):
    return dict(t_max=t_max, sunshine_h=sunshine_h, overpass_wind=wind,
                precip_mm=precip, cumrain_48h=cumrain, scene_cloud_pct=cloud)


def test_label_days_distinguishes_typical_and_extreme():
    df = pd.DataFrame([
        _row(31.5),                # typical (真夏日)
        _row(36.0),                # extreme (猛暑日)
        _row(28.0),                # neither — below 真夏日
        _row(31.0, precip=2.0),    # wet surface disqualifies
        _row(31.0, cloud=40.0),    # AOI clouded out
        _row(31.0, cumrain=20.0),  # surface still wet from 48 h rain
    ])
    out = label_days(df)
    assert out["is_typical"].tolist() == [True, False, False, False, False, False]
    assert out["is_extreme"].tolist() == [False, True, False, False, False, False]


def test_jma_official_bands_are_contiguous_and_exclusive():
    """Scenario strata follow the JMA categories 真夏日 (>=30) and 猛暑日
    (>=35). The bands must leave no dead zone and must not overlap:
    a 34 °C day is typical, a 35 °C day is extreme only."""
    df = pd.DataFrame([
        _row(30.0),   # lower edge of 真夏日 -> typical
        _row(34.0),   # would have fallen in the old 33-35 dead zone
        _row(34.9),
        _row(35.0),   # 猛暑日 boundary -> extreme only
        _row(29.9),   # below 真夏日 -> neither
    ])
    out = label_days(df)
    assert out["is_typical"].tolist() == [True, True, True, False, False]
    assert out["is_extreme"].tolist() == [False, False, False, True, False]
    assert not (out["is_typical"] & out["is_extreme"]).any()


def test_sunshine_and_wind_do_not_screen_by_default():
    """Sunshine and wind are regressed out during weather normalisation,
    so screening on them as well would double-count. A low-sunshine,
    breezy but cloud-free and dry scene must still be usable."""
    df = pd.DataFrame([_row(32.0, sunshine_h=2.0, wind=9.0)])
    out = label_days(df)
    assert bool(out["is_typical"].iloc[0])


def test_strict_mode_reinstates_the_original_conjunction():
    """The supplement reports sensitivity to the stricter screen."""
    df = pd.DataFrame([
        _row(32.0, sunshine_h=2.0, wind=1.0),   # fails sunshine
        _row(32.0, sunshine_h=10.0, wind=9.0),  # fails wind
        _row(32.0, sunshine_h=10.0, wind=1.0),  # passes both
    ])
    out = label_days(df, strict=True)
    assert out["is_typical"].tolist() == [False, False, True]


def test_retrieval_valid_isolates_the_unfixable_conditions():
    df = pd.DataFrame([
        _row(32.0),                       # clean
        _row(32.0, precip=1.0),           # wet
        _row(32.0, cloud=99.0),           # clouded
        _row(32.0, cumrain=50.0),         # antecedent rain
        _row(32.0, sunshine_h=0.0, wind=20.0),  # normalisable, so still valid
    ])
    assert retrieval_valid(df).tolist() == [True, False, False, False, True]


def test_label_days_missing_column_raises():
    with pytest.raises(ValueError):
        label_days(pd.DataFrame({"t_max": [30.0]}))


def test_strict_mode_requires_the_extra_columns():
    df = pd.DataFrame([{
        "t_max": 32.0, "precip_mm": 0.0,
        "cumrain_48h": 0.0, "scene_cloud_pct": 0.0,
    }])
    label_days(df)                       # fine in default mode
    with pytest.raises(ValueError):
        label_days(df, strict=True)      # needs sunshine_h / overpass_wind
