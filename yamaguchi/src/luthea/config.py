"""Project-wide constants. Edit before running the pipeline.

Coordinates:
- AOI working CRS uses JGD2011 / Japan Plane Rectangular CS Zone II (EPSG:6670)
  because Yamaguchi prefecture falls in Zone II per GSI specification.
- Storage CRS is WGS84 (EPSG:4326) for portability.
"""

from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[3]          # repo /home/user/LULCtoLST
PROJECT = ROOT / "yamaguchi"
AOI_DIR = PROJECT / "aoi"
OUT_DIR = PROJECT / "outputs"
FIG_DIR = PROJECT / "figures"
TAB_DIR = PROJECT / "tables"

# ── Study window ─────────────────────────────────────────────────────────
YEAR_START = 2016
YEAR_END = 2025
SUMMER_MONTHS = (7, 8)        # peak summer; June is 梅雨, September is typhoon
                              # season in western Japan, so both are excluded

# ── Epoch design ─────────────────────────────────────────────────────────
# The cloud-screened Landsat 8/9 record over the Yamaguchi AOI yields only
# 18 usable summer scenes across 2016–2025, and five individual years
# contribute a single scene each. Single-year WNSC composites therefore
# collapse to NaN under the min_obs = 2 guard, and would collapse further
# once stratified into typical / extreme scenarios.
#
# The contrast is consequently defined between three-year *epochs* rather
# than single years. This both restores statistical power and matches the
# manuscript's decadal framing.
#
#   t0 = 2016–2018   (6 scenes)
#   t1 = 2023–2025   (8 scenes)
#   mid = 2019–2022  (4 scenes; trend/robustness only, not in the contrast)
EPOCH_EARLY = (2016, 2017, 2018)
EPOCH_LATE = (2023, 2024, 2025)
EPOCH_MID = (2019, 2020, 2021, 2022)

# Minimum scenes required per (epoch × scenario) cell before a composite
# is considered valid; cells below this threshold are reported as NaN and
# flagged in the scene inventory.
MIN_SCENES_PER_EPOCH_SCENARIO = 2

# ── CRS ──────────────────────────────────────────────────────────────────
CRS_STORAGE = "EPSG:4326"
CRS_WORK = "EPSG:6670"        # JGD2011 / Japan Plane Rectangular CS II

# ── JMA / AMeDAS ─────────────────────────────────────────────────────────
JMA_STATION_NAME = "Yamaguchi"
JMA_STATION_ID = 81428        # 観測所番号 — verify before download
AMEDAS_STATION_ID = 81428     # if separate, override

# ── Landsat ──────────────────────────────────────────────────────────────
LANDSAT_PATH = 112
LANDSAT_ROW = 35              # verify against scene list for Yamaguchi
LANDSAT_ST_SCALE = 0.00341802
LANDSAT_ST_OFFSET = 149.0     # Kelvin; subtract 273.15 for Celsius

# ── Filtering thresholds (Step 4) ────────────────────────────────────────
TYP_TMAX_MIN, TYP_TMAX_MAX = 30.0, 33.0
EXT_TMAX_MIN = 35.0
NO_RAIN_MM = 0.0
SUNSHINE_HOURS_MIN_TYP = 8.0
SUNSHINE_HOURS_MIN_EXT = 9.0
WIND_MAX_MS = 3.0
CUMRAIN_48H_MAX_MM = 5.0
CLOUD_AOI_MAX_PCT = 5.0

# ── LULC aggregation (Step 6) ────────────────────────────────────────────
DW_NATIVE_RES_M = 10
LST_RES_M = 30
SUBPIXELS_PER_LST = (LST_RES_M // DW_NATIVE_RES_M) ** 2     # 9
DOMINANT_PLAND_MIN = 4 / 9                                  # 0.444…

# ── Multi-scale neighbourhood (Step 7) ───────────────────────────────────
NEIGHBOURHOOD_RADII_M = (100, 300, 500)

# ── Bootstrap (Step 8) ───────────────────────────────────────────────────
BOOTSTRAP_B = 1000
RNG_SEED = 20260512
