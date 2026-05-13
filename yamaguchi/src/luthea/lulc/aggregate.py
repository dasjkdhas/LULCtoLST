"""Step 6 — Aggregate 10 m Dynamic World to the 30 m LST grid.

For each 30 m cell we report PLAND_k for every class k, plus the dominant
class. Implementation uses a 3 × 3 block reduction on the integer label
raster (no per-pixel one-hot blow-up — keeps memory bounded).
"""

from __future__ import annotations

import numpy as np
import xarray as xr


def _block_pland(labels: np.ndarray, n_classes: int, factor: int) -> np.ndarray:
    h, w = labels.shape
    h2, w2 = h // factor, w // factor
    trimmed = labels[: h2 * factor, : w2 * factor]
    blocks = trimmed.reshape(h2, factor, w2, factor).transpose(0, 2, 1, 3).reshape(h2, w2, -1)
    out = np.zeros((n_classes, h2, w2), dtype="float32")
    block_size = factor * factor
    for k in range(n_classes):
        out[k] = (blocks == k).sum(axis=-1) / block_size
    return out


def aggregate_to_30m(dw_10m: xr.DataArray, n_classes: int = 9,
                     factor: int = 3) -> xr.Dataset:
    """Return a Dataset with PLAND_0 ... PLAND_{n-1} and `dominant` DataArrays
    on the 30 m grid derived from the 10 m label raster."""
    labels = dw_10m.fillna(-1).astype("int16").to_numpy()
    pland = _block_pland(labels, n_classes=n_classes, factor=factor)

    coarse_h, coarse_w = pland.shape[1:]
    y0 = dw_10m["y"].values[: coarse_h * factor].reshape(coarse_h, factor).mean(axis=1)
    x0 = dw_10m["x"].values[: coarse_w * factor].reshape(coarse_w, factor).mean(axis=1)

    arrays = {f"PLAND_{k}": xr.DataArray(pland[k], coords={"y": y0, "x": x0},
                                         dims=("y", "x"))
              for k in range(n_classes)}
    dominant = xr.DataArray(np.argmax(pland, axis=0).astype("int16"),
                            coords={"y": y0, "x": x0}, dims=("y", "x"))
    dominant_pland = xr.DataArray(np.max(pland, axis=0),
                                  coords={"y": y0, "x": x0}, dims=("y", "x"))
    ds = xr.Dataset({**arrays,
                     "dominant": dominant,
                     "dominant_pland": dominant_pland})
    crs = getattr(getattr(dw_10m, "rio", None), "crs", None)
    if crs is not None:
        ds = ds.rio.write_crs(crs, inplace=False)
    return ds
