"""
BSE Insider Trading / SAST — Async CSV Manifest Builder  (FAST edition)
Key fixes over v1:
  • asyncio.gather() on chunks — windows are now truly parallel (was sequential!)
  • CONCURRENCY 5 → 8
  • Progress saved every SAVE_EVERY windows, not every window (disk I/O was a bottleneck)
  • CSV writes batched per chunk (one open/close per chunk, not per window)
  • RateLimiter simplified — semaphore + per-slot timestamp, no broken index return
  • Retry logic cleaned up (was double-acquiring the limiter on retry)
"""

import aiohttp
import asyncio
import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta
from collections import deque
from tqdm import tqdm

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── paths ──────────────────────────────────────────────────────────────────
BASE      = r"c:\Users\shree\Desktop\AA\ArthLLM-2B\corporate_announcements"
LOGS      = os.path.join(BASE, "logs")
CSV_PATH  = os.path.join(BASE, "insider_trading.csv")
PROG_PATH = os.path.join(LOGS, "manifest_progress_insider_trading.json")
os.makedirs(LOGS, exist_ok=True)

# ── config ─────────────────────────────────────────────────────────────────
BSE_API    = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w"
PDF_LIVE   = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/{}"
PDF_HIST   = "https://www.bseindia.com/xml-data/corpfiling/AttachHis/{}"
CAT_NAME   = "insider_trading"
CAT_FILTER = "Insider Trading / SAST"  # spaces around slash required by BSE API

CONCURRENCY  = 8        # true parallel slots
MIN_DELAY    = 1.0      # seconds between requests per slot
RETRY_WAIT   = 40       # back-off on 429 / 503
WINDOW_DAYS  = 30
CHUNK_SIZE   = CONCURRENCY * 4   # windows dispatched per gather() call
SAVE_EVERY   = 20       # save progress JSON every N completed windows

START = datetime(2011, 1, 1)
END   = datetime(2026, 5, 8)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bseindia.com/corporates/ann.html",
    "Origin": "https://www.bseindia.com",
}

CSV_COLUMNS = [
    "scrip_code", "company_name", "category", "attachment",
    "pdf_url_live", "pdf_url_hist",
    "filing_date", "headline", "status",
    "scrip_cd_raw", "long_name_raw", "dt_tm_raw", "newssub_raw",
]


# ── helpers ─────────────────────────────────────────────────────────────────
def make_windows():
    wins, cur = [], START
    while cur < END:
        w_end = min(cur + timedelta(days=WINDOW_DAYS - 1), END)
        wins.append((cur.strftime("%Y%m%d"), w_end.strftime("%Y%m%d")))
        cur = w_end + timedelta(days=1)
    return wins


def load_progress():
    if os.path.exists(PROG_PATH):
        with open(PROG_PATH) as f:
            return set(json.load(f).get("done_windows", []))
    return set()


def save_progress(done_w):
    with open(PROG_PATH, "w") as f:
        json.dump({"done_windows": list(done_w),
                   "updated": datetime.now().isoformat()}, f)






