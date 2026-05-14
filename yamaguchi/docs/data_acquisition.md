# Data Acquisition Guide — Yamaguchi LUTHEA pipeline

> Audience: the person who will actually run the pipeline.
> Outcome: when every step in this document is done,
> `python yamaguchi/scripts/check_environment.py` prints all ✓ and you
> can run `luthea ingest-dw` / `luthea ingest-lst` without further setup.

The pipeline needs **three** data assets from you. Everything else is
pulled automatically by code from Earth Engine or NASA Earthdata.

| # | Asset | Source | Format | Target path | Mandatory? |
|---|---|---|---|---|---|
| 1 | AOI polygon of 山口市中心市街地 | hand-drawn in QGIS | GeoJSON | `yamaguchi/aoi/yamaguchi_center.geojson` | ✅ yes |
| 2 | JMA 山口観測所 日別値 2016–2025 | JMA download portal | CSV (Shift-JIS / cp932) | `yamaguchi/outputs/raw/jma/yamaguchi_daily.csv` | ✅ yes |
| 3 | JMA 山口 AMeDAS 10分値 (summer 2016–2025) | JMA download portal | CSV (Shift-JIS / cp932) | `yamaguchi/outputs/raw/jma/yamaguchi_10min.csv` | ✅ yes |

You will also need:
- **Earth Engine account + a Google Cloud project with Earth Engine API
  enabled** (free for research use; ~5 minutes to set up).
- A working Python environment (`mamba env create -f yamaguchi/env/environment.yml`).

Total operator time: **about 2 hours**, dominated by the JMA CSV
download UI (it is form-based, not API-based).

---

## Step 1 — Earth Engine account & project (≈ 10 min)

1. Go to <https://earthengine.google.com/signup/> with a Google account
   and request research access. Approval is usually instant for academic
   email addresses; otherwise allow up to one business day.
