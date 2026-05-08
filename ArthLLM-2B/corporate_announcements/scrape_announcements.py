"""
BSE Corporate Announcements PDF Scraper
=======================================
6 categories | Jan 2011 - May 2026 | ~468,000 filings

Categories:
  1. Board Meeting           -> "Board Meeting"            ~180,000
  2. Insider Trading          -> "Insider Trading/SAST"     ~250,000
  3. Dividend                 -> "Dividend"                 ~30,000
  4. Bonus / Split            -> "Sub-Division/Splits/Consolidation" ~2,000
  5. Buyback                  -> "Buy Back"                 ~1,200
  6. Demerger                 -> "Scheme of Arrangement/Amalgamation" ~5,000

PDF URLs:
  2015-2026 (live):    bseindia.com/xml-data/corpfiling/AttachLive/{FILE}
  2011-2014 (archive): bseindia.com/xml-data/corpfiling/AttachHis/{FILE}

Usage:
  python scrape_announcements.py                  # all 6 categories
  python scrape_announcements.py board_meetings   # single category
  python scrape_announcements.py --status         # show progress
"""

import requests
import os
import sys
import json
import time
import random
import hashlib
import csv
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# --- PATHS ---
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"

# --- 6 CATEGORIES ---
CATEGORIES = {
    "board_meetings":  "Board Meeting",
    "insider_trading": "Insider Trading/SAST",
    "dividend":        "Dividend",
    "bonus_splits":    "Sub-Division/Splits/Consolidation",
    "buyback":         "Buy Back",
    "demerger":        "Scheme of Arrangement/Amalgamation",
}

# --- RULES ---
RATE_LIMIT      = 3
PAUSE_EVERY     = 100
PAUSE_SECS      = 30
RETRY_WAIT      = 60
SESSION_BUDGET  = 11 * 3600  # 11 hours — stop before Colab's 12hr kill
MIN_FILE_SIZE   = 30720     # 30 KB
WINDOW_DAYS     = 15

BSE_API  = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w"
PDF_LIVE = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/{}"
PDF_HIST = "https://www.bseindia.com/xml-data/corpfiling/AttachHis/{}"

START = datetime(2011, 1, 1)
END   = datetime(2026, 5, 8)


# === SESSION ===
class BSE:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.bseindia.com/corporates/ann.html",
            "Origin": "https://www.bseindia.com",
        })
        self.last = 0
        self.dl_count = 0
        self._warm()

    def _warm(self):
        try:
            print("  -> Warming BSE session...", flush=True)
            self.s.get("https://www.bseindia.com", timeout=15)
            time.sleep(1)
            self.s.get("https://www.bseindia.com/corporates/ann.html", timeout=15)
            print("  [OK] Session ready", flush=True)
        except Exception as e:
            print(f"  [!] Warm-up warning: {e}", flush=True)

    def _wait(self):
        gap = time.time() - self.last
        if gap < RATE_LIMIT:
            time.sleep(RATE_LIMIT - gap + random.uniform(0.2, 0.8))
        self.last = time.time()

    def _pause(self):
        self.dl_count += 1
        if self.dl_count % PAUSE_EVERY == 0:
            print(f"  || Cooling {PAUSE_SECS}s after {self.dl_count} downloads...", flush=True)
            time.sleep(PAUSE_SECS)

    def api(self, params):
        self._wait()
        r = self.s.get(BSE_API, params=params, timeout=60)
        if r.status_code in (429, 503):
            print(f"  [!] Rate limited ({r.status_code}), waiting 60s...", flush=True)
            time.sleep(60)
            r = self.s.get(BSE_API, params=params, timeout=60)
        r.raise_for_status()
        return r.json()

    def get_pdf(self, url):
        self._wait()
        r = self.s.get(url, timeout=120)
        if r.status_code == 403:
            self._warm()
            time.sleep(5)
            self._wait()
            r = self.s.get(url, timeout=120)
        r.raise_for_status()
        return r.content