def load_seen():
    seen = set()
    if not os.path.exists(CSV_PATH):
        return seen
    try:
        with open(CSV_PATH, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                att = (row.get("attachment") or "").strip()
                if att:
                    seen.add(att)
                else:
                    sc = row.get("scrip_code", "")
                    fd = row.get("filing_date", "")
                    hl = (row.get("headline") or "")[:80]
                    seen.add(f"{sc}|{fd}|{hl}")
    except Exception:
        pass
    return seen


def dedup_key(ann):
    att = (ann.get("ATTACHMENTNAME") or "").strip()
    if att:
        return att
    sc = str(ann.get("SCRIP_CD", ""))
    dt = (ann.get("DT_TM") or "").strip()
    hl = (ann.get("NEWSSUB") or "").strip()[:80]
    return f"{sc}|{dt}|{hl}"


def ann_to_row(ann):
    att     = (ann.get("ATTACHMENTNAME") or "").strip()
    scrip   = str(ann.get("SCRIP_CD", ""))
    company = (ann.get("SLONGNAME") or ann.get("SCRIP_NAME") or "").strip()
    headline= (ann.get("NEWSSUB") or "").strip()
    dt      = (ann.get("DT_TM") or "").strip()
    return [
        scrip, company, CAT_NAME, att,
        PDF_LIVE.format(att) if att else "",
        PDF_HIST.format(att) if att else "",
        dt, headline, "pending",
        scrip, (ann.get("SLONGNAME") or "").strip(), dt, headline,
    ]


def append_csv(rows, first_write):
    mode = "w" if first_write else "a"
    with open(CSV_PATH, mode, newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if first_write:
            w.writerow(CSV_COLUMNS)
        w.writerows(rows)


# ── rate limiter ────────────────────────────────────────────────────────────
class RateLimiter:
    """Token-bucket: CONCURRENCY parallel slots, each respects MIN_DELAY."""
    def __init__(self, n, delay):
        self._sem   = asyncio.Semaphore(n)
        self._delay = delay
        self._slots = [0.0] * n          # last-used timestamp per slot
        self._free  = deque(range(n))    # available slot indices
        self._lock  = asyncio.Lock()

    async def __aenter__(self):
        await self._sem.acquire()
        async with self._lock:
            self._slot = self._free.popleft()
        wait = self._delay - (time.monotonic() - self._slots[self._slot])
        if wait > 0:
            await asyncio.sleep(wait)
        self._slots[self._slot] = time.monotonic()
        return self

    async def __aexit__(self, *_):
        async with self._lock:
            self._free.append(self._slot)
        self._sem.release()


# ── window fetcher ───────────────────────────────────────────────────────────
async def fetch_window(session, rl, wf, wt, seen, seen_lock):
    """
    Fetch ALL pages for one date window.
    Returns (list_of_new_rows, success: bool)
    """
    new_rows  = []
    page      = 1
    total_cnt = 0
    collected = 0

    while True:
        params = {
            "strCat": CAT_FILTER, "strPrevDate": wf, "strScrip": "",
            "strSearch": "P", "strToDate": wt, "strType": "C",
            "strPageNo": str(page),
        }

        data = None
        for attempt in range(3):
            try:
                async with rl:
                    async with session.get(
                        BSE_API, params=params,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as resp:
                        if resp.status in (429, 503):
                            await asyncio.sleep(RETRY_WAIT * (attempt + 1))
                            continue
                        if resp.status != 200:
                            return new_rows, False
                        data = await resp.json(content_type=None)
                break
            except Exception:
                if attempt == 2:
                    return new_rows, False
                await asyncio.sleep(10 * (attempt + 1))

        if data is None:
            return new_rows, False

        rows = []
        if isinstance(data, dict) and "Table" in data:
            rows = data["Table"]
        elif isinstance(data, list):
            rows = data

        if page == 1 and isinstance(data, dict) and "Table1" in data:
            try:
                total_cnt = int(data["Table1"][0]["ROWCNT"])
            except Exception:
                pass

        if not rows:
            break

        collected += len(rows)

        # dedup under lock so parallel tasks don't race on `seen`
        async with seen_lock:
            for ann in rows:
                key = dedup_key(ann)
                if key in seen:
                    continue
                seen.add(key)
                new_rows.append(ann_to_row(ann))

        if total_cnt > 0 and collected >= total_cnt:
            break
        page += 1

    return new_rows, True


# ── main ─────────────────────────────────────────────────────────────────────
async def main():
    print("=" * 62)
    print("BSE INSIDER TRADING / SAST  —  FAST ASYNC MANIFEST BUILDER")
    print(f"  Range       : Jan 2011 – May 2026")
    print(f"  Concurrency : {CONCURRENCY}  |  Window : {WINDOW_DAYS}d  |  ChunkSize : {CHUNK_SIZE}")
    print(f"  Output      : {CSV_PATH}")
    print("=" * 62)

    done_w     = load_progress()
    seen       = load_seen()
    windows    = make_windows()
    pending    = [(f, t) for f, t in windows if f"{f}_{t}" not in done_w]
    first_write= not os.path.exists(CSV_PATH)

    print(f"  Windows  : {len(windows)} total, {len(pending)} pending")
    print(f"  Existing : {len(seen):,} rows in CSV\n")

    connector = aiohttp.TCPConnector(limit=CONCURRENCY + 4, ssl=False)
    rl        = RateLimiter(CONCURRENCY, MIN_DELAY)
    seen_lock = asyncio.Lock()

    total_new  = 0
    failed_w   = []
    since_save = 0

    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        # warm up
        try:
            async with session.get("https://www.bseindia.com",
                                   timeout=aiohttp.ClientTimeout(total=15)):
                pass
            await asyncio.sleep(0.5)
            async with session.get("https://www.bseindia.com/corporates/ann.html",
                                   timeout=aiohttp.ClientTimeout(total=15)):
                pass
            print("  Session warm-up OK\n")
        except Exception as e:
            print(f"  Warm-up warning: {e}\n")

        pbar = tqdm(total=len(pending), desc="insider_trading", unit="win",
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} "
                               "[{elapsed}<{remaining}, {rate_fmt}]  +{postfix}")
        pbar.set_postfix_str("0 rows")

        # ── TRUE PARALLEL: dispatch CHUNK_SIZE tasks at once ──────────────
        for chunk_start in range(0, len(pending), CHUNK_SIZE):
            chunk = pending[chunk_start: chunk_start + CHUNK_SIZE]

            tasks = [
                asyncio.create_task(
                    fetch_window(session, rl, wf, wt, seen, seen_lock)
                )
                for wf, wt in chunk
            ]
            results = await asyncio.gather(*tasks)

            chunk_rows = []
            for (wf, wt), (rows, ok) in zip(chunk, results):
                if not ok:
                    failed_w.append((wf, wt))
                else:
                    done_w.add(f"{wf}_{wt}")
                    since_save += 1
                if rows:
                    chunk_rows.extend(rows)
                    total_new += len(rows)

            # one CSV write per chunk (not per window)
            if chunk_rows:
                append_csv(chunk_rows, first_write)
                first_write = False

            # save progress every SAVE_EVERY completed windows
            if since_save >= SAVE_EVERY:
                save_progress(done_w)
                since_save = 0

            pbar.update(len(chunk))
            pbar.set_postfix_str(f"{total_new:,} rows")

            # re-warm every 10 chunks
            if (chunk_start // CHUNK_SIZE) % 10 == 9:
                try:
                    async with session.get("https://www.bseindia.com",
                                           timeout=aiohttp.ClientTimeout(total=10)):
                        pass
                except Exception:
                    pass

        pbar.close()

    # final progress save
    save_progress(done_w)

    # stats
    csv_rows = 0
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, encoding="utf-8") as f:
            csv_rows = sum(1 for _ in f) - 1

    print(f"\n{'='*62}")
    print(f"DONE  —  {total_new:,} new rows  |  {csv_rows:,} total in CSV")
    if failed_w:
        print(f"  ⚠  {len(failed_w)} windows FAILED — re-run to retry (resume is safe)")
        print(f"  Failed: {failed_w[:5]}{'...' if len(failed_w) > 5 else ''}")
    print(f"  Output : {CSV_PATH}")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(main())
