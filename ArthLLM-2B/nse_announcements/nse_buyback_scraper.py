"""
NSE Buyback — UNIFIED Scraper  (PRODUCTION)
Two-pass approach:
  Pass 1: /api/corporates-corporateActions → structured data (price, dates, etc.)
  Pass 2: /api/corporate-announcements   → PDF URLs + announcement text
Merges both into a single CSV: nse_buyback.csv

• 90-day windows (actions) + 30-day windows (announcements)
• 3 parallel sessions  •  0.4s delay  •  Resume-safe
"""

import requests, csv, json, os, sys, re, time, threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE      = r"c:\Users\shree\Desktop\AA\ArthLLM-2B\nse_announcements"
LOGS      = os.path.join(BASE, "logs")
CSV_PATH  = os.path.join(BASE, "nse_buyback.csv")
PROG_PATH = os.path.join(LOGS, "nse_progress_buyback.json")
os.makedirs(LOGS, exist_ok=True)

ACTIONS_URL = "https://www.nseindia.com/api/corporates-corporateActions"
ANNOUNCE_URL = "https://www.nseindia.com/api/corporate-announcements"
HOMEPAGE     = "https://www.nseindia.com/"
REFERER_ACT  = "https://www.nseindia.com/companies-listing/corporate-filings-actions"
REFERER_ANN  = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"

CONCURRENCY = 3; MIN_DELAY = 0.4; RETRY_WAIT = 30; COOKIE_TTL = 240
FLUSH_EVERY = 500
START = datetime(2013, 1, 1); END = datetime(2026, 5, 8)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9", "Connection": "keep-alive",
}

CSV_COLUMNS = [
    "source",
    "symbol", "company", "series", "isin", "industry",
    "subject", "buyback_type",
    "record_date", "open_date", "close_date",
    "buyback_price", "issue_size_shares", "issue_size_amount_cr",
    "face_value", "broadcast_date",
    "seq_id", "filing_date", "sort_date",
    "desc", "announcement_text",
    "pdf_url", "file_size", "status",
]

# ── Filters ────────────────────────────────────────────────────────────────
BUYBACK_DESC = {"Buyback", "Buy Back", "Buy-Back"}

BUYBACK_KW = re.compile(
    r"buy\s*back|buyback|buy[\s-]*back.*shares|"
    r"tender\s*offer.*buy|sebi.*buyback|"
    r"buyback\s*regulat|repurchase.*shares|"
    r"buy[\s-]*back.*equity|offer\s*for\s*buy[\s-]*back",
    re.IGNORECASE,
)

PRICE_RE  = re.compile(r"(?:@|at)\s*(?:Rs\.?\s*|₹\s*)([0-9,]+(?:\.\d+)?)", re.IGNORECASE)
AMT_RE    = re.compile(r"(?:Rs\.?\s*|₹\s*)([0-9,]+(?:\.\d+)?)\s*(?:cr|crore)", re.IGNORECASE)
SHARES_RE = re.compile(r"([0-9,]+)\s*(?:equity\s*)?shares", re.IGNORECASE)

def is_buyback_action(subject):
    p = (subject or "").upper()
    return "BUYBACK" in p or "BUY BACK" in p or "BUY-BACK" in p

def is_buyback_ann(a):
    desc = (a.get("desc") or "").strip()
    if desc in BUYBACK_DESC: return True
    text = a.get("attchmntText") or ""
    return bool(BUYBACK_KW.search(f"{desc} {text}"))

def classify_buyback(subject):
    p = (subject or "").upper()
    if "TENDER" in p: return "TENDER"
    if "OPEN MARKET" in p or "OPEN-MARKET" in p: return "OPEN_MARKET"
    return "BUYBACK"

def parse_price(s):
    m = PRICE_RE.search(s or ""); return m.group(1).replace(",", "") if m else ""
def parse_amount(s):
    m = AMT_RE.search(s or ""); return m.group(1).replace(",", "") if m else ""
def parse_shares(s):
    m = SHARES_RE.search(s or ""); return m.group(1).replace(",", "") if m else ""

