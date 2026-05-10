"""
NSE Insider Trading (PIT) Scraper — corporates-pit endpoint  (PRODUCTION)
Endpoint: /api/corporates-pit?from_date=DD-MM-YYYY&to_date=DD-MM-YYYY
Response: {"acqNameList": [...], "data": [...]}

Real field names (verified via probe):
  symbol, company, anex, acqName, date, pid, tkdAcqm,
  buyValue, sellValue, buyQuantity, sellquantity, secType, secAcq, did,
  tdpTransactionType, tdpDerivativeContractType, xbrl, personCategory,
  befAcqSharesNo, befAcqSharesPer, secVal, securitiesTypePost,
  afterAcqSharesNo, afterAcqSharesPer, acqfromDt, acqtoDt, intimDt,
  acqMode, derivativeType, exchange, remarks, xbrlFileSize

• 90-day windows (PIT is lower volume than announcements)
• 3 parallel sessions  •  0.4s delay
• Auto cookie refresh every 4 min
• Resume-safe: progress JSON + CSV dedup on pid
"""

import requests
import csv
import json
import os
import sys
import time
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── paths ──────────────────────────────────────────────────────────────────
BASE      = r"c:\Users\shree\Desktop\AA\ArthLLM-2B\nse_announcements"
LOGS      = os.path.join(BASE, "logs")
CSV_PATH  = os.path.join(BASE, "nse_insider_trading.csv")
PROG_PATH = os.path.join(LOGS, "nse_progress_insider.json")
os.makedirs(LOGS, exist_ok=True)

# ── config ─────────────────────────────────────────────────────────────────
API_URL        = "https://www.nseindia.com/api/corporates-pit"
HOMEPAGE       = "https://www.nseindia.com/"
REFERER_PAGE   = "https://www.nseindia.com/companies-listing/corporate-filings-insider-trading"

CONCURRENCY    = 3
MIN_DELAY      = 0.4
RETRY_WAIT     = 30
WINDOW_DAYS    = 90       # PIT is lower volume; 90 days is safe
FLUSH_EVERY    = 500
COOKIE_TTL     = 240      # seconds

START = datetime(2011, 1, 1)
END   = datetime(2026, 5, 8)

# No Accept-Encoding — let requests handle decompression
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

CSV_COLUMNS = [
    "symbol", "company", "regulation", "acquirer_name", "person_category",
    "transaction_type", "securities_type", "derivative_type",
    "securities_acquired", "securities_value",
    "buy_quantity", "buy_value", "sell_quantity", "sell_value",
    "before_acq_shares", "before_acq_pct",
    "after_acq_shares", "after_acq_pct",
    "acq_from_date", "acq_to_date", "intimation_date", "date",
    "acq_mode", "exchange", "remarks",
    "pid", "did", "xbrl_url", "status",
]


# ── NSE Session ────────────────────────────────────────────────────────────
class NSESession:
    def __init__(self, sid=0):
        self.id = sid
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.last_warm = 0
        self._warm_up()

    def _warm_up(self):
        try:
            self.session.get(HOMEPAGE, timeout=15)
            time.sleep(0.3)
            self.session.get(REFERER_PAGE, timeout=15)
            self.last_warm = time.monotonic()
        except Exception as e:
            print(f"  [S-{self.id}] warm-up warn: {e}")

    def get_json(self, url, params=None):
        if time.monotonic() - self.last_warm > COOKIE_TTL:
            self._warm_up()

        for attempt in range(3):
            try:
                time.sleep(MIN_DELAY)
                r = self.session.get(url, params=params, timeout=60)

                if r.status_code in (401, 403):
                    self._warm_up()
                    time.sleep(2)
                    continue
                if r.status_code == 429:
                    time.sleep(RETRY_WAIT * (attempt + 1))
                    continue
                if r.status_code != 200:
                    return None

                return r.json()
            except requests.exceptions.JSONDecodeError:
                return {"data": []}
            except Exception:
                if attempt == 2:
                    return None
                time.sleep(5 * (attempt + 1))
        return None


# ── helpers ────────────────────────────────────────────────────────────────
def make_windows():
    wins, cur = [], START
    while cur < END:
        w_end = min(cur + timedelta(days=WINDOW_DAYS - 1), END)
        wins.append((cur, w_end))
        cur = w_end + timedelta(days=1)
    return wins


def fmt_date(dt):
    return dt.strftime("%d-%m-%Y")


def wkey(f, t):
    return f"{f:%Y%m%d}_{t:%Y%m%d}"


def load_progress():
    if os.path.exists(PROG_PATH):
        with open(PROG_PATH) as f:
            return set(json.load(f).get("done_windows", []))
    return set()


def save_progress(done):
    tmp = PROG_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"done_windows": list(done),
                   "updated": datetime.now().isoformat()}, f)
    os.replace(tmp, PROG_PATH)


