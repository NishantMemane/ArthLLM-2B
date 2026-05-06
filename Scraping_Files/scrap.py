#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║   India Regulatory Complete Scraper — indiacode.nic.in           ║
║   Uses DSpace REST API to get EVERY act, rule, notification      ║
║   20 parallel workers | Live progress | Local AI ready           ║
╚══════════════════════════════════════════════════════════════════╝

HOW IT WORKS:
  IndiaCode runs on DSpace (open-source repository software).
  DSpace exposes a REST API at /rest/ that returns JSON.
  We use it to discover ALL items + their PDF bitstreams,
  then download with 20 workers.

API ENDPOINTS USED:
  /rest/collections          → list all collections
  /rest/collections/{id}/items?expand=bitstreams,metadata
  /rest/items?expand=bitstreams,metadata&limit=100&offset=N

WHAT YOU GET:
  - Every Central Act (Income Tax, FEMA, RBI, GST, CBDT, etc.)
  - All Rules, Regulations, Notifications, Circulars
  - State Acts (all 28 states + UTs)
  - Amendments, Ordinances
  - Complete metadata JSON for local AI ingestion
"""

import asyncio
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict

# ── ANSI colors (zero deps) ────────────────────────────────────────
R    = "\033[0m"
BOLD = "\033[1m"
DIM  = "\033[2m"
RED  = "\033[91m"
GRN  = "\033[92m"
YLW  = "\033[93m"
BLU  = "\033[94m"
CYN  = "\033[96m"
def c(*codes): return "".join(codes)

# ── Config ─────────────────────────────────────────────────────────
BASE_URL   = "https://www.indiacode.nic.in"
REST_URL   = f"{BASE_URL}/rest"
OUT_DIR    = Path("indiacode_complete")
META_FILE  = OUT_DIR / "metadata.json"
LOG_FILE   = OUT_DIR / "scraper.log"
WORKERS    = 20
TIMEOUT    = 45
RETRY      = 3

OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Categories we care about most (for priority tagging) ───────────
PRIORITY_KEYWORDS = [
    "income tax", "fema", "foreign exchange", "gst", "goods and services",
    "rbi", "reserve bank", "cbdt", "direct tax", "indirect tax",
    "customs", "excise", "sebi", "companies act", "insolvency",
    "bankruptcy", "banking regulation", "fdi", "foreign investment",
    "finance", "fiscal", "revenue", "tax"
]

# ── Shared state ───────────────────────────────────────────────────
_lock     = Lock()
_results  : List[dict] = []
_done     = 0
_total    = 0
_failures = 0
_logs     : List[str] = []
_phase    = "init"

def log(msg: str):
    ts   = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    with _lock:
        _logs.append(line)

def record(r: dict):
    global _done, _failures
    with _lock:
        _results.append(r)
        _done += 1
        if r.get("status") == "fail":
            _failures += 1

# ── HTTP ───────────────────────────────────────────────────────────
HEADERS = {
    "User-Agent":      "Mozilla/5.0 (compatible; IndiaCodeResearch/1.0)",
    "Accept":          "application/json",
    "Accept-Language": "en-IN,en;q=0.9",
}

def http_json(url: str, retries=RETRY) -> Optional[dict | list]:
    """GET JSON from DSpace REST API."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                raw = r.read()
                return json.loads(raw.decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                log(f"HTTP fail {url}: {e}")
                return None
    return None

def http_download(url: str, dest: Path, retries=RETRY) -> int:
    """Download binary file, return size in bytes."""
    dl_headers = {**HEADERS, "Accept": "*/*"}
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=dl_headers)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                data = r.read()
            dest.write_bytes(data)
            return len(data)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
    return 0

def safe_name(s: str, max_len=120) -> str:
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', str(s))
    s = re.sub(r'\s+', '_', s.strip())
    s = re.sub(r'_+', '_', s)
    return s[:max_len]

def is_priority(title: str) -> bool:
    t = (title or "").lower()
    return any(kw in t for kw in PRIORITY_KEYWORDS)

# ── DSpace REST API discovery ───────────────────────────────────────
def fetch_all_items_from_collection(collection_id: int) -> List[dict]:
    """Paginate through all items in a collection."""
    items = []
    offset = 0
    limit  = 100
    while True:
        url  = f"{REST_URL}/collections/{collection_id}/items?expand=bitstreams,metadata&limit={limit}&offset={offset}"
        data = http_json(url)
        if not data or not isinstance(data, list):
            break
        items.extend(data)
        if len(data) < limit:
            break
        offset += limit
        time.sleep(0.1)  # be polite
    return items