def clean_dash(v):
    v = (v or "").strip(); return "" if v == "-" else v
def clean(v):
    return "" if v is None else str(v).strip()


# ── NSE Session ────────────────────────────────────────────────────────────
class NSESession:
    def __init__(self, sid=0, referer=REFERER_ACT):
        self.id = sid; self.referer = referer
        self.session = requests.Session()
        self.session.headers.update(HEADERS); self.last_warm = 0; self._warm_up()

    def _warm_up(self):
        try:
            self.session.get(HOMEPAGE, timeout=15); time.sleep(0.3)
            self.session.get(self.referer, timeout=15)
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
                    self._warm_up(); time.sleep(2); continue
                if r.status_code == 429:
                    time.sleep(RETRY_WAIT * (attempt + 1)); continue
                if r.status_code != 200: return None
                return r.json()
            except requests.exceptions.JSONDecodeError: return []
            except Exception:
                if attempt == 2: return None
                time.sleep(5 * (attempt + 1))
        return None


# ── Row converters ─────────────────────────────────────────────────────────
def action_to_row(a):
    subject = (a.get("subject") or "").strip()
    return [
        "ACTION",
        clean(a.get("symbol")), clean(a.get("comp")),
        clean(a.get("series")), clean(a.get("isin")), "",
        subject, classify_buyback(subject),
        clean_dash(a.get("recDate") or ""),
        clean_dash(a.get("bcStartDate") or ""),
        clean_dash(a.get("bcEndDate") or ""),
        parse_price(subject), parse_shares(subject), parse_amount(subject),
        str(a.get("faceVal") or "").strip(),
        clean(a.get("caBroadcastDate")),
        "", "", "",    # seq_id, filing_date, sort_date
        "", "",        # desc, announcement_text
        "", "",        # pdf_url, file_size
        "scraped",
    ]

def ann_to_row(a):
    desc = clean(a.get("desc"))
    text = clean(a.get("attchmntText"))
    combined = f"{desc} {text}"
    return [
        "ANNOUNCEMENT",
        clean(a.get("symbol")), clean(a.get("sm_name")),
        "", clean(a.get("sm_isin")), clean(a.get("smIndustry")),
        "", classify_buyback(combined),
        "", "", "",                          # dates
        parse_price(combined), parse_shares(combined), parse_amount(combined),
        "", "",                              # face_value, broadcast_date
        clean(a.get("seq_id")), clean(a.get("an_dt")), clean(a.get("sort_date")),
        desc, text,
        clean(a.get("attchmntFile")),
        clean(a.get("attFileSize") or a.get("fileSize")),
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
                w.writerow(CSV_COLUMNS); first_write_flag = False
            w.writerows(rows)


# ── Window helpers ─────────────────────────────────────────────────────────
def make_windows(days):
    wins, cur = [], START
    while cur < END:
        w_end = min(cur + timedelta(days=days - 1), END)
        wins.append((cur, w_end)); cur = w_end + timedelta(days=1)
    return wins

def fmt_date(dt): return dt.strftime("%d-%m-%Y")
def wkey(prefix, f, t): return f"{prefix}_{f:%Y%m%d}_{t:%Y%m%d}"

def load_progress():
    if os.path.exists(PROG_PATH):
        with open(PROG_PATH) as f: return set(json.load(f).get("done_windows", []))
    return set()

def save_progress(done):
    tmp = PROG_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"done_windows": list(done), "updated": datetime.now().isoformat()}, f)
    os.replace(tmp, PROG_PATH)


