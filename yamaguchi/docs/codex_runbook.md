# Codex Runbook — data acquisition for the LUTHEA Yamaguchi + Yonago pipeline

> **Audience**: this file is written for a coding agent (codex) that has
> **browser / computer-use** tools. It is *not* addressed to the human
> operator. The human operator's role is limited to two moments: (a)
> logging in to services when prompted with 🔑; (b) triggering this
> runbook once for the whole session.
>
> **Success criterion**: at the end of this runbook, running
> `python yamaguchi/scripts/check_environment.py` from the repository
> root prints all `[✓]` lines and exits 0.

---

## 0. Legend

| Marker | Meaning |
|---|---|
| ✅ | Fully automatable. No human intervention. |
| 🔑 | **Pause here.** Ask the human to complete a login or CAPTCHA in the same browser session, then continue. |
| ⚠️ | Automation may fail; a manual fallback is documented in-line. |

Every step has a **Success check** — a shell command whose exit status
and/or output confirms the step succeeded. Codex must run the success
check before proceeding to the next step. If the check fails, retry the
step up to two times, then stop and print the failure to the human.

---

## 1. Prerequisites

### 1.1 Environment (✅ one-time)

```bash
cd $(git rev-parse --show-toplevel)               # repo root: LULCtoLST/
mamba env create -f yamaguchi/env/environment.yml || conda env create -f yamaguchi/env/environment.yml
mamba activate luthea                             # or conda activate
pip install -e yamaguchi/                         # editable install
pip install requests beautifulsoup4               # for scripts/fetch_fdma.py
```

**Success check:**
```bash
python -c "import luthea; print('luthea', luthea.__version__)"
# expected: luthea 0.1.0
```

### 1.2 Earth Engine credentials (🔑 human)

```bash
earthengine authenticate                          # opens browser
# 🔑 HUMAN: sign in with Google, paste the verification token back into the terminal
export EE_PROJECT=<google-cloud-project-id-with-EE-API-enabled>
```

**Success check:**
```bash
python -c "import ee, os; ee.Initialize(project=os.environ['EE_PROJECT']); print(ee.Number(42).getInfo())"
# expected: 42
```

If this fails, ask the human to visit
<https://console.cloud.google.com/apis/library/earthengine.googleapis.com>
and enable Earth Engine API for their project.

---

## 2. AOI polygons — automatable, no browser (✅)

```bash
python yamaguchi/scripts/build_aoi_polygons.py --force
```

**Success check:**
```bash
python -c "import geopandas as gpd; \
  for p in ['yamaguchi/aoi/yamaguchi_center.geojson', 'yamaguchi/yonago/aoi/yonago_center.geojson']: \
    g = gpd.read_file(p).to_crs(6670); \
    print(p, f'area_km2={g.area.sum()/1e6:.2f}')"
# expected: both areas in 8-15 km²
```

Do **not** use QGIS here. The Python script builds both GeoJSONs from
hard-coded landmark bounding boxes; if the human later refines them
manually, that refined version takes precedence on the next run
(script skips existing non-script-generated files by default).

---

## 3. JMA daily values — Yamaguchi station 81428 (⚠️🔑)

**Target file:** `yamaguchi/outputs/raw/jma/yamaguchi_daily.csv`
**Portal:** <https://www.data.jma.go.jp/risk/obsdl/index.php>

### 3.1 Browser navigation (computer-use)

1. Navigate to the portal URL above.
2. Click **地点を選ぶ**.
3. In the region selector, click **山口** (prefecture selector on the
   left, then the map on the right).
4. Click the point labelled **山口** with 観測所番号 **81428**. A green
   marker appears.
5. Click **項目を選択** (top nav).
6. Under **データの種類**, select **日別値**.
7. Tick each of the following boxes:
   - 平均気温
   - 最高気温
   - 最低気温
   - 降水量の合計
   - 日照時間
   - 平均風速
   - 最大風速
   - 平均湿度
   - 最小相対湿度
8. Click **期間を選択** (top nav).
9. Under **連続した期間で表示する**, set:
   - 開始年月日: **2016 / 1 / 1**
   - 終了年月日: **2025 / 12 / 31**
10. Click **CSVファイルをダウンロード** (top-right button).
11. 🔑 If the portal asks for consent or CAPTCHA, wait for the human.
12. Save the returned CSV. Move it to
    `yamaguchi/outputs/raw/jma/yamaguchi_daily.csv`.

### 3.2 Success check

```bash
python -c "from luthea.data_ingest.jma import load_daily; \
  d = load_daily('yamaguchi/outputs/raw/jma/yamaguchi_daily.csv'); \
  print(d.index.min(), d.index.max(), len(d), 't_max' in d.columns)"
# expected: 2016-01-01 ... 2025-12-31 True   (row count ≈ 3650)
```

If the file parses but the row count is < 3000, some columns are
missing — repeat Step 3 § 7 with the exact tick-list.

---

## 4. JMA AMeDAS 10-min values — Yamaguchi (⚠️🔑)