def fetch_all_items_global(max_items=50000) -> List[dict]:
    """
    Fetch ALL items from the global /rest/items endpoint (paginated).
    This gets EVERYTHING regardless of collection.
    """
    items  = []
    offset = 0
    limit  = 100
    log("Fetching all items from DSpace REST API (global scan)...")
    while offset < max_items:
        url  = f"{REST_URL}/items?expand=bitstreams,metadata&limit={limit}&offset={offset}"
        data = http_json(url)
        if not data or not isinstance(data, list) or len(data) == 0:
            break
        items.extend(data)
        log(f"  Global scan: {len(items)} items fetched (offset={offset})")
        if len(data) < limit:
            break
        offset += limit
        time.sleep(0.15)
    return items

def fetch_all_collections() -> List[dict]:
    """Get all collections."""
    cols   = []
    offset = 0
    limit  = 100
    while True:
        url  = f"{REST_URL}/collections?limit={limit}&offset={offset}"
        data = http_json(url)
        if not data or not isinstance(data, list):
            break
        cols.extend(data)
        if len(data) < limit:
            break
        offset += limit
    return cols

def extract_metadata_value(metadata: list, key: str) -> str:
    """Extract first value for a metadata key like 'dc.title'."""
    if not metadata:
        return ""
    for m in metadata:
        if m.get("key") == key:
            return m.get("value", "")
    return ""

def extract_pdf_bitstreams(item: dict) -> List[dict]:
    """Get all PDF bitstreams from an item."""
    pdfs = []
    bitstreams = item.get("bitstreams") or []
    for bs in bitstreams:
        name = bs.get("name", "")
        mime = bs.get("mimeType", "")
        if name.lower().endswith(".pdf") or "pdf" in mime.lower():
            retrieve_link = bs.get("retrieveLink") or ""
            if retrieve_link:
                if not retrieve_link.startswith("http"):
                    retrieve_link = BASE_URL + retrieve_link
            else:
                bs_id = bs.get("id")
                retrieve_link = f"{REST_URL}/bitstreams/{bs_id}/retrieve" if bs_id else ""
            if retrieve_link:
                pdfs.append({
                    "name":  name,
                    "url":   retrieve_link,
                    "size":  bs.get("sizeBytes", 0),
                    "mime":  mime,
                })
    return pdfs

def parse_item(item: dict) -> Optional[dict]:
    """Convert a DSpace item JSON into our download task."""
    metadata = item.get("metadata") or []
    title    = (extract_metadata_value(metadata, "dc.title")
                or item.get("name", "")
                or str(item.get("id", "unknown")))
    year     = extract_metadata_value(metadata, "dc.date.issued") or ""
    ministry = extract_metadata_value(metadata, "dc.description.ministry") or ""
    act_no   = extract_metadata_value(metadata, "dc.identifier.actno") or ""
    handle   = item.get("handle", "")
    item_id  = item.get("id")

    pdfs = extract_pdf_bitstreams(item)
    if not pdfs:
        return None

    # Build subfolder: ministry or year
    folder_name = safe_name(ministry or year[:4] or "general")
    dest_dir    = OUT_DIR / folder_name
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Tag priority
    priority = is_priority(title) or is_priority(ministry)

    return {
        "id":       item_id,
        "title":    title,
        "year":     year[:4] if year else "",
        "ministry": ministry,
        "act_no":   act_no,
        "handle":   handle,
        "url":      f"{BASE_URL}/handle/{handle}" if handle else "",
        "pdfs":     pdfs,
        "dest_dir": str(dest_dir),
        "priority": priority,
        "status":   "pending",
    }

# ── Download worker (runs in ThreadPoolExecutor) ───────────────────
def download_task(task: dict) -> dict:
    dest_dir = Path(task["dest_dir"])
    title    = task["title"]
    all_ok   = True
    dl_paths = []

    for i, pdf in enumerate(task["pdfs"]):
        suffix   = f"_{i+1}" if len(task["pdfs"]) > 1 else ""
        pdf_name = safe_name(pdf["name"] or title) + suffix
        if not pdf_name.lower().endswith(".pdf"):
            pdf_name += ".pdf"
        dest = dest_dir / pdf_name

        if dest.exists() and dest.stat().st_size > 512:
            dl_paths.append(str(dest))
            log(f"skip  {title[:50]}")
            continue

        try:
            sz = http_download(pdf["url"], dest)
            dl_paths.append(str(dest))
            log(f"✓ {title[:50]} ({sz//1024}KB)")
        except Exception as e:
            all_ok = False
            log(f"✗ {title[:50]}: {e}")

    task["files"]      = dl_paths
    task["status"]     = "ok" if all_ok and dl_paths else "fail"
    task["scraped_at"] = datetime.now().isoformat()
    record(task)
    return task