# ── Generic pass runner ───────────────────────────────────────────────────
def run_pass(pass_name, api_url, referer, window_days, filter_fn, row_fn, dedup_fn, done_w):
    global first_write_flag
    windows = make_windows(window_days)
    pending = [(f, t) for f, t in windows if wkey(pass_name, f, t) not in done_w]

    print(f"\n  [{pass_name}] {len(windows)} windows, {len(pending)} pending")
    if not pending:
        print(f"  [{pass_name}] All done!"); return 0

    sessions = []
    for i in range(CONCURRENCY):
        sessions.append(NSESession(sid=i, referer=referer)); time.sleep(1)

    total_new = 0; total_scan = 0; failed_w = []
    buffer = []; buf_lock = threading.Lock(); done_lock = threading.Lock()
    seen = set(); seen_lock = threading.Lock()

    pbar = tqdm(total=len(pending), desc=pass_name, unit="win",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]  +{postfix}")
    pbar.set_postfix_str("0 rows")

    def process(idx, wf, wt):
        nonlocal total_new, total_scan
        s = sessions[idx % CONCURRENCY]
        params = {"index": "equities", "from_date": fmt_date(wf), "to_date": fmt_date(wt)}
        data = s.get_json(api_url, params)
        ok = data is not None
        records = data if isinstance(data, list) else []
        new_rows = []
        with seen_lock:
            total_scan += len(records)
            for a in records:
                if not filter_fn(a): continue
                k = dedup_fn(a)
                if not k or k in seen: continue
                seen.add(k); new_rows.append(row_fn(a))
        with done_lock:
            k2 = wkey(pass_name, wf, wt)
            if ok: done_w.add(k2)
            else: failed_w.append(k2)
        rows_to_write = []
        with buf_lock:
            if new_rows: buffer.extend(new_rows); total_new += len(new_rows)
            if len(buffer) >= FLUSH_EVERY:
                rows_to_write = list(buffer); buffer.clear()
        if rows_to_write: append_csv(rows_to_write); save_progress(done_w)
        pbar.update(1); pbar.set_postfix_str(f"{total_new:,} rows / {total_scan:,} scanned")

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futs = {pool.submit(process, i, wf, wt): (wf, wt) for i, (wf, wt) in enumerate(pending)}
        for fut in as_completed(futs):
            try: fut.result()
            except Exception as e:
                wf, wt = futs[fut]; print(f"\n  ERR {wf}-{wt}: {e}")

    if buffer: append_csv(buffer)
    save_progress(done_w); pbar.close()
    if failed_w:
        print(f"  [{pass_name}] ⚠ {len(failed_w)} windows FAILED — re-run to retry")
    print(f"  [{pass_name}] +{total_new:,} new rows")
    return total_new


def main():
    global first_write_flag
    print("=" * 65)
    print("NSE BUYBACK — UNIFIED SCRAPER")
    print(f"  Pass 1 : Corporate Actions  (90-day windows)")
    print(f"  Pass 2 : Announcements + PDFs (30-day windows)")
    print(f"  Range  : Jan 2013 – May 2026")
    print(f"  Output : {CSV_PATH}")
    print("=" * 65)

    first_write_flag = not os.path.exists(CSV_PATH)
    done_w = load_progress()

    run_pass(
        pass_name="ACTIONS", api_url=ACTIONS_URL, referer=REFERER_ACT,
        window_days=90,
        filter_fn=lambda a: is_buyback_action((a.get("subject") or "")),
        row_fn=action_to_row,
        dedup_fn=lambda a: f"A|{clean(a.get('symbol'))}|{clean_dash(a.get('recDate') or '')}",
        done_w=done_w,
    )

    run_pass(
        pass_name="ANNOUNCE", api_url=ANNOUNCE_URL, referer=REFERER_ANN,
        window_days=30,
        filter_fn=is_buyback_ann,
        row_fn=ann_to_row,
        dedup_fn=lambda a: f"P|{str(a.get('seq_id') or '').strip()}",
        done_w=done_w,
    )

    csv_rows = 0; pdf_count = 0; act_count = 0
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                csv_rows += 1
                if row.get("source") == "ACTION": act_count += 1
                if (row.get("pdf_url") or "").startswith("http"): pdf_count += 1

    print(f"\n{'='*65}")
    print(f"DONE — {csv_rows:,} total rows in unified CSV")
    print(f"  ACTION rows      : {act_count:,}")
    print(f"  ANNOUNCEMENT rows: {csv_rows - act_count:,} ({pdf_count:,} with PDFs)")
    print(f"  Output: {CSV_PATH}")
    print("=" * 65)


if __name__ == "__main__":
    main()
