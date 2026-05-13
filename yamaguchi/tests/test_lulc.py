"""Tests for LULC aggregation and transition identification."""

import numpy as np
import xarray as xr

from luthea.lulc.aggregate import aggregate_to_30m
from luthea.lulc.transitions import identify_transitions


def _make_label_grid(blocks_h=2, blocks_w=2, factor=3, seed=0):
    rng = np.random.default_rng(seed)
    labels = rng.integers(0, 3, size=(blocks_h * factor, blocks_w * factor))
    return xr.DataArray(labels.astype("int16"),
                        dims=("y", "x"),
                        coords={"y": np.arange(blocks_h * factor),
                                "x": np.arange(blocks_w * factor)})


def test_aggregate_to_30m_pland_sums_to_one():
    da = _make_label_grid(blocks_h=4, blocks_w=4)
    ds = aggregate_to_30m(da, n_classes=3, factor=3)
    pland_sum = sum(ds[f"PLAND_{k}"] for k in range(3))
    assert np.allclose(pland_sum.values, 1.0)


def test_aggregate_to_30m_dominant_argmax():
    labels = np.zeros((3, 3), dtype="int16")
    labels[0, 0] = 1
    labels[0, 1] = 1
    da = xr.DataArray(labels, dims=("y", "x"),
                      coords={"y": [0, 1, 2], "x": [0, 1, 2]})
    ds = aggregate_to_30m(da, n_classes=3, factor=3)
    # 7 zeros, 2 ones, 0 twos → dominant = 0
    assert int(ds["dominant"].values.item()) == 0


def test_identify_transitions_codes():
    da = _make_label_grid(blocks_h=4, blocks_w=4, seed=1)
    ds0 = aggregate_to_30m(da, n_classes=3, factor=3)
    ds1 = aggregate_to_30m(_make_label_grid(blocks_h=4, blocks_w=4, seed=2),
                           n_classes=3, factor=3)
    t = identify_transitions(ds0, ds1, dominant_min=0.0)
    expected = ds0["dominant"].astype("uint16") * 100 + ds1["dominant"].astype("uint16")
    assert np.array_equal(t["transition_code"].values, expected.values)