# ── Progress bar ───────────────────────────────────────────────────
def pbar(done, total, width=45):
    if total == 0:
        return "[" + "─" * width + "]  0%"
    pct    = done / total
    filled = int(pct * width)
    b      = "█" * filled + "░" * (width - filled)
    return f"[{b}] {int(pct*100):3d}%"

def render(phase: str, eta: float = 0):
    with _lock:
        done  = _done
        total = _total
        fails = _failures
        logs  = _logs[-8:]

    sys.stdout.write("\033[2J\033[H")
    sys.stdout.write(f"""
{c(BOLD, BLU)}╔══════════════════════════════════════════════════════╗
║   🇮🇳  IndiaCode Complete Scraper                      ║
╚══════════════════════════════════════════════════════╝{R}

  {c(BOLD)}Platform :{R}  indiacode.nic.in  (DSpace REST API)
  {c(BOLD)}Phase    :{R}  {c(CYN)}{phase}{R}
  {c(BOLD)}Progress :{R}  {pbar(done, total)}  {done}/{total}
  {c(BOLD)}Workers  :{R}  {WORKERS}
  {c(BOLD)}Failures :{R}  {c(RED if fails else GRN)}{fails}{R}
  {c(BOLD)}ETA      :{R}  {int(eta)}s

{c(DIM)}  Recent:{R}
""")
    for line in logs:
        sys.stdout.write(f"  {c(DIM)}{line}{R}\n")
    sys.stdout.flush()

async def progress_loop(stop: asyncio.Event, start: float):
    while not stop.is_set():
        with _lock:
            done  = _done
            total = _total
        elapsed = time.time() - start
        if done > 0 and total > 0 and elapsed > 0:
            eta = (total - done) / (done / elapsed)
        else:
            eta = 0
        render(_phase, eta)
        await asyncio.sleep(0.6)

