# Data Acquisition Guide — Yamaguchi LUTHEA pipeline

> Audience: the person who will actually run the pipeline.
> Outcome: when every step in this document is done,
> `python yamaguchi/scripts/check_environment.py` prints all ✓ and you
> can run `luthea ingest-dw` / `luthea ingest-lst` without further setup.

The pipeline (Urban Climate version, with Yonago as second case city and
population + heatstroke + policy overlays) needs **nine** data assets from
you. Everything else is pulled automatically by code from Earth Engine.

| # | Asset | Source | Format | Target path | Mandatory? |
|---|---|---|---|---|---|
| 1 | AOI polygon of 山口市中心市街地 | hand-drawn in QGIS | GeoJSON | `yamaguchi/aoi/yamaguchi_center.geojson` | ✅ yes |
| 2 | JMA 山口観測所 日別値 2016–2025 | JMA obsdl portal | CSV (Shift-JIS) | `yamaguchi/outputs/raw/jma/yamaguchi_daily.csv` | ✅ yes |
| 3 | JMA 山口 AMeDAS 10分値 (summer 2016–2025) | JMA obsdl portal | CSV (Shift-JIS) | `yamaguchi/outputs/raw/jma/yamaguchi_10min.csv` | ✅ yes |
| 4 | AOI polygon of 米子市中心市街地 | hand-drawn in QGIS | GeoJSON | `yamaguchi/yonago/aoi/yonago_center.geojson` | ✅ yes |
| 5 | JMA 米子観測所 日別値 2016–2025 (station 68861) | JMA obsdl portal | CSV (Shift-JIS) | `yamaguchi/yonago/outputs/raw/jma/yonago_daily.csv` | ✅ yes |
| 6 | JMA 米子 AMeDAS 10分値 (summer 2016–2025) | JMA obsdl portal | CSV (Shift-JIS) | `yamaguchi/yonago/outputs/raw/jma/yonago_10min.csv` | ✅ yes |
| 7 | 250 m mesh 2020 census population for Yamaguchi + Tottori prefectures | e-Stat 統計 GIS | Shapefile | `yamaguchi/outputs/raw/estat/{yamaguchi,tottori}_250m_pop_2020/` | ✅ yes |
| 8 | 立地適正化計画区域データ (national A50, extract Yamaguchi + Yonago) | 国土数値情報 A50 | Shapefile (GML) | `yamaguchi/outputs/raw/mlit_a50/` | ✅ yes |
| 9 | FDMA 熱中症救急搬送 weekly reports 2016–2025 | 消防庁 熱中症情報 | XLSX + CSV | `yamaguchi/outputs/raw/fdma/heatstroke_YYYY.xlsx` | ✅ yes |

You will also need:
- **Earth Engine account + a Google Cloud project with Earth Engine API
  enabled** (free for research use; ~5 minutes to set up).
- A working Python environment (`mamba env create -f yamaguchi/env/environment.yml`).

Total operator time: **about 3.5 hours** for all nine assets. All manual
downloads combined take ~2.5 h; the QGIS AOI work adds ~1 h (30 min per
city). None of these portals expose a scriptable API; all require browser
navigation.

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

## Step 5 — Yonago (米子) AOI + JMA data (≈ 1 hour)

The Urban Climate submission mandates a second case city. Yonago
(米子市, Tottori) is picked for its shared "compact regional city +
onsen quarter + コンパクトシティ policy" profile with a **coastal**
morphology contrast to Yamaguchi's inland basin.

### 5.1 Draw Yonago AOI

1. In QGIS, jump to lat 35.428°, lon 133.331° (米子駅).
2. Add a new polygon layer (EPSG:4326) and draw a single polygon
   covering:
   - 米子駅 (south-east)
   - 皆生温泉 (north, at the coast)
   - 中心商店街 (角盤町 / 法勝寺町)
   - 米子城跡 (west)
   - extend ≥ 500 m beyond the outermost landmark
3. Export as GeoJSON to `yamaguchi/yonago/aoi/yonago_center.geojson`.
4. Sanity check area (target 8–15 km²):

   ```bash
   python -c "import geopandas as gpd; \
     g = gpd.read_file('yamaguchi/yonago/aoi/yonago_center.geojson').to_crs(6670); \
     print(f'area_km2={g.area.sum()/1e6:.2f}')"
   ```

### 5.2 Yonago JMA daily values 2016–2025

Same portal <https://www.data.jma.go.jp/risk/obsdl/index.php>. Station:
**米子 (観測所番号 68861)**. Columns and date range identical to
Step 3. Save to `yamaguchi/yonago/outputs/raw/jma/yonago_daily.csv`.

### 5.3 Yonago AMeDAS 10-min summer values