# === LOGGING ===
class Logger:
    def __init__(self):
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self._dl = LOGS_DIR / "download_log.csv"
        self._fail = LOGS_DIR / "failed_downloads.log"

        if not self._dl.exists():
            with open(self._dl, "w", newline="") as f:
                csv.writer(f).writerow(["timestamp","category","scrip","filename","url","bytes","md5"])

        if not self._fail.exists():
            with open(self._fail, "w") as f:
                f.write(f"# Failed Downloads -- {datetime.now()}\n")

        self.hashes = set()
        try:
            with open(self._dl, "r") as f:
                for row in csv.DictReader(f):
                    if row.get("md5"):
                        self.hashes.add(row["md5"])
        except Exception:
            pass

    def ok(self, cat, scrip, fname, url, sz, md5):
        with open(self._dl, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([datetime.now().isoformat(), cat, scrip, fname, url, sz, md5])
        self.hashes.add(md5)

    def fail(self, cat, url, err):
        with open(self._fail, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {cat} | {url} | {err}\n")

    def is_dup(self, md5):
        return md5 in self.hashes


# === DONE ATTACHMENTS — flat text file (not JSON) to avoid bloat ===
def load_done_attach(cat):
    p = LOGS_DIR / f"done_attach_{cat}.txt"
    if p.exists():
        with open(p) as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def append_done_attach(cat, att):
    with open(LOGS_DIR / f"done_attach_{cat}.txt", "a") as f:
        f.write(att + "\n")


# === WINDOW PROGRESS — small JSON, no attachment list ===
def _pfile(cat):
    return LOGS_DIR / f"progress_{cat}.json"

def load_progress(cat):
    p = _pfile(cat)
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return {"done_windows": [], "total_dl": 0}

def save_progress(cat, d):
    d["updated"] = datetime.now().isoformat()
    with open(_pfile(cat), "w") as f:
        json.dump(d, f)


# === DATE WINDOWS ===
def make_windows():
    wins = []
    cur = START
    while cur < END:
        w_end = min(cur + timedelta(days=WINDOW_DAYS - 1), END)
        wins.append((cur.strftime("%Y%m%d"), w_end.strftime("%Y%m%d")))
        cur = w_end + timedelta(days=1)
    return wins


# === CORE SCRAPER ===
def scrape_category(bse, logger, cat_name, cat_filter, session_start=None):
    out_dir = BASE_DIR / cat_name
    out_dir.mkdir(parents=True, exist_ok=True)

    if session_start is None:
        session_start = time.time()

    prog = load_progress(cat_name)
    done_wins = set(prog["done_windows"])
    done_a = load_done_attach(cat_name)
    total_dl = prog["total_dl"]

    windows = make_windows()
    pending = [(f, t) for f, t in windows if f"{f}_{t}" not in done_wins]

    print(f"\n{'='*60}", flush=True)
    print(f"  Category : {cat_name}", flush=True)
    print(f"  Filter   : {cat_filter}", flush=True)
    print(f"  Windows  : {len(windows)} total, {len(pending)} pending", flush=True)
    print(f"  Resumed  : {len(done_a)} attach done, {total_dl} PDFs saved", flush=True)
    print(f"  Output   : {out_dir}", flush=True)
    print(f"{'='*60}", flush=True)

    for wi, (w_from, w_to) in enumerate(pending):
        # Session budget check
        elapsed = time.time() - session_start
        if elapsed > SESSION_BUDGET:
            print(f"\n  [!] Session budget ({SESSION_BUDGET//3600}h) reached. Re-run to continue.", flush=True)
            return total_dl

        window_dl = 0
        window_ok = False
        total_count = 0
        collected = 0

        # --- PAGINATE through all pages (BSE returns ~20 per page) ---
        page = 1
        while True:
            params = {
                "strCat":      cat_filter,
                "strPrevDate": w_from,
                "strScrip":    "",
                "strSearch":   "P",
                "strToDate":   w_to,
                "strType":     "C",
                "strPageNo":   str(page),
            }

            try:
                data = bse.api(params)
                window_ok = True
            except Exception as e:
                logger.fail(cat_name, f"API {w_from}-{w_to} p{page}", str(e))
                time.sleep(RETRY_WAIT)
                try:
                    data = bse.api(params)
                    window_ok = True
                except Exception as e2:
                    logger.fail(cat_name, f"API RETRY {w_from}-{w_to} p{page}", str(e2))
                    break  # move to next window

            rows = []
            if isinstance(data, dict) and "Table" in data:
                rows = data["Table"]
            elif isinstance(data, list):
                rows = data

            # On page 1, grab total count from Table1 if available
            if page == 1:
                total_count = 0
                collected = 0
                if isinstance(data, dict) and "Table1" in data:
                    try:
                        total_count = int(data["Table1"][0]["ROWCNT"])
                    except Exception:
                        pass

            if not rows:
                break  # no more pages

            collected += len(rows)

            for ann in rows:
                att = (ann.get("ATTACHMENTNAME") or "").strip()
                if not att or att in done_a:
                    continue

                scrip = str(ann.get("SCRIP_CD", ""))
                save_path = out_dir / att

                if save_path.exists():
                    done_a.add(att)
                    append_done_attach(cat_name, att)
                    continue

                # Download: try AttachLive then AttachHis, track which worked
                content = None
                used_url = None
                for url in [PDF_LIVE.format(att), PDF_HIST.format(att)]:
                    try:
                        content = bse.get_pdf(url)
                        used_url = url
                        break
                    except Exception as e:
                        logger.fail(cat_name, url, str(e))

                if content is None:
                    # Final retry on live
                    time.sleep(RETRY_WAIT)
                    try:
                        content = bse.get_pdf(PDF_LIVE.format(att))
                        used_url = PDF_LIVE.format(att)
                    except Exception:
                        pass

                # Connection failure: do NOT blacklist, will retry next run
                if content is None:
                    continue

                # HTML check BEFORE size check — log error pages properly
                if b"<html" in content[:500].lower() or b"<!doctype" in content[:500].lower():
                    logger.fail(cat_name, att, "HTML not PDF")
                    done_a.add(att)
                    append_done_attach(cat_name, att)
                    continue

                # Size filter (permanent skip)
                if len(content) < MIN_FILE_SIZE:
                    done_a.add(att)
                    append_done_attach(cat_name, att)
                    continue

                md5 = hashlib.md5(content).hexdigest()
                if logger.is_dup(md5):
                    done_a.add(att)
                    append_done_attach(cat_name, att)
                    continue

                # Save
                with open(save_path, "wb") as f:
                    f.write(content)

                logger.ok(cat_name, scrip, att, used_url, len(content), md5)
                done_a.add(att)
                append_done_attach(cat_name, att)
                total_dl += 1
                window_dl += 1
                bse._pause()

            # Stop if we've collected all rows per ROWCNT
            if total_count > 0 and collected >= total_count:
                break

            page += 1
        # --- end pagination ---

        # Only mark window done if at least one page succeeded
        if window_ok:
            done_wins.add(f"{w_from}_{w_to}")
            prog["done_windows"] = list(done_wins)
            prog["total_dl"] = total_dl
            save_progress(cat_name, prog)

        if window_dl > 0 or wi % 20 == 0:
            print(f"  [{wi+1}/{len(pending)}] {w_from}-{w_to} | "
                  f"+{window_dl} PDFs | total: {total_dl}", flush=True)

        if (wi + 1) % 25 == 0:
            bse._warm()

    print(f"\n  [OK] {cat_name} DONE -- {total_dl} PDFs in {out_dir}", flush=True)
    return total_dl


# === ENTRY ===
def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--status":
            print("Progress:")
            wins = make_windows()
            for cat in CATEGORIES:
                p = load_progress(cat)
                da = load_done_attach(cat)
                print(f"  {cat:20s}  windows={len(p.get('done_windows',[]))}/{len(wins)}  "
                      f"pdfs={p.get('total_dl',0)}  attach_done={len(da)}")
            return
        if arg == "--list":
            for k, v in CATEGORIES.items():
                print(f"  {k:20s} -> {v}")
            return
        if arg not in CATEGORIES:
            print(f"Unknown: {arg}")
            print(f"Available: {', '.join(CATEGORIES.keys())}")
            return
        cats = {arg: CATEGORIES[arg]}
    else:
        cats = CATEGORIES

    print("=" * 60, flush=True)
    print("BSE CORPORATE ANNOUNCEMENTS -- PDF SCRAPER", flush=True)
    print(f"Categories : {len(cats)}", flush=True)
    print(f"Date       : Jan 2011 - May 2026", flush=True)
    print(f"Started    : {datetime.now()}", flush=True)
    print("=" * 60, flush=True)

    bse = BSE()
    logger = Logger()
    session_start = time.time()

    grand = 0
    for name, filt in cats.items():
        try:
            grand += scrape_category(bse, logger, name, filt, session_start=session_start)
        except KeyboardInterrupt:
            print(f"\n[!] Interrupted at {name}. Run again to resume.", flush=True)
            break
        except Exception as e:
            print(f"\n[X] {name} crashed: {e}", flush=True)
            import traceback; traceback.print_exc()

    print(f"\n{'='*60}", flush=True)
    print(f"DONE -- {grand:,} PDFs downloaded", flush=True)
    print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    main()