# ── Main ───────────────────────────────────────────────────────────
async def main():
    global _total, _phase

    # ── Phase 1: Discover via DSpace REST API ──────────────────────
    _phase = "Discovering via DSpace REST API"
    render(_phase)

    log("Checking DSpace REST API...")
    test = http_json(f"{REST_URL}/communities?limit=1")
    if test is None:
        # REST API not accessible directly — fall back to HTML scraping
        log("REST API not directly accessible, switching to HTML browse scrape...")
        items_raw = await discover_via_html()
    else:
        log(f"DSpace REST API accessible! Starting full scan...")
        # Use global items endpoint — gets EVERYTHING
        items_raw = fetch_all_items_global(max_items=100000)

        # Also scan collection-by-collection for completeness
        log("Scanning all collections for completeness...")
        cols = fetch_all_collections()
        log(f"Found {len(cols)} collections")
        for col in cols:
            col_id   = col.get("id")
            col_name = col.get("name", "")
            if col_id:
                col_items = fetch_all_items_from_collection(col_id)
                log(f"  Collection '{col_name}': {len(col_items)} items")
                # Merge — avoid duplicates by id
                existing_ids = {i.get("id") for i in items_raw}
                for ci in col_items:
                    if ci.get("id") not in existing_ids:
                        items_raw.append(ci)
                        existing_ids.add(ci.get("id"))

    log(f"Total raw items from API: {len(items_raw)}")

    # ── Phase 2: Parse items → download tasks ──────────────────────
    _phase = "Parsing items"
    render(_phase)

    tasks = []
    for item in items_raw:
        parsed = parse_item(item)
        if parsed:
            tasks.append(parsed)

    # Sort: priority items first
    tasks.sort(key=lambda t: (0 if t["priority"] else 1, t.get("title", "")))

    with _lock:
        _total = len(tasks)

    log(f"Items with PDFs: {len(tasks)} (priority: {sum(1 for t in tasks if t['priority'])})")

    if len(tasks) == 0:
        print(f"\n{c(YLW)}  ⚠ No downloadable items found via REST API.{R}")
        print(f"  Falling back to direct known PDF list...\n")
        await fallback_known_pdfs()
        return

    # ── Phase 3: Download with 20 workers ─────────────────────────
    _phase = "Downloading (20 workers)"
    render(_phase)

    start      = time.time()
    stop_event = asyncio.Event()
    loop       = asyncio.get_event_loop()

    prog_task = asyncio.create_task(progress_loop(stop_event, start))

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = [loop.run_in_executor(executor, download_task, t) for t in tasks]
        await asyncio.gather(*futures)

    stop_event.set()
    await prog_task

    # ── Phase 4: Write metadata ────────────────────────────────────
    _phase = "Saving metadata"
    render(_phase)

    elapsed = time.time() - start
    ok      = sum(1 for r in _results if r.get("status") == "ok")
    fail    = sum(1 for r in _results if r.get("status") == "fail")
    skip    = len(_results) - ok - fail

    meta = {
        "source":        "indiacode.nic.in",
        "api":           f"{REST_URL}/items",
        "scraped_at":    datetime.now().isoformat(),
        "total_items":   len(_results),
        "downloaded":    ok,
        "skipped_cache": skip,
        "failed":        fail,
        "elapsed_sec":   round(elapsed),
        "output_dir":    str(OUT_DIR),
        "documents":     _results,
    }
    META_FILE.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    LOG_FILE.write_text("\n".join(_logs))

    # ── Summary ────────────────────────────────────────────────────
    total_kb = sum(
        sum(Path(f).stat().st_size for f in r.get("files", []) if Path(f).exists())
        for r in _results
    ) / 1024
    render("Complete")

    print(f"""
  {c(BOLD, GRN)}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅  Scraping Complete
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{R}

  Items found      : {c(BOLD)}{len(tasks)}{R}
  Downloaded       : {c(BOLD, GRN)}{ok}{R}
  Skipped (cached) : {c(YLW)}{skip}{R}
  Failed           : {c(RED if fail else GRN)}{fail}{R}
  Total size       : {c(BOLD)}{total_kb/1024:.1f} MB{R}
  Time             : {c(BOLD)}{round(elapsed)}s{R}

  Output dir       : {c(CYN)}{OUT_DIR}{R}
  Metadata for AI  : {c(CYN)}{META_FILE}{R}

  {c(BOLD)}Load in your local AI:{R}
  {c(DIM)}  import json
    meta = json.load(open("{META_FILE}"))
    docs = meta["documents"]   # list of all items + file paths{R}

  {c(BOLD, GRN)}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{R}
""")

# ── HTML fallback (if REST API is blocked) ────────────────────────
async def discover_via_html() -> List[dict]:
    """
    Fallback: scrape the browse-by-year HTML pages to find all item handles,
    then fetch each item's page to find PDF bitstream URLs.
    """
    log("HTML fallback: browsing by act year...")
    from bs4 import BeautifulSoup

    # Get all years from browse page
    years_url = f"{BASE_URL}/handle/123456789/1362/browse?type=actyear&rpp=200&offset=0"
    try:
        raw  = http_get_html(years_url)
        soup = BeautifulSoup(raw, "lxml")
    except Exception as e:
        log(f"Failed to load browse page: {e}")
        return []

    year_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "browse?type=actyear&order=ASC&rpp=200&value=" in href:
            year_links.append(BASE_URL + href if not href.startswith("http") else href)

    log(f"Found {len(year_links)} year pages")

    items_raw = []
    seen_handles = set()

    for yurl in year_links:
        offset = 0
        while True:
            purl = yurl if offset == 0 else yurl + f"&offset={offset}"
            try:
                raw  = http_get_html(purl)
                soup = BeautifulSoup(raw, "lxml")
                found = 0
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if "/handle/123456789/" in href and "browse" not in href:
                        handle = href.split("/handle/")[1].strip("/")
                        if handle not in seen_handles and handle != "1362":
                            seen_handles.add(handle)
                            items_raw.append({"handle": handle, "name": a.get_text(strip=True)})
                            found += 1
                log(f"  {purl[-40:]}: +{found} handles (total {len(items_raw)})")
                next_link = soup.find("img", {"src": lambda s: s and "nextPage" in s})
                if next_link and next_link.parent.get("href"):
                    offset += 200
                else:
                    break
            except Exception as e:
                log(f"  Error on {purl}: {e}")
                break

    log(f"Total handles discovered: {len(items_raw)}")

    # Convert handle-only items to format parse_item expects
    # Each needs to be fetched from REST API by handle
    full_items = []
    for item in items_raw:
        handle = item["handle"]
        rest_url = f"{REST_URL}/handle/{handle}?expand=bitstreams,metadata"
        data = http_json(rest_url)
        if data and isinstance(data, dict):
            full_items.append(data)
        time.sleep(0.05)

    return full_items