**Target file:** `yamaguchi/outputs/raw/jma/yamaguchi_10min.csv`

The portal enforces short download windows for 10-min data. Loop over
years 2016–2025, one summer at a time, and stitch the CSVs.

### 4.1 Browser navigation (loop)

For each year Y in {2016, 2017, ..., 2025}:

1. Same portal.
2. **地点を選ぶ** → **山口 AMeDAS** (not the 観測所).
3. **項目を選ぶ** → frequency **10分ごとの値** → tick:
   - 気温
   - 降水量
   - 風向・風速
   - 相対湿度
   - 日照時間
4. **期間を選ぶ** → 開始 **Y / 6 / 1** → 終了 **Y / 9 / 30**.
5. Click **CSVファイルをダウンロード**.
6. Save as `yamaguchi/outputs/raw/jma/yamaguchi_10min_{Y}.csv`.

### 4.2 Concatenate

```bash
python -c "
import pandas as pd, glob, sys
frames = []
for p in sorted(glob.glob('yamaguchi/outputs/raw/jma/yamaguchi_10min_*.csv')):
    with open(p, 'rb') as f:
        head = f.read(4)
    enc = 'utf-8-sig' if head.startswith(b'\\xef\\xbb\\xbf') else 'cp932'
    frames.append(pd.read_csv(p, encoding=enc, header=None))
out = pd.concat(frames, ignore_index=True)
out.to_csv('yamaguchi/outputs/raw/jma/yamaguchi_10min.csv', index=False, header=False, encoding='cp932')
print('stitched', len(out), 'rows')
"
```

### 4.3 Success check

```bash
python -c "from luthea.data_ingest.jma import load_amedas_10min; \
  d = load_amedas_10min('yamaguchi/outputs/raw/jma/yamaguchi_10min.csv'); \
  print(d.index.min(), d.index.max(), len(d))"
# expected: ~260 000 rows spanning 2016 summer to 2025 summer
```

---

## 5. JMA — Yonago station 68861 (⚠️🔑)

Repeat Steps 3 and 4 **verbatim**, substituting:

| Original | Replacement |
|---|---|
| 山口 (81428) | **米子 (68861)** |
| 山口 AMeDAS | **米子 AMeDAS** |
| `yamaguchi_daily.csv` | `yonago_daily.csv` |
| `yamaguchi_10min_*.csv` | `yonago_10min_*.csv` |
| `yamaguchi/outputs/raw/jma/` | `yamaguchi/yonago/outputs/raw/jma/` |

**Success check** for both files:
```bash
python -c "from luthea.data_ingest.jma import load_daily, load_amedas_10min; \
  d = load_daily('yamaguchi/yonago/outputs/raw/jma/yonago_daily.csv'); \
  a = load_amedas_10min('yamaguchi/yonago/outputs/raw/jma/yonago_10min.csv'); \
  print('daily', len(d), 'amedas', len(a))"
```

---

## 6. e-Stat 250 m mesh 2020 census — population (🔑)

**Target dir:** `yamaguchi/outputs/raw/estat/`
**Portal:** <https://www.e-stat.go.jp/gis>

### 6.1 Browser navigation

For each prefecture in {山口県 (Yamaguchi), 鳥取県 (Tottori)}:

1. Navigate to the portal.
2. Click **統計データダウンロード** in the left sidebar.
3. Click **国勢調査 → 2020年 → 5次メッシュ (250m)**. If 250 m is not
   available at prefecture granularity, use **500m メッシュ**; the
   downstream loader supports both.
4. In the **項目 (items)** panel tick:
   - 総人口
   - 65歳以上人口
   - 総世帯数
5. In the **地域 (region)** panel select **{prefecture}**.
6. Click **ダウンロード**.
7. 🔑 If e-Stat requires login (registration is free), wait for the
   human to complete it once — the session cookie persists for all
   subsequent downloads.
8. Save the ZIP to
   `yamaguchi/outputs/raw/estat/{prefecture_slug}_250m_pop_2020.zip`
   where `prefecture_slug` is `yamaguchi` or `tottori`.
9. Unzip in place into a same-named directory (without `.zip`).

### 6.2 Success check

```bash
python -c "from luthea.data_ingest.estat import load_mesh; \
  g = load_mesh('yamaguchi/outputs/raw/estat/yamaguchi_250m_pop_2020'); \
  print('yamaguchi mesh:', len(g), 'polygons; cols:', [c for c in g.columns if 'pop' in c.lower() or 'household' in c.lower()])"
# expected: several thousand polygons with total_pop / elderly_pop columns
```

Repeat for `tottori`.

---

## 7. MLIT A50 立地適正化計画 shapefile (✅ direct URL)

**Target dir:** `yamaguchi/outputs/raw/mlit_a50/`

### 7.1 Discover the current-year direct download URL

The MLIT NLFTP portal lists a national ZIP at the top of
<https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A50-v1_0.html>.

Codex should scrape the page to find the anchor whose text starts with
`全国` and whose href ends in `.zip`. If that scrape fails, hard-code
the current-year fallback URL — check the page header for the latest
fiscal year (令和 5 → 2023, 令和 6 → 2024).

