"""Best-effort downloader for FDMA weekly heatstroke workbook releases.

Run this script **on your own machine** (not inside the Claude Code
sandbox — the sandbox blocks fdma.go.jp at the proxy).

Usage:
    python yamaguchi/scripts/fetch_fdma.py --out yamaguchi/outputs/raw/fdma

What it does:
    1. Loads the FDMA past-data index page at
       https://www.fdma.go.jp/disaster/heatstroke/post4.html
    2. Extracts every XLSX / CSV / PDF link on that page.
    3. For each linked file, saves it under the target directory with a
       `heatstroke_<year>.<ext>` name inferred from the URL text or
       enclosing anchor text.
    4. Prints a summary of what was written, and any years still missing
       from the 2016–2025 required set.

If a year appears only as a PDF, keep the PDF — the manuscript
Limitations section explicitly acknowledges this. The parser in
`luthea.data_ingest.fdma` will read whichever XLSX years are present.

This script requires the `requests` and `beautifulsoup4` packages.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urljoin


INDEX_URL = "https://www.fdma.go.jp/disaster/heatstroke/post4.html"
YEARS_NEEDED = list(range(2016, 2026))
JP_ERA_TO_GREGORIAN = {
    "H28": 2016, "H29": 2017, "H30": 2018, "H31": 2019,
    "R01": 2019, "R1": 2019,
    "R02": 2020, "R2": 2020,
    "R03": 2021, "R3": 2021,
    "R04": 2022, "R4": 2022,
    "R05": 2023, "R5": 2023,
    "R06": 2024, "R6": 2024,
    "R07": 2025, "R7": 2025,
}
DOWNLOAD_EXTS = (".xlsx", ".xls", ".csv", ".pdf")


def _load_page(url: str) -> str:
    import requests
    resp = requests.get(url, headers={"User-Agent": "luthea-fetcher/0.1"},
                        timeout=30)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def _guess_year(link_text: str, href: str) -> int | None:
    combined = f"{link_text} {href}"
    m = re.search(r"(20\d{2})", combined)
    if m:
        return int(m.group(1))
    for era, greg in JP_ERA_TO_GREGORIAN.items():
        if era in combined:
            return greg
    m = re.search(r"令和\s*(\d{1,2})", combined)
    if m:
        return 2018 + int(m.group(1))
    m = re.search(r"平成\s*(\d{2})", combined)
    if m:
        return 1988 + int(m.group(1))
    return None


def scrape_links(html: str) -> list[tuple[int | None, str, str]]:
    """Return (year, anchor_text, absolute_url) for each downloadable link."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    out: list[tuple[int | None, str, str]] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        low = href.lower()
        if not any(low.endswith(ext) for ext in DOWNLOAD_EXTS):
            continue
        abs_url = urljoin(INDEX_URL, href)
        text = " ".join((a.get_text() or "").split())
        out.append((_guess_year(text, href), text, abs_url))
    return out


def _download(url: str, dest: Path) -> None:
    import requests
    with requests.get(url, stream=True, timeout=60,
                      headers={"User-Agent": "luthea-fetcher/0.1"}) as r:
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as fh:
            for chunk in r.iter_content(chunk_size=64 * 1024):
                fh.write(chunk)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path,
                   default=Path("yamaguchi/outputs/raw/fdma"),
                   help="Output directory")
    p.add_argument("--dry-run", action="store_true",
                   help="List planned downloads without fetching")
    args = p.parse_args(argv)

    try:
        html = _load_page(INDEX_URL)
    except Exception as exc:
        print(f"error: could not load {INDEX_URL}: {exc}", file=sys.stderr)
        print(
            "\nIf this fails with 403 or connection refused, you are probably\n"
            "running inside the Claude Code sandbox. Run this script on your\n"
            "own machine instead, or download the workbooks manually per\n"
            "docs/data_acquisition.md Step 8.", file=sys.stderr,
        )
        return 2

    links = scrape_links(html)
    if not links:
        print("no downloadable links found on the FDMA index page", file=sys.stderr)
        return 3

    fetched: dict[int, list[Path]] = {}
    for year, text, url in links:
        if year is None or year not in YEARS_NEEDED:
            continue
        ext = Path(url).suffix.lower()
        dest = args.out / f"heatstroke_{year}{ext}"
        print(f"  {year}  {ext}  {url}  →  {dest}")
        if args.dry_run:
            continue
        try:
            _download(url, dest)
            fetched.setdefault(year, []).append(dest)
        except Exception as exc:
            print(f"    failed: {exc}", file=sys.stderr)

    missing = [y for y in YEARS_NEEDED if y not in fetched] if not args.dry_run else []
    if missing:
        print(f"\nMissing years after fetch: {missing}", file=sys.stderr)
        print("  → download manually per docs/data_acquisition.md Step 8",
              file=sys.stderr)
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