def load_seen():
    seen = set()
    if not os.path.exists(CSV_PATH):
        return seen
    try:
        with open(CSV_PATH, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pid = (row.get("pid") or "").strip()
                if pid:
                    seen.add(pid)
    except Exception:
        pass
    return seen


def clean(v):
    if v is None:
        return ""
    v = str(v).strip()
    return "" if v == "-" else v


def pit_to_row(a):
    """Convert NSE PIT record to CSV row."""
    return [
        clean(a.get("symbol")),
        clean(a.get("company")),
        clean(a.get("anex")),            # regulation e.g. "7(2)"
        clean(a.get("acqName")),          # acquirer/insider name
        clean(a.get("personCategory")),
        clean(a.get("tdpTransactionType")),
        clean(a.get("secType")),
        clean(a.get("derivativeType")),
        clean(a.get("secAcq")),           # securities acquired/disposed
        clean(a.get("secVal")),           # value of securities
        clean(a.get("buyQuantity")),
        clean(a.get("buyValue")),
        clean(a.get("sellquantity")),     # note: lowercase 'q' in NSE API
        clean(a.get("sellValue")),
        clean(a.get("befAcqSharesNo")),
        clean(a.get("befAcqSharesPer")),
        clean(a.get("afterAcqSharesNo")),
        clean(a.get("afterAcqSharesPer")),
        clean(a.get("acqfromDt")),
        clean(a.get("acqtoDt")),
        clean(a.get("intimDt")),
        clean(a.get("date")),
        clean(a.get("acqMode")),
        clean(a.get("exchange")),
        clean(a.get("remarks")),
        clean(a.get("pid")),              # unique filing ID
        clean(a.get("did")),
        clean(a.get("xbrl")),             # XBRL URL
        "scraped",
    ]


# ── CSV writer ─────────────────────────────────────────────────────────────
csv_lock = threading.Lock()
first_write_flag = True


def append_csv(rows):
    global first_write_flag
    with csv_lock:
        mode = "w" if first_write_flag else "a"
        with open(CSV_PATH, mode, newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if first_write_flag:
                w.writerow(CSV_COLUMNS)
                first_write_flag = False
            w.writerows(rows)


# ── main ───────────────────────────────────────────────────────────────────
def main():
    global first_write_flag
    print("=" * 65)
    print("NSE INSIDER TRADING (PIT) SCRAPER — corporates-pit endpoint")
    print(f"  Range       : Jan 2011 – May 2026")
    print(f"  Window      : {WINDOW_DAYS}d  |  Concurrency : {CONCURRENCY}")
    print(f"  Output      : {CSV_PATH}")
    print("=" * 65)

    done_w    = load_progress()
    seen      = load_seen()
    seen_lock = threading.Lock()
    windows   = make_windows()
    pending   = [(f, t) for f, t in windows if wkey(f, t) not in done_w]
    first_write_flag = not os.path.exists(CSV_PATH)

    print(f"  Windows  : {len(windows)} total, {len(pending)} pending")
    print(f"  Existing : {len(seen):,} dedup keys (pid)\n")

    if not pending:
        print("  All windows done!")
        return

    # create session pool
    sessions = []
    for i in range(CONCURRENCY):
        print(f"  Warming session {i+1}/{CONCURRENCY}...")
        sessions.append(NSESession(sid=i))
        time.sleep(1.5)
    print()

    total_new   = 0
    failed_w    = []
    buffer      = []
    buf_lock    = threading.Lock()
    done_lock   = threading.Lock()

    pbar = tqdm(total=len(pending), desc="nse_pit", unit="win",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} "
                           "[{elapsed}<{remaining}, {rate_fmt}]  +{postfix}")
    pbar.set_postfix_str("0 rows")

    def process(idx, wf, wt):
        nonlocal total_new
        s = sessions[idx % CONCURRENCY]
        params = {"from_date": fmt_date(wf),
                  "to_date": fmt_date(wt)}

        raw = s.get_json(API_URL, params)
        ok = raw is not None

        # Response is {"acqNameList": [...], "data": [...]}
        records = []
        if isinstance(raw, dict):
            records = raw.get("data", [])
            if not isinstance(records, list):
                records = []
        elif isinstance(raw, list):
            records = raw

        new_rows = []
        with seen_lock:
            for a in records:
                pid = str(a.get("pid") or "").strip()
                if not pid or pid in seen:
                    continue
                seen.add(pid)
                new_rows.append(pit_to_row(a))

        k = wkey(wf, wt)
        with done_lock:
            if ok:
                done_w.add(k)
            else:
                failed_w.append(k)

        flush_now = False
        rows_to_write = []
        with buf_lock:
            if new_rows:
                buffer.extend(new_rows)
                total_new += len(new_rows)
            if len(buffer) >= FLUSH_EVERY:
                rows_to_write = list(buffer)
                buffer.clear()
                flush_now = True

        if flush_now:
            append_csv(rows_to_write)
            save_progress(done_w)

        pbar.update(1)
        pbar.set_postfix_str(f"{total_new:,} rows")

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futs = {pool.submit(process, i, wf, wt): (wf, wt)
                for i, (wf, wt) in enumerate(pending)}
        for fut in as_completed(futs):
            try:
                fut.result()
            except Exception as e:
                wf, wt = futs[fut]
                print(f"\n  ERR {wf}-{wt}: {e}")

    # final flush
    if buffer:
        append_csv(buffer)
    save_progress(done_w)
    pbar.close()

    csv_rows = 0
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, encoding="utf-8") as f:
            csv_rows = sum(1 for _ in f) - 1

    print(f"\n{'='*65}")
    print(f"DONE — {total_new:,} new PIT rows  |  {csv_rows:,} total in CSV")
    if failed_w:
        print(f"  ⚠ {len(failed_w)} windows FAILED — re-run to retry")
        print(f"  {failed_w[:5]}{'...' if len(failed_w) > 5 else ''}")
    print(f"  Output : {CSV_PATH}")
    print("=" * 65)


if __name__ == "__main__":
    main()
