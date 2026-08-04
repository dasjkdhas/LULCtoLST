"""Tests for epoch-pooled WNSC compositing.

Motivated by the real Yamaguchi record: 18 cloud-screened Landsat scenes
across 2016-2025, with five single-scene years. Single-year compositing
collapses to NaN there, so the t0/t1 contrast is defined between
three-year epochs instead.
"""

from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from luthea.config import EPOCH_EARLY, EPOCH_LATE, EPOCH_MID
from luthea.lst.wnsc import composite_epoch, composite_year


def _scene(value: float, shape=(4, 4)) -> xr.DataArray:
    return xr.DataArray(
        np.full(shape, value, dtype=float),
        dims=("y", "x"),
        coords={"y": np.arange(shape[0]), "x": np.arange(shape[1])},
    )


# Actual per-year scene counts from the Yamaguchi ingest-lst dry run.
YAMAGUCHI_SCENES_PER_YEAR = {
    2016: 1, 2017: 2, 2018: 3, 2019: 1, 2020: 1,
    2021: 1, 2022: 1, 2023: 2, 2024: 2, 2025: 4,
}


def test_epochs_partition_the_study_window_without_overlap():
    allyears = set(EPOCH_EARLY) | set(EPOCH_LATE) | set(EPOCH_MID)
    assert allyears == set(range(2016, 2026))
    assert not (set(EPOCH_EARLY) & set(EPOCH_LATE))
    assert not (set(EPOCH_EARLY) & set(EPOCH_MID))
    assert not (set(EPOCH_LATE) & set(EPOCH_MID))


def test_single_year_composites_collapse_on_the_real_record():
    """Five Yamaguchi years contribute one scene each; composite_year with
    the default min_obs=2 must return all-NaN for those years. This is the
    failure mode that motivated epoch pooling."""
    lone_years = [y for y, n in YAMAGUCHI_SCENES_PER_YEAR.items() if n == 1]
    assert len(lone_years) == 5
    out = composite_year([_scene(30.0)], min_obs=2)
    assert bool(out.isnull().all())


def test_epoch_pooling_restores_coverage():
    """Pooling 2016-2018 gives six scenes, so the composite is defined."""
    scenes_by_year = {
        2016: [_scene(30.0)],
        2017: [_scene(31.0), _scene(32.0)],
        2018: [_scene(29.0), _scene(30.0), _scene(31.0)],
    }
    comp, prov = composite_epoch(scenes_by_year, EPOCH_EARLY)
    assert not bool(comp.isnull().any())
    assert prov["n_scenes"] == 6
    assert prov["scenes_per_year"] == {2016: 1, 2017: 2, 2018: 3}
    assert prov["sufficient"] is True
    # median of [29,30,30,31,31,32] = 30.5
    assert abs(float(comp.isel(y=0, x=0)) - 30.5) < 1e-9


def test_epoch_provenance_reports_missing_years():
    scenes_by_year = {2023: [_scene(33.0), _scene(34.0)]}
    comp, prov = composite_epoch(scenes_by_year, EPOCH_LATE)
    assert prov["scenes_per_year"] == {2023: 2, 2024: 0, 2025: 0}
    assert prov["n_scenes"] == 2
    assert prov["sufficient"] is True


def test_epoch_below_min_obs_is_masked_but_reported():
    scenes_by_year = {2016: [_scene(30.0)]}
    comp, prov = composite_epoch(scenes_by_year, EPOCH_EARLY, min_obs=2)
    assert prov["n_scenes"] == 1
    assert prov["sufficient"] is False
    assert bool(comp.isnull().all())


def test_empty_epoch_raises():
    with pytest.raises(ValueError):
        composite_epoch({}, EPOCH_EARLY)


def test_real_record_supports_both_contrast_epochs():
    """Sanity-check the actual scene counts against the epoch design."""
    early = sum(YAMAGUCHI_SCENES_PER_YEAR[y] for y in EPOCH_EARLY)
    late = sum(YAMAGUCHI_SCENES_PER_YEAR[y] for y in EPOCH_LATE)
    assert early == 6
    assert late == 8
    # Both comfortably exceed the two-scene floor before scenario splitting.
    assert early >= 2 and late >= 2
