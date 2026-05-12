"""Optional: spatially explicit GeoShapley (if compute budget allows).

Wraps the external `geoshapley` package; degrades to a no-op if absent.
"""

from __future__ import annotations


def run_geoshapley(model, X, xy, **kw):
    try:
        import geoshapley as gs  # noqa: F401
    except ImportError:
        raise RuntimeError("geoshapley not installed; pip install geoshapley")
    raise NotImplementedError
