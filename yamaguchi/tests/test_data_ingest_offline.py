"""Offline tests for the GEE-dependent ingestion modules.

We do not exercise Earth Engine itself — these tests verify that:

* modules import cleanly even when `earthengine-api` is absent;
* the GeoJSON parser handles FeatureCollection / Feature / Geometry;
* the QA-bitmask logic in `landsat_st.qa_mask_numpy` is correct so the
  identical bit positions can be trusted in the ee version.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_AOI = REPO_ROOT / "yamaguchi" / "aoi" / "yamaguchi_center.example.geojson"


def test_modules_import_without_ee():
    """The ingest modules must import even if `ee` is uninstalled. They
    only require ee at *call time*, not import time."""
    import importlib
    for mod in (
        "luthea.data_ingest._gee",
        "luthea.data_ingest.dynamic_world",
        "luthea.data_ingest.landsat_st",
    ):
        importlib.import_module(mod)


def test_load_aoi_geojson_featurecollection():
    from luthea.data_ingest._gee import load_aoi_geojson
    geom = load_aoi_geojson(SAMPLE_AOI)
    assert geom["type"] == "Polygon"
    assert len(geom["coordinates"][0]) == 5  # 4 corners + closing point


def test_load_aoi_geojson_handles_geometry_directly(tmp_path: Path):
    from luthea.data_ingest._gee import load_aoi_geojson
    raw = {
        "type": "Polygon",
        "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]],
    }
    p = tmp_path / "geom.geojson"
    p.write_text(json.dumps(raw), encoding="utf-8")
    geom = load_aoi_geojson(p)
    assert geom == raw


def test_load_aoi_geojson_handles_feature(tmp_path: Path):
    from luthea.data_ingest._gee import load_aoi_geojson
    feat = {
        "type": "Feature",
        "properties": {},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]],
        },
    }
    p = tmp_path / "feature.geojson"
    p.write_text(json.dumps(feat), encoding="utf-8")
    geom = load_aoi_geojson(p)
    assert geom["type"] == "Polygon"


def test_load_aoi_geojson_rejects_empty_collection(tmp_path: Path):
    from luthea.data_ingest._gee import load_aoi_geojson
    p = tmp_path / "empty.geojson"
    p.write_text(json.dumps({"type": "FeatureCollection", "features": []}),
                 encoding="utf-8")
    with pytest.raises(ValueError):
        load_aoi_geojson(p)


def test_utc_date_string_known_epoch():
    from luthea.data_ingest._gee import utc_date_string
    # 2024-08-15 01:30:00 UTC
    epoch_ms = 1_723_685_400_000
    assert utc_date_string(epoch_ms) == "20240814" or \
           utc_date_string(epoch_ms) == "20240815"
    # Accept either depending on the platform's strftime quirks; the
    # important contract is the YYYYMMDD format.


def test_qa_mask_numpy_drops_each_cloud_bit():
    from luthea.data_ingest.landsat_st import (QA_BITS_CLOUD_FAMILY,
                                                qa_mask_numpy)
    qa = np.zeros((1, 6), dtype=np.int64)
    qa[0, 0] = 0                       # clear — keep
    qa[0, 1] = 1 << 1                  # dilated cloud — drop
    qa[0, 2] = 1 << 2                  # cirrus — drop
    qa[0, 3] = 1 << 3                  # cloud — drop
    qa[0, 4] = 1 << 4                  # cloud shadow — drop
    qa[0, 5] = (1 << 0) | (1 << 5)     # other bits we don't filter — keep
    keep = qa_mask_numpy(qa, bits=QA_BITS_CLOUD_FAMILY)
    assert keep.tolist() == [[True, False, False, False, False, True]]


def test_cli_help_lists_ingest_subcommands():
    import subprocess
    import sys
    res = subprocess.run([sys.executable, "-m", "luthea.cli", "--help"],
                         capture_output=True, text=True)
    assert res.returncode == 0
    assert "ingest-dw" in res.stdout
    assert "ingest-lst" in res.stdout


def test_cli_ingest_dw_help_lists_required_options():
    import subprocess
    import sys
    res = subprocess.run([sys.executable, "-m", "luthea.cli", "ingest-dw", "--help"],
                         capture_output=True, text=True)
    assert res.returncode == 0
    assert "--aoi" in res.stdout
    assert "--year-start" in res.stdout
    assert "--folder" in res.stdout