Same as Step 4 but station **米子 AMeDAS**. Save to
`yamaguchi/yonago/outputs/raw/jma/yonago_10min.csv`.

> **Pitfall**: the 米子 观測所 and the 米子 AMeDAS coexist under the same
> station name; make sure the "AMeDAS 観測所" toggle is on for Step 5.3.

---

## Step 6 — 250 m mesh 2020 census population (e-Stat) (≈ 30 min)

Provides the population denominators for the HIPI exposure overlay
(H7).

1. Open <https://www.e-stat.go.jp/gis> → **統計データダウンロード** →
   **国勢調査 → 2020年 → 4次メッシュ (500 m) or 5次メッシュ (250 m)**.
   Pick **5次メッシュ (250 m)** — the finer resolution matches our
   HIPI grid.
2. **項目 (variables)**: at minimum
   - 総人口 (total population)
   - 65 歳以上人口 (elderly, aged 65+)
   - 総世帯数 (households)
3. **地域 (region)**: select prefectures — one download per prefecture:
   - 山口県 → save shapefile bundle to
     `yamaguchi/outputs/raw/estat/yamaguchi_250m_pop_2020/`
   - 鳥取県 → save shapefile bundle to
     `yamaguchi/outputs/raw/estat/tottori_250m_pop_2020/`
4. Click **ダウンロード**, save the resulting `.zip`, unzip in place.
   Each unzipped folder should contain `MESH_2020_ppp.shp` (or similar
   canonical mesh filename) plus `.dbf`, `.shx`, `.prj`.
5. Sanity check:

   ```bash
   python -c "import geopandas as gpd; \
     g = gpd.read_file('yamaguchi/outputs/raw/estat/yamaguchi_250m_pop_2020'); \
     print(len(g), list(g.columns)[:8], g['MESH1_ID'].iloc[0] if 'MESH1_ID' in g.columns else '')"
   ```

> **Pitfall**: e-Stat sometimes distributes only 500 m mesh at
> prefecture level and 250 m mesh at national level. If the 250 m
> prefecture download is unavailable, take the national 250 m file and
> clip to prefecture — see `luthea.data_ingest.estat.clip_to_aoi`.

---

## Step 7 — MLIT 立地適正化計画 boundaries (A50) (≈ 15 min)

Provides the 都市機能誘導区域 polygons for the policy overlay (H8).

1. Open <https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A50-v1_0.html>.
2. Download the latest year available (as of 2026, fiscal year 2023 or
   later). One national ZIP (~200 MB).
3. Unzip to `yamaguchi/outputs/raw/mlit_a50/`. Expect files following
   `A50-YY_XX-jgd_1_UDA.shp` naming (XX = prefecture two-digit code:
   **35** for Yamaguchi, **31** for Tottori).
4. Sanity check:

   ```bash
   python -c "import geopandas as gpd; \
     g = gpd.read_file('yamaguchi/outputs/raw/mlit_a50/A50-YY_35-jgd_1_UDA.shp'); \
     print(len(g), 'polygons; first city:', g['A50_004'].iloc[0])"
   ```

> **Pitfall**: MLIT's `A50` is a schema-family. **UDA** shapefiles are
> 都市機能誘導区域, **JIA** are 居住誘導区域, **URA** are the outer
> 立地適正化計画区域. We need **UDA** for H8.

---

## Step 8 — FDMA 熱中症救急搬送 weekly reports (≈ 20 min)

Provides the annual prefecture-level heatstroke ambulance transport
counts for the correlation-only sub-analysis (§ 4.7).

1. Open <https://www.fdma.go.jp/disaster/heatstroke/post4.html>.
2. Under **過去のデータ一覧**, download the weekly PDF/XLSX bundle for
   each year 2016 (平成28) through 2025 (令和7). Ten files total.
3. Save into `yamaguchi/outputs/raw/fdma/` with names
   `heatstroke_YYYY.xlsx` (rename Reiwa/Heisei to Gregorian).
4. Sanity check will be done by the environment checker; the parser
   inside `luthea.data_ingest.fdma.load_prefecture_weekly` normalises
   the file layout.

> **Pitfall**: for early years (2016–2019) some releases are PDF-only.
> The parser tries `openpyxl` first and falls back to a printed error
> pointing you to `tabula-py` or manual OCR; do not delete the PDFs.

> **Limitation you must acknowledge**: FDMA reports data at
> **prefecture-week** granularity, not municipality-week. All heatstroke
> analyses in the manuscript are therefore *correlation-only* between
> the AOI-mean HSI and the whole-prefecture transport count. This is
> explicitly stated in § 6 Limitations of the manuscript.

---

## Step 9 — Run the environment check

After Steps 1–8 are done, run:

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
