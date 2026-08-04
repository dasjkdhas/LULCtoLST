"""Tests for typical/extreme day selection."""

import pandas as pd

from luthea.lst.selection import label_days


def _row(t_max, sunshine_h=10.0, wind=1.0, precip=0.0, cumrain=0.0, cloud=0.0):
    return dict(t_max=t_max, sunshine_h=sunshine_h, overpass_wind=wind,
                precip_mm=precip, cumrain_48h=cumrain, scene_cloud_pct=cloud)


def test_label_days_distinguishes_typical_and_extreme():
    df = pd.DataFrame([
        _row(31.5),                # typical
        _row(36.0),                # extreme
        _row(28.0),                # neither (too cool)
        _row(31.0, sunshine_h=5),  # typical fails sunshine
        _row(31.0, precip=2.0),    # rain disqualifies
        _row(36.0, wind=5.0),      # windy disqualifies extreme
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
    # No scene may ever occupy both strata.
    assert not (out["is_typical"] & out["is_extreme"]).any()


def test_label_days_missing_column_raises():
    import pytest
    with pytest.raises(ValueError):
        label_days(pd.DataFrame({"t_max": [30.0]}))