2. Visit the Google Cloud Console (<https://console.cloud.google.com>),
   click **Select project → New project**, pick a memorable id (e.g.
   `yamaguchi-luthea`), and create it. Free-tier quota is fine for our
   AOI-clipped exports.
3. With the new project selected, open the API library
   (<https://console.cloud.google.com/apis/library>) and **Enable** the
   "Earth Engine API".
4. Install the CLI locally and authenticate:

   ```bash
   mamba activate luthea       # or source your venv
   earthengine authenticate    # opens a browser; paste the token back
   export EE_PROJECT=yamaguchi-luthea    # use the id from step 2
   echo 'export EE_PROJECT=yamaguchi-luthea' >> ~/.bashrc
   ```
5. Verify:

   ```bash
   python -c "import ee, os; ee.Initialize(project=os.environ['EE_PROJECT']); print(ee.Number(42).getInfo())"
   ```

   Expected output: `42`.

---

## Step 2 — Draw the AOI polygon in QGIS (≈ 30 min)

The AOI defines what the pipeline analyses. It must cover the central
district landmarks 山口駅 / 湯田温泉 / 中央商店街 / 県庁 and target a
total area of **8–15 km²**.

1. Install QGIS (free) from <https://qgis.org/en/site/forusers/download.html>.
2. Open QGIS → **Layer → Add Layer → Add XYZ Layer →
   OpenStreetMap** (or another basemap of your choice).
3. Zoom to Yamaguchi: search "山口駅" or use coordinates
   34.1745° N, 131.4733° E.
4. **Layer → Create Layer → New Temporary Scratch Layer**:
   - Geometry type: *Polygon*
   - CRS: **EPSG:4326 — WGS 84**
   - Name: `yamaguchi_center`
5. Toggle editing on (✏️ pencil icon), use the **Add Polygon Feature**
   tool, and click around a single polygon that contains:
   - 山口駅 to the south
   - 湯田温泉 to the west
   - 県庁 / 県立美術館 to the north
   - 中央商店街 (米屋町 / 道場門前) in the centre
   - extend ≥ 500 m beyond these landmarks so neighbourhood radii
     (100 / 300 / 500 m) stay inside the AOI for **every** focal pixel.
6. Right-click the layer → **Export → Save Features As…**:
   - Format: **GeoJSON**
   - File name: `yamaguchi_center.geojson`
   - CRS: **EPSG:4326**
   - Save into the `yamaguchi/aoi/` directory of this repository
     (overwrite the `.example.geojson` placeholder is fine).
7. Sanity check — area must fall in 8–15 km²:

   ```bash
   python -c "import geopandas as gpd; \
       gdf = gpd.read_file('yamaguchi/aoi/yamaguchi_center.geojson').to_crs(6670); \
       print(f'area_km2={gdf.area.sum() / 1e6:.2f}')"
   ```

> **Pitfall**: do *not* use a rectangular bounding box covering the
> whole prefecture — that explodes Landsat scene count and breaks the
> "compact central district" framing. Aim for ≈ 3 km × 3 km.

---

## Step 3 — Download JMA daily values 2016–2025 (≈ 30 min)

The JMA site has no clean API. Use the modern download portal:

1. Open <https://www.data.jma.go.jp/risk/obsdl/index.php> in a browser.
2. **地点を選ぶ** (Select station):
   - Click "山口" (region) → the prefecture map appears.
   - Select **山口 (観測所番号 81428)**.
   - Click **項目を選択** at the top to move to the next step.
3. **項目を選ぶ** (Select items):
   - Frequency: **日別値**.
   - Tick the following columns:
     - 平均気温 / 最高気温 / 最低気温
     - 降水量の合計
     - 日照時間
     - 平均風速 / 最大風速
     - 平均湿度 / 最小相対湿度
   - Click **期間を選択** at the top.
4. **期間を選ぶ** (Select date range):
   - **連続した期間で表示する** (continuous range), 2016-01-01 to 2025-12-31.
   - Click **表示オプション** if you want to disable the
     "観測機器変更の表示" toggles — keep the defaults for now.
5. Click **CSVファイルをダウンロード** at the top.
6. The browser downloads `data.csv` (Shift-JIS encoded). **Rename and
   move** to:

   ```
   yamaguchi/outputs/raw/jma/yamaguchi_daily.csv
   ```

7. Sanity check (the parser is encoding-aware):

   ```bash
   python -c "from luthea.data_ingest.jma import load_daily; \
       d = load_daily('yamaguchi/outputs/raw/jma/yamaguchi_daily.csv'); \
       print(d.index.min(), d.index.max(), len(d), list(d.columns))"
   ```

   You should see roughly `2016-01-01 ... 2025-12-31`, around 3 650 rows,
   columns including `t_max`, `precip_mm`, `sunshine_h`.

---

## Step 4 — Download AMeDAS 10-min values (summer 2016–2025) (≈ 45 min)

The 10-min values are needed only for overpass-time meteorology on the
summer scenes; you do not need the whole year, just June–September.

1. Same portal — <https://www.data.jma.go.jp/risk/obsdl/index.php>.
2. **地点を選ぶ**: choose AMeDAS station "山口" (the AMeDAS station
   coexists with the 観測所; pick the AMeDAS variant).
3. **項目を選ぶ**:
   - Frequency: **10分ごとの値**.
   - Tick: 気温, 風向・風速, 降水量, 相対湿度, 日照時間.
4. **期間を選ぶ**: the portal restricts 10-min downloads to short
   windows. You will need to repeat the download for each summer
   season; the easiest cadence is:
   - 2016-06-01 → 2016-09-30
   - 2017-06-01 → 2017-09-30
   - …
   - 2025-06-01 → 2025-09-30
   For each window, click **CSVファイルをダウンロード** and append the
   results.
5. After concatenating the 10 yearly CSVs into one file, save as:

   ```
   yamaguchi/outputs/raw/jma/yamaguchi_10min.csv
   ```

   A convenience: if the portal allows you to download multiple years
   in one shot for AMeDAS 10-min, do that and skip the concatenation.

6. Sanity check:

   ```bash
   python -c "from luthea.data_ingest.jma import load_amedas_10min; \
       d = load_amedas_10min('yamaguchi/outputs/raw/jma/yamaguchi_10min.csv'); \
       print(d.index.min(), d.index.max(), len(d), list(d.columns))"
   ```

   You should see roughly 6 × 30 × 24 × 6 ≈ 26 000 rows per summer,
   times 10 summers ≈ 260 000 rows total.

> **Pitfall**: the JMA 10-min download has been known to silently
> truncate windows longer than 6 months. Keep the windows at one summer
> each and stitch them together in pandas. The loader is tolerant of
> repeated header rows.

---

## Step 5 — Run the environment check

After Steps 1–4 are done, run:

```bash
python yamaguchi/scripts/check_environment.py
```

This script walks through every prerequisite and prints a checklist.
Every line should be `[✓]`. If any line is `[✗]`, the message tells you
which step of this document to revisit.

---

## Step 6 — First dry-run of the GEE ingestion

```bash
luthea ingest-lst --dry-run
```

Expected: a list of Landsat 8/9 scenes the pipeline will export, with
no Drive exports actually submitted. Typical output:

```
[ingest-lst] AOI=yamaguchi/aoi/yamaguchi_center.geojson years=2016-2025 dry_run=True
  30-60 scene(s) listed
[
  {"date": "20160712", "scene_id": "LC81120362016194LGN02", "task_id": null},
  ...
]
```

If the count is **0**, your AOI may not intersect the canonical Landsat
path/row for Yamaguchi — go back and verify that the AOI polygon is
genuinely over the city centre.

If the count is **> 100**, your AOI is too big — see Step 2 pitfall.

---

## Step 7 — Live ingestion

```bash
luthea ingest-dw                        # 10 Drive tasks for 2016-2025 LULC
luthea ingest-lst                       # 30-60 Drive tasks for Landsat LST
```

After all Drive tasks complete (Earth Engine sends an email; usually
≤ 30 min), download from Google Drive into:

```
yamaguchi/outputs/lulc/dw_lulc_YYYY.tif   (10 files)
yamaguchi/outputs/lst/lst_YYYYMMDD_*.tif  (30-60 files)
```

---

## Frequently-asked questions

**Q1. Do I need to obtain ECOSTRESS data?**
No — ECOSTRESS is only an *auxiliary* diurnal cross-check (see
manuscript § 6.3 footnote). The headline LUTHI uses Landsat alone. You
can add ECOSTRESS later if you want a robustness panel in the SI.

**Q2. Do I need the DEM separately?**
The pipeline pulls JAXA ALOS AW3D30 from Earth Engine automatically
during the covariate-extraction stage. Optional: if you want a sharper
5 m DEM for figures, download from the 国土地理院 基盤地図情報 service
and save as `yamaguchi/outputs/aux/dem_5m.tif`.

**Q3. Do I need to draw the second-city AOI now?**
Not yet. The methodology mandates a second case city (per Q1 method-first
lock), but the second-city replication is the *last* step. You can run
the entire Yamaguchi pipeline first and only return to draw the second
AOI when you are about to write § 4.7 of the manuscript.

**Q4. What if the JMA portal layout has changed and the menu names
differ?**
The data the pipeline needs is invariant: daily T_max / T_mean /
precip / sunshine / wind / RH for station 81428 over 2016-01-01 to
2025-12-31, plus the same variables at 10-min frequency for the
summer months. Any UI route that produces those CSVs is fine; the
loader auto-detects column names from the canonical Japanese headers
(see `JP_DAILY_COLUMN_MAP` in `luthea/data_ingest/jma.py`).

**Q5. The AOI polygon I drew is in a different CRS / I forgot to
specify EPSG:4326.**
Open the file in QGIS, right-click → Export → Save Features As… with
CRS set to EPSG:4326 and overwrite. The pipeline assumes WGS84 inputs.

**Q6. Can I use a different station id, e.g. for the secondary city?**
Yes — edit `JMA_STATION_ID` in `yamaguchi/src/luthea/config.py` (or
pass it explicitly to the loader). The default 81428 corresponds to
Yamaguchi.

---

## Troubleshooting cheatsheet

| Symptom | Likely cause | Fix |
|---|---|---|
| `earthengine authenticate` opens browser but never returns | proxy or paste error | retry; or `earthengine authenticate --quiet --auth-mode=notebook` |
| `ee.Initialize()` raises `EEException: Earth Engine client library not initialized` | missing `EE_PROJECT` env var | `export EE_PROJECT=<your-project-id>` |
| `load_daily` returns 0 rows | wrong encoding or wrong portal frequency | verify file is Shift-JIS; re-download with frequency = 日別値 |
| `luthea ingest-lst --dry-run` returns 0 scenes | AOI outside Landsat coverage | confirm AOI is over Yamaguchi (lon ≈ 131.47, lat ≈ 34.17) |
| Drive export task fails with quota error | concurrent task cap | wait for some to finish or split year range |
| `load_amedas_10min` raises "could not locate 年月日時分" | the file is the daily, not the 10-min variant | re-download with frequency = 10分ごとの値 |
