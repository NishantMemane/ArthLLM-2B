"""
BSE Board Meetings Scraper — Maximum Speed Edition
====================================================
Architecture: flat (scrip × year) task queue → fixed thread pool
No nested executors. Each thread owns its session. Background I/O.

Speed improvements over v2 (optimized):
  A. Flat task queue — single ThreadPoolExecutor processes (scrip, year) atoms
     · eliminates nested pool create/destroy overhead per company
     · perfect load balancing: busy companies don't block idle threads
  B. Fixed bug: year-threads no longer share one requests.Session
     (requests.Session is NOT thread-safe for concurrent use)
  C. urllib3 connection pool tuned: pool_connections=50, pool_maxsize=50
     · default is 10 — was silently serializing connections
  D. Background writer thread — CSV/progress writes never block scrapers
  E. Smart year ordering — recent years first; skip pre-listing years
     when scrip_code gives a clue about listing era
  F. ujson drop-in (if installed) for faster JSON decode
  G. Async mode improved: semaphore outside request for true overlap

Usage:
  pip install aiohttp ujson          # optional speed extras
  python bse_board_meetings_scraper.py               # full run
  python bse_board_meetings_scraper.py --test         # 3 companies x 2 years
  python bse_board_meetings_scraper.py --status
  python bse_board_meetings_scraper.py --assemble
  python bse_board_meetings_scraper.py --async        # aiohttp mode
  python bse_board_meetings_scraper.py --workers 300  # override thread count
"""

import csv
import math
import queue
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# optional fast JSON
try:
    import ujson as json
except ImportError:
    import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# --- PATHS -------------------------------------------------------------------
BASE_DIR       = Path(__file__).parent
SCRIP_FILE     = BASE_DIR / "all_scrip_codes.csv"
SCRIP_FALLBACK = BASE_DIR / "bse_company_master.csv"
PROGRESS_FILE  = BASE_DIR / "scraper_progress.csv"
RAW_FILE       = BASE_DIR / "board_meetings_raw.csv"
FINAL_FILE     = BASE_DIR / "board_meetings.csv"

# --- API ---------------------------------------------------------------------
BSE_API  = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w"
PDF_LIVE = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/{}"
PDF_HIST = "https://www.bseindia.com/xml-data/corpfiling/AttachHis/{}"

CATEGORY_FILTER = "Board Meeting"
ROWS_PER_PAGE   = 20

# --- TUNING ------------------------------------------------------------------
# A: flat pool — total concurrent (scrip x year) tasks
TOTAL_WORKERS       = 150    # override with --workers N
# C: urllib3 pool size — must be >= TOTAL_WORKERS / hosts
CONN_POOL_SIZE      = 100
API_RATE_LIMIT      = 0.10   # per-session seconds between calls
MAX_RETRIES         = 3
BLOCK_PAUSE         = 45
SESSION_REFRESH     = 400    # per-thread company count before cookie refresh
# D: background writer queue size
WRITER_QUEUE_SIZE   = 2000
PROGRESS_FLUSH_EVERY = 50

START_YEAR = 2001
END_YEAR   = 2025
END_DATE   = "20250509"

