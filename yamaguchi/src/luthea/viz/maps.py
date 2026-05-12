"""Common map styling helpers (colour ramps, scale bar, north arrow, basemap)."""

from __future__ import annotations


def style_lulc_cmap():
    """Return Dynamic World canonical colour map."""
    return {
        0: "#419BDF",  # water
        1: "#397D49",  # trees
        2: "#88B053",  # grass
        3: "#7A87C6",  # flooded vegetation
        4: "#E49635",  # crops
        5: "#DFC35A",  # shrub & scrub
        6: "#C4281B",  # built
        7: "#A59B8F",  # bare
        8: "#B39FE1",  # snow & ice
    }


def style_lst_cmap():
    return "inferno"
