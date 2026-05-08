"""
BSE Insider Trading / SAST — Async CSV Manifest Builder
Fetches ALL insider trading announcements (2011-2026) into a single CSV.
Async with 5 concurrent slots, full resume, no rows skipped.
"""
import aiohttp
import asyncio
import csv
import json
import os
import sys
import time
from datetime import datetime, timedelta
from tqdm import tqdm

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# --- PATHS ---
BASE = r"c:\Users\shree\Desktop\AA\ArthLLM-2B\corporate_announcements"
LOGS = os.path.join(BASE, "logs")
CSV_PATH = os.path.join(BASE, "insider_trading.csv")
PROG_PATH = os.path.join(LOGS, "manifest_progress_insider_trading.json")
os.makedirs(LOGS, exist_ok=True)

# --- CONFIG ---
BSE_API    = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w"
PDF_LIVE   = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/{}"
PDF_HIST   = "https://www.bseindia.com/xml-data/corpfiling/AttachHis/{}"
CAT_NAME   = "insider_trading"
CAT_FILTER = "Insider Trading / SAST"

CONCURRENCY  = 5
MIN_DELAY    = 1.0
RETRY_WAIT   = 45
WINDOW_DAYS  = 30

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
        json.dump({"done_windows": list(done_w), "updated": datetime.now().isoformat()}, f)


def load_seen():
    seen = set()
    if os.path.exists(CSV_PATH):
        try:
            with open(CSV_PATH, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    att = (row.get("attachment") or "").strip()
                    if att:
                        seen.add(att)
                    else:
                        sc = row.get("scrip_code", "")
                        fd = row.get("filing_date", "")
                        hl = row.get("headline", "")[:80]
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
    att = (ann.get("ATTACHMENTNAME") or "").strip()
    scrip = str(ann.get("SCRIP_CD", ""))
    company = (ann.get("SLONGNAME") or ann.get("SCRIP_NAME") or "").strip()
    headline = (ann.get("NEWSSUB") or "").strip()
    dt = (ann.get("DT_TM") or "").strip()

    return [
        scrip, company, CAT_NAME, att,
        PDF_LIVE.format(att) if att else "",
        PDF_HIST.format(att) if att else "",
        dt, headline, "pending",
        str(ann.get("SCRIP_CD", "")),
        (ann.get("SLONGNAME") or "").strip(),
        dt,
        (ann.get("NEWSSUB") or "").strip(),
    ]


class RateLimiter:
    def __init__(self, n, delay):
        self.sema = asyncio.Semaphore(n)
        self.delay = delay
        self.slots = [0.0] * n
        self.lock = asyncio.Lock()

    async def acquire(self):
        await self.sema.acquire()
        async with self.lock:
            now = time.time()
            idx = min(range(len(self.slots)), key=lambda i: self.slots[i])
            wait = self.slots[idx] + self.delay - now
            if wait > 0:
                await asyncio.sleep(wait)
            self.slots[idx] = time.time()
            return idx

    def release(self):
        self.sema.release()


async def fetch_window(session, limiter, wf, wt, seen, lock):
    """Fetch all pages for one date window. Returns list of new rows."""
    new_rows = []
    page = 1
    total_count = 0
    collected = 0

    while True:
        params = {
            "strCat": CAT_FILTER, "strPrevDate": wf, "strScrip": "",
            "strSearch": "P", "strToDate": wt, "strType": "C",
            "strPageNo": str(page),
        }

        slot = await limiter.acquire()
        try:
            async with session.get(BSE_API, params=params,
                                   timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status in (429, 503):
                    await asyncio.sleep(RETRY_WAIT)
                    async with session.get(BSE_API, params=params,
                                           timeout=aiohttp.ClientTimeout(total=60)) as r2:
                        if r2.status != 200:
                            return None
                        data = await r2.json(content_type=None)
                elif resp.status != 200:
                    return None
                else:
                    data = await resp.json(content_type=None)
        except Exception:
            await asyncio.sleep(RETRY_WAIT)
            try:
                s2 = await limiter.acquire()
                try:
                    async with session.get(BSE_API, params=params,
                                           timeout=aiohttp.ClientTimeout(total=60)) as r3:
                        if r3.status != 200:
                            return None
                        data = await r3.json(content_type=None)
                finally:
                    limiter.release()
            except Exception:
                return None
        finally:
            limiter.release()

        rows = []
        if isinstance(data, dict) and "Table" in data:
            rows = data["Table"]
        elif isinstance(data, list):
            rows = data

        if page == 1 and isinstance(data, dict) and "Table1" in data:
            try:
                total_count = int(data["Table1"][0]["ROWCNT"])
            except Exception:
                pass

        if not rows:
            break

        collected += len(rows)

        async with lock:
            for ann in rows:
                key = dedup_key(ann)
                if key in seen:
                    continue
                seen.add(key)
                new_rows.append(ann_to_row(ann))

        if total_count > 0 and collected >= total_count:
            break
        page += 1

    return new_rows


def append_csv(rows, first_write):
    """Write rows to CSV immediately — no buffering."""
    mode = "w" if first_write else "a"
    with open(CSV_PATH, mode, newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if first_write:
            w.writerow(CSV_COLUMNS)
        w.writerows(rows)


async def main():
    print("=" * 60)
    print("BSE INSIDER TRADING / SAST — ASYNC CSV MANIFEST")
    print(f"Range      : Jan 2011 – May 2026")
    print(f"Concurrency: {CONCURRENCY}")
    print(f"Output     : {CSV_PATH}")
    print("=" * 60)

    done_w = load_progress()
    seen = load_seen()
    windows = make_windows()
    pending = [(f, t) for f, t in windows if f"{f}_{t}" not in done_w]

    first_write = not os.path.exists(CSV_PATH)

    print(f"Windows    : {len(windows)} total, {len(pending)} pending")
    print(f"Existing   : {len(seen)} rows in CSV")

    connector = aiohttp.TCPConnector(limit=CONCURRENCY + 2, ssl=False)
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        # Warm up
        try:
            async with session.get("https://www.bseindia.com",
                                   timeout=aiohttp.ClientTimeout(total=15)):
                pass
            await asyncio.sleep(1)
            async with session.get("https://www.bseindia.com/corporates/ann.html",
                                   timeout=aiohttp.ClientTimeout(total=15)):
                pass
        except Exception:
            pass

        limiter = RateLimiter(CONCURRENCY, MIN_DELAY)
        lock = asyncio.Lock()
        total_new = 0

        pbar = tqdm(pending, desc="insider_trading", unit="win",
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] +{postfix}")
        pbar.set_postfix_str("0 rows")

        for wf, wt in pbar:
            result = await fetch_window(session, limiter, wf, wt, seen, lock)

            if result is None:
                pbar.write(f"  [FAIL] {wf}-{wt} — will retry next run")
                continue

            if result:
                append_csv(result, first_write)
                first_write = False
                total_new += len(result)

            # Mark done + save progress
            done_w.add(f"{wf}_{wt}")
            save_progress(done_w)

            pbar.set_postfix_str(f"{total_new:,} rows")

            # Re-warm every 50 windows
            if len(done_w) % 50 == 0:
                try:
                    async with session.get("https://www.bseindia.com",
                                           timeout=aiohttp.ClientTimeout(total=15)):
                        pass
                except Exception:
                    pass

        pbar.close()

    # Final
    csv_rows = 0
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, encoding="utf-8") as f:
            csv_rows = sum(1 for _ in f) - 1

    print(f"\n{'='*60}")
    print(f"DONE — {total_new:,} new rows | {csv_rows:,} total in CSV")
    print(f"Output: {CSV_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