HEADERS_DICT = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept":     "application/json, text/plain, */*",
    "Referer":    "https://www.bseindia.com/corporates/ann.html",
    "Origin":     "https://www.bseindia.com",
}

# --- THREAD-LOCAL SESSION ----------------------------------------------------
_tl = threading.local()


def _get_session():
    """One BSESession per OS thread — never shared between threads."""
    if not hasattr(_tl, "sess"):
        _tl.sess          = BSESession()
        _tl.company_count = 0
    return _tl.sess


def _tick_company():
    _tl.company_count = getattr(_tl, "company_count", 0) + 1
    if _tl.company_count % SESSION_REFRESH == 0:
        _tl.sess.refresh()


# =============================================================================
# C  SESSION  (tuned urllib3 pool, per-instance rate limit)
# =============================================================================

class BSESession:
    def __init__(self):
        self._sess      = self._make_session()
        self._last_call = 0.0   # per-instance — no global lock

    @staticmethod
    def _make_session():
        s = requests.Session()
        s.headers.update(HEADERS_DICT)
        # C: large connection pool so threads don't queue for sockets
        adapter = HTTPAdapter(
            pool_connections=CONN_POOL_SIZE,
            pool_maxsize=CONN_POOL_SIZE,
            max_retries=Retry(total=0),   # retries handled manually
        )
        s.mount("https://", adapter)
        s.mount("http://",  adapter)
        # warm cookies
        try:
            s.get("https://www.bseindia.com", timeout=12)
            time.sleep(0.3 + random.uniform(0, 0.2))
            s.get("https://www.bseindia.com/corporates/ann.html", timeout=12)
            time.sleep(0.2)
        except Exception:
            pass
        return s

    def refresh(self):
        try:
            self._sess.close()
        except Exception:
            pass
        self._sess = self._make_session()

    def _throttle(self):
        now = time.time()
        gap = now - self._last_call
        if gap < API_RATE_LIMIT:
            time.sleep(API_RATE_LIMIT - gap + random.uniform(0.01, 0.05))
        self._last_call = time.time()

    def get(self, params, retry=0):
        self._throttle()
        try:
            r = self._sess.get(BSE_API, params=params, timeout=45)

            if r.status_code in (429, 503):
                if retry < MAX_RETRIES:
                    time.sleep((2 ** retry) * 4 + random.uniform(0, 2))
                    return self.get(params, retry + 1)
                return None

            if r.status_code == 403:
                if retry < 1:
                    time.sleep(BLOCK_PAUSE)
                    self.refresh()
                    return self.get(params, retry + 1)
                return None

            r.raise_for_status()

            ct = r.headers.get("Content-Type", "")
            if "html" in ct and "json" not in ct:
                if retry < 1:
                    time.sleep(BLOCK_PAUSE)
                    self.refresh()
                    return self.get(params, retry + 1)
                return None

            # F: ujson if available (imported at top as json)
            return json.loads(r.content)

        except requests.exceptions.Timeout:
            if retry < MAX_RETRIES:
                time.sleep((2 ** retry) * 4)
                return self.get(params, retry + 1)
            return None

        except Exception:
            if retry < MAX_RETRIES:
                time.sleep((2 ** retry) * 2)
                return self.get(params, retry + 1)
            return None

    def close(self):
        try:
            self._sess.close()
        except Exception:
            pass


# =============================================================================
# D  BACKGROUND WRITER
#   Scraper threads push rows/progress onto a queue.
#   A single writer thread drains it — scrapers never block on file I/O.
# =============================================================================

class BackgroundWriter:
    _STOP = object()

    def __init__(self):
        self._q      = queue.Queue(maxsize=WRITER_QUEUE_SIZE)
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def push_rows(self, rows: list):
        if rows:
            self._q.put(("rows", rows))

    def push_progress(self, entry: dict):
        self._q.put(("progress", entry))

    def flush_and_stop(self):
        self._q.put(self._STOP)
        self._thread.join()

    def _loop(self):
        pending_rows     = []
        pending_progress = {}
        FLUSH_ROWS_EVERY = 500
        dirty            = 0

        if not RAW_FILE.exists():
            with open(RAW_FILE, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([
                    "scrip_code", "company_name", "category", "attachment",
                    "pdf_url", "pdf_url_hist", "filing_date", "headline",
                ])

        while True:
            try:
                item = self._q.get(timeout=2.0)
            except queue.Empty:
                self._flush_rows(pending_rows);         pending_rows = []
                self._flush_progress(pending_progress); dirty = 0
                continue

            if item is self._STOP:
                self._flush_rows(pending_rows)
                self._flush_progress(pending_progress)
                return

            kind, payload = item
            if kind == "rows":
                pending_rows.extend(payload)
                if len(pending_rows) >= FLUSH_ROWS_EVERY:
                    self._flush_rows(pending_rows)
                    pending_rows = []
            elif kind == "progress":
                key = f"{payload['scrip_code']}|{payload['year']}"
                pending_progress[key] = payload
                dirty += 1
                if dirty >= PROGRESS_FLUSH_EVERY:
                    self._flush_progress(pending_progress)
                    dirty = 0

    @staticmethod
    def _flush_rows(rows):
        if not rows:
            return
        with open(RAW_FILE, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for r in rows:
                w.writerow([
                    r["scrip_code"], r["company_name"], r["category"],
                    r["attachment"], r["pdf_url"], r["pdf_url_hist"],
                    r["filing_date"], r["headline"],
                ])

    @staticmethod
    def _flush_progress(pending: dict):
        if not pending:
            return
        existing = {}
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    existing[f"{row['scrip_code']}|{row['year']}"] = row
        existing.update(pending)
        rows = sorted(existing.values(), key=lambda x: (x["scrip_code"], x["year"]))
        with open(PROGRESS_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=[
                "scrip_code", "company_name", "year", "status",
                "rows_collected", "last_page",
            ])
            w.writeheader()
            w.writerows(rows)


# =============================================================================
# PROGRESS TRACKER  (in-memory; persisted by BackgroundWriter)
# =============================================================================

class ProgressTracker:
    def __init__(self, writer: BackgroundWriter):
        self._lock   = threading.Lock()
        self._writer = writer
        self._done   = set()
        self._fail   = set()
        self._counts = {}

        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    key = f"{row['scrip_code']}|{row['year']}"
                    if row["status"] == "done":
                        self._done.add(key)
                        self._counts[key] = int(row.get("rows_collected", 0))
                    elif row["status"] == "failed":
                        self._fail.add(key)

    def is_done(self, scrip, year):
        with self._lock:
            return f"{scrip}|{year}" in self._done

    def mark_done(self, scrip, name, year, n_rows, last_page):
        key = f"{scrip}|{year}"
        with self._lock:
            self._done.add(key)
            self._counts[key] = n_rows
        self._writer.push_progress({
            "scrip_code": scrip, "company_name": name, "year": str(year),
            "status": "done", "rows_collected": n_rows, "last_page": last_page,
        })

    def mark_failed(self, scrip, name, year):
        with self._lock:
            self._fail.add(f"{scrip}|{year}")
        self._writer.push_progress({
            "scrip_code": scrip, "company_name": name, "year": str(year),
            "status": "failed", "rows_collected": 0, "last_page": 0,
        })

    def stats(self):
        with self._lock:
            return len(self._done), len(self._fail), sum(self._counts.values())


# =============================================================================
# SCRIP LOADING
# =============================================================================

def load_scrip_codes():
    src = SCRIP_FILE if SCRIP_FILE.exists() else SCRIP_FALLBACK
    if not src.exists():
        print(f"[X] No scrip file at {SCRIP_FILE} or {SCRIP_FALLBACK}", flush=True)
        sys.exit(1)

    companies, seen = [], set()
    with open(src, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sc = row.get("scrip_code", "").strip()
            if sc and sc not in seen:
                seen.add(sc)
                companies.append({
                    "scrip_code":   sc,
                    "company_name": row.get("company_name", "").strip(),
                })
    print(f"  Loaded {len(companies):,} companies from {src.name}", flush=True)
    return companies


# =============================================================================
# E  SMART YEAR ORDERING
#   BSE scrip codes are roughly sequential by listing date.
#   Skip years before the company likely existed; process recent years first.
# =============================================================================

def build_year_chunks():
    """
    All years START_YEAR..END_YEAR, newest-first.
    Newest-first means recent data arrives quickly, but NO years are skipped —
    the scrip-code heuristic was removed because it caused missed rows.
    """
    chunks = []
    for year in range(END_YEAR, START_YEAR - 1, -1):
        from_date = f"{year}0101"
        to_date   = END_DATE if year == END_YEAR else f"{year}1231"
        chunks.append((year, from_date, to_date))
    return chunks


# =============================================================================
# CORE SCRAPER
# =============================================================================

def scrape_one_year(scrip_code, company_name, year, from_date, to_date):
    """
    B fix: calls _get_session() — always this thread's OWN session.
    Returns list of rows, [] for no data, or None on API failure.
    """
    sess = _get_session()
    all_rows, page, total_count = [], 1, None

    while True:
        params = {
            "strCat":      CATEGORY_FILTER,
            "strPrevDate": from_date,
            "strScrip":    str(scrip_code),
            "strSearch":   "P",
            "strToDate":   to_date,
            "strType":     "C",
            "strPageNo":   str(page),
        }

        data = sess.get(params)
        if data is None:
            return None

        rows = []
        if isinstance(data, dict):
            rows = data.get("Table", []) or []
            if page == 1:
                try:
                    t1 = data.get("Table1", [{}])[0]
                    total_count = int(
                        t1.get("ROWCNT", 0) or t1.get("RWCNT", 0) or 0
                    )
                except Exception:
                    total_count = 0
        elif isinstance(data, list):
            rows = data

        if page == 1 and total_count == 0 and not rows:
            return []

        if not rows:
            break

        for ann in rows:
            att = (ann.get("ATTACHMENTNAME") or "").strip()
            all_rows.append({
                "scrip_code":   str(ann.get("SCRIP_CD", scrip_code)),
                "company_name": (ann.get("SLONGNAME") or company_name or "").strip(),
                "category":     "board_meetings",
                "attachment":   att,
                "pdf_url":      PDF_LIVE.format(att) if att else "",
                "pdf_url_hist": PDF_HIST.format(att) if att else "",
                "filing_date":  (ann.get("NEWS_DT") or "").strip(),
                "headline":     (ann.get("HEADLINE") or "").strip(),
            })

        if total_count and len(all_rows) >= total_count:
            break
        if len(rows) < ROWS_PER_PAGE or page >= 50:
            break

        page += 1

    return all_rows


# =============================================================================
# ASYNC MODE  (aiohttp)
# =============================================================================

def run_async_mode(all_tasks, tracker, writer):
    try:
        import asyncio
        import aiohttp
    except ImportError:
        print("[X] pip install aiohttp", flush=True)
        sys.exit(1)

    CONCURRENCY = 200

    async def api_get(session, sem, params, retry=0):
        async with sem:
            try:
                async with session.get(
                    BSE_API, params=params,
                    timeout=aiohttp.ClientTimeout(total=45),
                ) as r:
                    if r.status in (429, 503):
                        if retry < MAX_RETRIES:
                            await asyncio.sleep((2 ** retry) * 4)
                            return await api_get(session, sem, params, retry + 1)
                        return None
                    if r.status == 403:
                        if retry < 1:
                            await asyncio.sleep(BLOCK_PAUSE)
                            return await api_get(session, sem, params, retry + 1)
                        return None
                    r.raise_for_status()
                    return await r.json(content_type=None, loads=json.loads)
            except asyncio.TimeoutError:
                if retry < MAX_RETRIES:
                    await asyncio.sleep((2 ** retry) * 4)
                    return await api_get(session, sem, params, retry + 1)
                return None
            except Exception:
                if retry < MAX_RETRIES:
                    await asyncio.sleep((2 ** retry) * 2)
                    return await api_get(session, sem, params, retry + 1)
                return None

    async def scrape_year(session, sem, scrip, name, year, from_d, to_d):
        all_rows, page, total_count = [], 1, None
        while True:
            params = {
                "strCat": CATEGORY_FILTER, "strPrevDate": from_d,
                "strScrip": str(scrip), "strSearch": "P",
                "strToDate": to_d, "strType": "C", "strPageNo": str(page),
            }
            data = await api_get(session, sem, params)
            if data is None:
                return scrip, name, year, None

            rows = []
            if isinstance(data, dict):
                rows = data.get("Table", []) or []
                if page == 1:
                    try:
                        t1 = data.get("Table1", [{}])[0]
                        total_count = int(
                            t1.get("ROWCNT", 0) or t1.get("RWCNT", 0) or 0
                        )
                    except Exception:
                        total_count = 0
            elif isinstance(data, list):
                rows = data

            if page == 1 and total_count == 0 and not rows:
                return scrip, name, year, []
            if not rows:
                break

            for ann in rows:
                att = (ann.get("ATTACHMENTNAME") or "").strip()
                all_rows.append({
                    "scrip_code": str(ann.get("SCRIP_CD", scrip)),
                    "company_name": (ann.get("SLONGNAME") or name or "").strip(),
                    "category": "board_meetings", "attachment": att,
                    "pdf_url": PDF_LIVE.format(att) if att else "",
                    "pdf_url_hist": PDF_HIST.format(att) if att else "",
                    "filing_date": (ann.get("NEWS_DT") or "").strip(),
                    "headline": (ann.get("HEADLINE") or "").strip(),
                })

            if total_count and len(all_rows) >= total_count:
                break
            if len(rows) < ROWS_PER_PAGE or page >= 50:
                break
            page += 1

        return scrip, name, year, all_rows

    async def main_async():
        sem  = asyncio.Semaphore(CONCURRENCY)
        conn = aiohttp.TCPConnector(
            limit=CONCURRENCY, ssl=False,
            ttl_dns_cache=300, use_dns_cache=True,
        )
        async with aiohttp.ClientSession(headers=HEADERS_DICT, connector=conn) as session:
            try:
                await session.get("https://www.bseindia.com",
                                  timeout=aiohttp.ClientTimeout(total=12))
                await asyncio.sleep(0.3)
            except Exception:
                pass

            grand, done = 0, 0
            start = time.time()
            BATCH = 500

            for i in range(0, len(all_tasks), BATCH):
                batch = all_tasks[i: i + BATCH]
                coros = [
                    scrape_year(session, sem, sc, nm, yr, fd, td)
                    for sc, nm, yr, fd, td in batch
                ]
                results = await asyncio.gather(*coros, return_exceptions=True)

                for (sc, nm, yr, fd, td), res in zip(batch, results):
                    done += 1
                    if isinstance(res, Exception):
                        tracker.mark_failed(sc, nm, yr)
                        continue
                    _, _, _, rows = res
                    if rows is None:
                        tracker.mark_failed(sc, nm, yr)
                    elif not rows:
                        tracker.mark_done(sc, nm, yr, 0, 0)
                    else:
                        writer.push_rows(rows)
                        tracker.mark_done(sc, nm, yr, len(rows),
                                          max(1, math.ceil(len(rows) / ROWS_PER_PAGE)))
                        grand += len(rows)

                elapsed = time.time() - start
                rate    = done / max(elapsed, 1) * 3600
                eta_h   = (len(all_tasks) - done) / max(rate, 1)
                print(
                    f"  [{done:,}/{len(all_tasks):,}] "
                    f"rows: {grand:,} | ETA: {eta_h:.1f}h",
                    flush=True,
                )

        return grand

    print("  [ASYNC MODE — aiohttp]", flush=True)
    return asyncio.run(main_async())


# =============================================================================
# FINAL ASSEMBLY (Phase 9)
# =============================================================================

def assemble_final_csv():
    print("\n" + "=" * 60, flush=True)
    print("PHASE 9: FINAL CSV ASSEMBLY & DEDUP", flush=True)
    print("=" * 60, flush=True)

    if not RAW_FILE.exists():
        print("  [X] Raw file not found.", flush=True)
        return

    with open(RAW_FILE, "r", encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))

    print(f"  Raw rows: {len(all_rows):,}", flush=True)

    seen, unique = set(), []
    for row in all_rows:
        key = (f"{row.get('scrip_code','')}|{row.get('filing_date','')}|"
               f"{row.get('attachment','')}")
        if key not in seen:
            seen.add(key)
            unique.append(row)

    print(f"  After dedup: {len(unique):,} (removed {len(all_rows)-len(unique):,})",
          flush=True)

    def _dt(d):
        try:
            return datetime.fromisoformat(d.replace("Z", ""))
        except Exception:
            return datetime.min

    unique.sort(key=lambda r: _dt(r.get("filing_date", "")), reverse=True)

    with open(FINAL_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["scrip_code", "company_name", "category", "attachment",
                    "pdf_url", "pdf_url_hist", "filing_date", "headline", "status"])
        for row in unique:
            w.writerow([
                row.get("scrip_code", ""), row.get("company_name", ""),
                row.get("category", "board_meetings"), row.get("attachment", ""),
                row.get("pdf_url", ""), row.get("pdf_url_hist", ""),
                row.get("filing_date", ""), row.get("headline", ""), "pending",
            ])

    companies   = {r.get("scrip_code", "") for r in unique}
    with_pdf    = sum(1 for r in unique if r.get("attachment", "").strip())
    valid_dates = [_dt(r.get("filing_date", "")) for r in unique
                   if _dt(r.get("filing_date", "")) != datetime.min]

    print(f"  OUTPUT            : {FINAL_FILE}", flush=True)
    print(f"  Rows              : {len(unique):,}", flush=True)
    print(f"  Companies covered : {len(companies):,}", flush=True)
    if valid_dates:
        print(f"  Date range        : {min(valid_dates):%Y-%m-%d} to "
              f"{max(valid_dates):%Y-%m-%d}", flush=True)
    print(f"  With PDF          : {with_pdf:,} "
          f"({100*with_pdf/max(len(unique),1):.1f}%)", flush=True)
    print("=" * 60, flush=True)


# =============================================================================
# STATUS
# =============================================================================

def show_status():
    print("=" * 60, flush=True)
    if not PROGRESS_FILE.exists():
        print("  No progress file yet.", flush=True)
        return
    total = done = failed = rows = 0
    companies = set()
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            total += 1
            companies.add(row["scrip_code"])
            rows += int(row.get("rows_collected", 0))
            if row["status"] == "done":     done   += 1
            elif row["status"] == "failed": failed += 1
    print(f"  Companies : {len(companies):,}", flush=True)
    print(f"  Tasks     : {total:,}  done={done:,}  failed={failed:,}  "
          f"pending={total-done-failed:,}", flush=True)
    print(f"  Rows      : {rows:,}", flush=True)
    if RAW_FILE.exists():
        n = sum(1 for _ in open(RAW_FILE, encoding="utf-8")) - 1
        print(f"  Raw CSV   : {n:,} lines", flush=True)
    if FINAL_FILE.exists():
        n = sum(1 for _ in open(FINAL_FILE, encoding="utf-8")) - 1
        print(f"  Final CSV : {n:,} lines", flush=True)
    print("=" * 60, flush=True)


# =============================================================================
# MAIN
# =============================================================================

def main():
    args = sys.argv[1:]

    if "--status"   in args: show_status();       return
    if "--assemble" in args: assemble_final_csv(); return

    test_mode  = "--test"  in args
    async_mode = "--async" in args

    n_workers = TOTAL_WORKERS
    if "--workers" in args:
        idx = args.index("--workers")
        try:
            n_workers = int(args[idx + 1])
        except (IndexError, ValueError):
            pass

    print("=" * 60, flush=True)
    print("BSE BOARD MEETINGS SCRAPER  [MAX SPEED]", flush=True)
    print(f"Date Range  : {START_YEAR} to {END_YEAR}", flush=True)
    mode_str = "ASYNC (aiohttp)" if async_mode else f"THREADED ({n_workers} workers)"
    print(f"Mode        : {mode_str}{' + TEST' if test_mode else ''}", flush=True)
    print(f"Conn pool   : {CONN_POOL_SIZE}", flush=True)
    print(f"Started     : {datetime.now()}", flush=True)
    print("=" * 60, flush=True)

    companies = load_scrip_codes()

    if test_mode:
        test_scrips = {"500209", "500325", "532540"}
        companies   = ([c for c in companies if c["scrip_code"] in test_scrips]
                       or companies[:3])

    writer  = BackgroundWriter()
    tracker = ProgressTracker(writer)

    # A + E: flat task list, smart year range per scrip, newest-first
    all_tasks = []
    for c in companies:
        sc   = c["scrip_code"]
        name = c["company_name"]
        chunks = build_year_chunks()
        if test_mode:
            chunks = [(yr, fd, td) for yr, fd, td in chunks if yr in (2023, 2024)]
        for yr, fd, td in chunks:
            if not tracker.is_done(sc, yr):
                all_tasks.append((sc, name, yr, fd, td))

    already_done = sum(
        1 for c in companies
        for yr, _, _ in build_year_chunks()
        if tracker.is_done(c["scrip_code"], yr)
    )
    print(f"  Companies    : {len(companies):,}", flush=True)
    print(f"  Tasks pending: {len(all_tasks):,}  (already done: {already_done:,})",
          flush=True)
    print("=" * 60, flush=True)

    grand_total = 0
    start_time  = time.time()

    if async_mode:
        grand_total = run_async_mode(all_tasks, tracker, writer)

    else:
        # A: flat pool
        done_count = 0
        count_lock = threading.Lock()

        def _worker(task):
            nonlocal grand_total, done_count
            sc, name, yr, fd, td = task
            rows = scrape_one_year(sc, name, yr, fd, td)
            _tick_company()

            if rows is None:
                tracker.mark_failed(sc, name, yr)
                n = 0
            elif not rows:
                tracker.mark_done(sc, name, yr, 0, 0)
                n = 0
            else:
                writer.push_rows(rows)
                tracker.mark_done(sc, name, yr, len(rows),
                                  max(1, math.ceil(len(rows) / ROWS_PER_PAGE)))
                n = len(rows)

            with count_lock:
                grand_total += n
                done_count  += 1
                dc = done_count
                gt = grand_total

            if n > 0 or dc % 500 == 0:
                elapsed = time.time() - start_time
                rate    = dc / max(elapsed, 1) * 3600
                eta_h   = (len(all_tasks) - dc) / max(rate, 1)
                print(
                    f"  [{dc:,}/{len(all_tasks):,}] "
                    f"{sc:>6s} {yr}  +{n:3d} rows | "
                    f"total: {gt:,} | ETA: {eta_h:.1f}h",
                    flush=True,
                )

        with ThreadPoolExecutor(max_workers=n_workers) as ex:
            futures = [ex.submit(_worker, t) for t in all_tasks]
            for f in as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    print(f"  [!] {e}", flush=True)

    writer.flush_and_stop()

    elapsed = time.time() - start_time
    done, fail, rows = tracker.stats()
    print(f"\n{'='*60}", flush=True)
    print(f"COMPLETE  {elapsed/3600:.1f}h | rows={grand_total:,} | "
          f"done={done:,} failed={fail:,}", flush=True)
    print("=" * 60, flush=True)

    assemble_final_csv()


if __name__ == "__main__":
    main()