```bash
python -c "
import re, requests, urllib.parse as up
r = requests.get('https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A50-v1_0.html',
                 headers={'User-Agent': 'luthea-fetcher/0.1'}, timeout=30)
r.encoding = r.apparent_encoding
m = re.search(r'href=\"([^\"]+A50[^\"]+\\.zip)\"[^>]*>[^<]*全国', r.text)
if not m: raise SystemExit('could not locate national A50 zip link — inspect the page')
url = up.urljoin('https://nlftp.mlit.go.jp/', m.group(1))
print(url)
" > /tmp/mlit_a50_url.txt
```

### 7.2 Download and unzip

```bash
URL=$(cat /tmp/mlit_a50_url.txt)
mkdir -p yamaguchi/outputs/raw/mlit_a50
curl -sSL -A 'luthea-fetcher/0.1' -o yamaguchi/outputs/raw/mlit_a50/A50.zip "$URL"
unzip -o -d yamaguchi/outputs/raw/mlit_a50 yamaguchi/outputs/raw/mlit_a50/A50.zip
```

### 7.3 Success check

```bash
ls yamaguchi/outputs/raw/mlit_a50/*_UDA.shp | head
# expected: shapefiles matching A50-YY_35-...UDA.shp (Yamaguchi) and A50-YY_31-...UDA.shp (Tottori)
```

---

## 8. FDMA weekly heatstroke workbooks 2016–2025 (⚠️)

**Target dir:** `yamaguchi/outputs/raw/fdma/`

### 8.1 Try the scripted downloader first

```bash
python yamaguchi/scripts/fetch_fdma.py --out yamaguchi/outputs/raw/fdma
```

If the script prints "Missing years: [...]" for some Reiwa era files,
proceed to Step 8.2 for those years only.

### 8.2 Manual browser fallback for missing years

For each missing year Y:

1. Navigate to <https://www.fdma.go.jp/disaster/heatstroke/post4.html>.
2. Find the anchor for the year (labelled 平成28年 for 2016 through
   令和7年 for 2025) — click the XLSX link.
3. If only PDF is available for that year, download the PDF; do **not**
   try to OCR. The parser tolerates missing years.
4. Save as `yamaguchi/outputs/raw/fdma/heatstroke_{Y}.xlsx` (or `.pdf`).

### 8.3 Success check

```bash
python -c "from luthea.data_ingest.fdma import annual_transports; \
  s = annual_transports('yamaguchi/outputs/raw/fdma', 'Yamaguchi'); \
  print(s)"
# expected: pd.Series indexed by year 2016..2025 with non-zero values for at least 7 of the 10 years
```

---

## 9. Final validation (✅)

```bash
python yamaguchi/scripts/check_environment.py
echo "exit=$?"
```

**Success = every line is `[✓]` and exit is `0`.**

If any line is `[✗]`, re-run the corresponding numbered step in this
runbook. The failing line always includes a `docs/data_acquisition.md`
step pointer for the human as a fallback.

---

## 10. Handing back to the pipeline

Only after Step 9 exits 0, proceed to:

```bash
luthea ingest-lst --dry-run                      # sanity-check Landsat scene count
luthea ingest-dw                                 # submit 10 Drive tasks (Dynamic World)
luthea ingest-lst                                # submit 30-60 Drive tasks (Landsat ST)
```

Then notify the human: data is in Drive; pipeline is ready to run once
Drive downloads land under `yamaguchi/outputs/lulc/` and `yamaguchi/outputs/lst/`.

---

## Appendix A — Directory layout after this runbook

```
yamaguchi/
├── aoi/yamaguchi_center.geojson              # Step 2
├── yonago/aoi/yonago_center.geojson          # Step 2
├── outputs/raw/
│   ├── jma/
│   │   ├── yamaguchi_daily.csv               # Step 3
│   │   ├── yamaguchi_10min.csv               # Step 4
│   │   └── (yamaguchi_10min_2016..2025.csv)  # Step 4 pre-concat
│   ├── estat/
│   │   ├── yamaguchi_250m_pop_2020/          # Step 6
│   │   └── tottori_250m_pop_2020/            # Step 6
│   ├── mlit_a50/                             # Step 7
│   │   ├── A50.zip
│   │   └── A50-*_35-*_UDA.shp                # Yamaguchi
│   │   └── A50-*_31-*_UDA.shp                # Tottori
│   └── fdma/
│       └── heatstroke_2016..2025.xlsx        # Step 8
└── yonago/outputs/raw/jma/                   # Step 5
    ├── yonago_daily.csv
    └── yonago_10min.csv
```

## Appendix B — What codex must NOT do

- Do not modify `yamaguchi/src/luthea/` code — it is already implemented.
- Do not attempt to download Dynamic World or Landsat rasters — that
  belongs to the `luthea ingest-*` step run after Step 9.
- Do not commit anything to git — the human handles version control.
- Do not run any `luthea` subcommand other than `--dry-run` unless
  Step 9 has passed.
