"""Two-period transition identification (2016 ↔ 2025) at 30 m."""

from __future__ import annotations

import numpy as np
import xarray as xr

from ..config import DOMINANT_PLAND_MIN


def identify_transitions(ds_start: xr.Dataset, ds_end: xr.Dataset,
                         dominant_min: float = DOMINANT_PLAND_MIN) -> xr.Dataset:
    """Return a Dataset with:
       - dom_start, dom_end (int16 class codes);
       - transition_code (uint16, dom_start * 100 + dom_end);
       - valid (bool, dominant_pland ≥ dominant_min at both ends).
    """
    if ds_start.sizes != ds_end.sizes:
        raise ValueError("identify_transitions: start/end grids differ in shape")

    dom0 = ds_start["dominant"]
    dom1 = ds_end["dominant"]
    valid = (ds_start["dominant_pland"] >= dominant_min) & \
            (ds_end["dominant_pland"] >= dominant_min)

    code = (dom0.astype("uint16") * 100 + dom1.astype("uint16"))
    out = xr.Dataset({
        "dom_start": dom0,
        "dom_end": dom1,
        "transition_code": code,
        "valid": valid,
    })
    crs = getattr(getattr(ds_start, "rio", None), "crs", None)
    if crs is not None:
        out = out.rio.write_crs(crs, inplace=False)
    return out


def summarise_transitions(transitions: xr.Dataset) -> "pd.DataFrame":
    import pandas as pd
    df = transitions[["dom_start", "dom_end", "valid"]].to_dataframe().reset_index(drop=True)
    df = df[df["valid"]]
    grouped = (df.groupby(["dom_start", "dom_end"])
                 .size().rename("n_pixels").reset_index())
    grouped["transition_code"] = grouped["dom_start"].astype(int) * 100 + grouped["dom_end"].astype(int)
    return grouped.sort_values("n_pixels", ascending=False)