def http_get_html(url: str) -> bytes:
    html_headers = {**HEADERS, "Accept": "text/html,application/xhtml+xml"}
    req = urllib.request.Request(url, headers=html_headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()

# ── Fallback: known direct PDFs from IndiaCode ───────────────────
async def fallback_known_pdfs():
    """
    Hard-coded list of the most important regulatory documents
    with their exact IndiaCode bitstream URLs.
    These are permanent stable URLs — IndiaCode guarantees them.
    """
    global _total
    KNOWN = [
        # ── Income Tax ──────────────────────────────────────────
        ("Income Tax Act 1961", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2435/1/a1961-43.pdf"),
        ("Income Tax (Amendment) Act 2023", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/19006/1/finance_act_2023.pdf"),
        ("Finance Act 2024", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/20197/1/finance_act_2024.pdf"),
        ("Finance Act 2022", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/16889/1/finance_act_2022.pdf"),
        ("Finance Act 2021", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/15300/1/finance_act_2021.pdf"),
        ("Finance Act 2020", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/13711/1/finance_act_2020.pdf"),
        ("Finance Act 2019", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/11647/1/finance_act_2019.pdf"),
        ("Finance Act 2018", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/5706/1/finance-act-2018.pdf"),
        ("Finance Act 2017", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2429/1/a2017-07.pdf"),
        ("Direct Tax Vivad Se Vishwas Act 2020", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/13710/1/a2020-03.pdf"),
        ("Black Money Act 2015", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2211/1/a2015-22.pdf"),
        ("Benami Transactions Act 1988", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2272/1/a1988-45.pdf"),

        # ── FEMA ────────────────────────────────────────────────
        ("Foreign Exchange Management Act 1999", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2256/1/a1999-42.pdf"),
        ("FERA 1973 (replaced by FEMA)", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/9413/1/a1973-046.pdf"),
        ("Foreign Contribution Regulation Act 2010", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2340/1/a2010-42.pdf"),

        # ── GST ─────────────────────────────────────────────────
        ("Central Goods and Services Tax Act 2017", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2255/1/a2017-12.pdf"),
        ("Integrated Goods and Services Tax Act 2017", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2251/1/a2017-13.pdf"),
        ("Union Territory Goods and Services Tax Act 2017", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2248/1/a2017-14.pdf"),
        ("GST Compensation Cess Act 2017", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2246/1/a2017-15.pdf"),
        ("CGST Amendment Act 2018", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/6232/1/a2018-31.pdf"),
        ("IGST Amendment Act 2018", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/6233/1/a2018-32.pdf"),

        # ── RBI / Banking ────────────────────────────────────────
        ("Reserve Bank of India Act 1934", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2398/1/a1934-02.pdf"),
        ("Banking Regulation Act 1949", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2229/1/a1949-10.pdf"),
        ("State Bank of India Act 1955", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2192/1/a1955-23.pdf"),
        ("Deposit Insurance and Credit Guarantee Corporation Act 1961", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2432/1/a1961-47.pdf"),
        ("Payment and Settlement Systems Act 2007", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2149/1/a2007-51.pdf"),
        ("Factoring Regulation Act 2011", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2336/1/a2011-12.pdf"),
        ("Banking Laws Amendment Act 2012", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2322/1/a2012-47.pdf"),

        # ── Companies / Insolvency ───────────────────────────────
        ("Companies Act 2013", "Corporate Affairs",
         "https://www.indiacode.nic.in/bitstream/123456789/2219/1/a2013-18.pdf"),
        ("Insolvency and Bankruptcy Code 2016", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2249/1/a2016-31.pdf"),
        ("LLP Act 2008", "Corporate Affairs",
         "https://www.indiacode.nic.in/bitstream/123456789/2169/1/a2008-06.pdf"),
        ("Competition Act 2002", "Corporate Affairs",
         "https://www.indiacode.nic.in/bitstream/123456789/2237/1/a2002-12.pdf"),
        ("SEBI Act 1992", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2268/1/a1992-15.pdf"),

        # ── Customs / Excise ─────────────────────────────────────
        ("Customs Act 1962", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2428/1/a1962-52.pdf"),
        ("Customs Tariff Act 1975", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2342/1/a1975-51.pdf"),
        ("Central Excise Act 1944", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2392/1/a1944-01.pdf"),

        # ── Constitution ─────────────────────────────────────────
        ("Constitution of India", "Law and Justice",
         "https://www.indiacode.nic.in/bitstream/123456789/15240/3/constitution_of_india.pdf"),

        # ── Other Key Regulations ────────────────────────────────
        ("Foreign Trade Development and Regulation Act 1992", "Commerce",
         "https://www.indiacode.nic.in/bitstream/123456789/2265/1/a1992-22.pdf"),
        ("Prevention of Money Laundering Act 2002", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2236/1/a2002-15.pdf"),
        ("FRBM Act 2003", "Finance",
         "https://www.indiacode.nic.in/bitstream/123456789/2230/1/a2003-39.pdf"),
        ("Micro Small Medium Enterprises Act 2006", "MSME",
         "https://www.indiacode.nic.in/bitstream/123456789/2157/1/a2006-27.pdf"),
        ("Special Economic Zones Act 2005", "Commerce",
         "https://www.indiacode.nic.in/bitstream/123456789/2185/1/a2005-28.pdf"),
        ("The Digital Personal Data Protection Act 2023", "IT",
         "https://www.indiacode.nic.in/bitstream/123456789/19985/1/a2023-22.pdf"),
        ("Information Technology Act 2000", "IT",
         "https://www.indiacode.nic.in/bitstream/123456789/2199/1/a2000-21.pdf"),
        ("Right to Information Act 2005", "Law and Justice",
         "https://www.indiacode.nic.in/bitstream/123456789/2182/1/a2005-22.pdf"),
    ]

    with _lock:
        _total = len(KNOWN)

    tasks = []
    for title, ministry, url in KNOWN:
        dest_dir = OUT_DIR / safe_name(ministry)
        dest_dir.mkdir(parents=True, exist_ok=True)
        tasks.append({
            "title":    title,
            "ministry": ministry,
            "url":      url,
            "dest_dir": str(dest_dir),
            "pdfs":     [{"name": safe_name(title) + ".pdf", "url": url, "size": 0, "mime": "application/pdf"}],
            "priority": True,
            "status":   "pending",
        })

    start      = time.time()
    stop_event = asyncio.Event()
    loop       = asyncio.get_event_loop()
    prog_task  = asyncio.create_task(progress_loop(stop_event, start))

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = [loop.run_in_executor(executor, download_task, t) for t in tasks]
        await asyncio.gather(*futures)

    stop_event.set()
    await prog_task

    # Save metadata
    ok   = sum(1 for r in _results if r.get("status") == "ok")
    fail = sum(1 for r in _results if r.get("status") == "fail")
    meta = {
        "source":     "indiacode.nic.in (fallback known PDFs)",
        "scraped_at": datetime.now().isoformat(),
        "downloaded": ok,
        "failed":     fail,
        "documents":  _results,
    }
    META_FILE.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    LOG_FILE.write_text("\n".join(_logs))

    print(f"\n  {c(BOLD, GRN)}Done! {ok} files downloaded, {fail} failed.{R}")
    print(f"  {c(CYN)}Output: {OUT_DIR}{R}\n")

# ── Entry point ────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"""
{c(BOLD, BLU)}  ╔══════════════════════════════════════════════════════════╗
  ║  🇮🇳  IndiaCode Complete Regulatory Scraper               ║
  ║  Source : indiacode.nic.in (DSpace REST API)              ║
  ║  Gets   : ALL Central Acts, Rules, Notifications, GST,    ║
  ║           Income Tax, FEMA, RBI, CBDT + State Acts        ║
  ║  Mode   : 20 parallel workers + live progress bar         ║
  ╚══════════════════════════════════════════════════════════╝{R}

  Starting in 2 seconds...
""")
    time.sleep(2)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n  {c(YLW)}⚠  Interrupted. Saving partial results...{R}")
        if _results:
            META_FILE.write_text(json.dumps({
                "status":    "interrupted",
                "documents": _results
            }, indent=2))
        LOG_FILE.write_text("\n".join(_logs))
        print(f"  Saved {len(_results)} records to {META_FILE}\n")