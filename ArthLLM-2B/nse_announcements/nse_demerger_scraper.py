"""
NSE Demerger — UNIFIED Scraper  (PRODUCTION)
Two-pass approach:
  Pass 1: /api/corporates-corporateActions → structured data
  Pass 2: /api/corporate-announcements   → PDF URLs + announcement text
Filters: "Scheme of Arrangement", "Demerger", "Amalgamation"
Post-filter keeps only demerger-related rows.

Merges both into a single CSV: nse_demerger.csv

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
CSV_PATH  = os.path.join(BASE, "nse_demerger.csv")
PROG_PATH = os.path.join(LOGS, "nse_progress_demerger.json")
os.makedirs(LOGS, exist_ok=True)

ACTIONS_URL  = "https://www.nseindia.com/api/corporates-corporateActions"
ANNOUNCE_URL = "https://www.nseindia.com/api/corporate-announcements"
HOMEPAGE     = "https://www.nseindia.com/"
REFERER_ACT  = "https://www.nseindia.com/companies-listing/corporate-filings-actions"
REFERER_ANN  = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"

CONCURRENCY = 3; MIN_DELAY = 0.4; RETRY_WAIT = 30; COOKIE_TTL = 240
FLUSH_EVERY = 500
START = datetime(2010, 1, 1); END = datetime(2026, 5, 8)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9", "Connection": "keep-alive",
}

CSV_COLUMNS = [
    "source",
    "symbol", "company", "series", "isin", "industry",
    "subject", "category",
    "ex_date", "record_date", "bc_start_date", "bc_end_date",
    "face_value", "broadcast_date",
    "seq_id", "filing_date", "sort_date",
    "desc", "announcement_text",
    "pdf_url", "file_size", "status",
]

# ── Filters ────────────────────────────────────────────────────────────────
# Pass 1 (Actions): broad catch on subject
DEMERGER_ACTION_KW = re.compile(
    r"demerger|de[\s-]*merger|scheme\s*of\s*arrange|"
    r"amalgamat|demerge|restructur|"
    r"composite\s*scheme|arrangement.*nclt|"
    r"hive[\s-]*off|spin[\s-]*off|separation",
    re.IGNORECASE,
)

# Pass 2 (Announcements): desc categories + keyword filter
DEMERGER_DESC = {
    "Scheme of Arrangement",
    "Amalgamation / Merger / Demerger",
    "Demerger",
}

DEMERGER_ANN_KW = re.compile(
    r"demerger|de[\s-]*merger|demerge[ds]?\s|"
    r"scheme\s*of\s*arrange|composite\s*scheme|"
    r"hive[\s-]*off|spin[\s-]*off|"
    r"demerged\s*(?:undertaking|company|entity)|"
    r"nclt.*(?:scheme|arrangement)|"
    r"restructur.*scheme|separation.*business",
    re.IGNORECASE,
)

# Negative filter: drop rows that are ONLY merger/amalgamation without demerger
DEMERGER_POSITIVE = re.compile(r"demerger|de[\s-]*merger|demerge|hive.?off|spin.?off", re.IGNORECASE)
MERGER_ONLY = re.compile(r"^(merger|amalgamation|takeover)$", re.IGNORECASE)

def classify_category(text):
    t = (text or "").upper()
    if "DEMERGER" in t or "DE-MERGER" in t or "DE MERGER" in t:
        return "DEMERGER"
    if "SCHEME" in t and "ARRANGEMENT" in t:
        return "SCHEME_OF_ARRANGEMENT"
    if "AMALGAM" in t or "MERGER" in t:
        return "AMALGAMATION_MERGER"
    if "HIVE" in t or "SPIN" in t:
        return "DEMERGER"
    if "RESTRUCTUR" in t:
        return "RESTRUCTURING"
    return "DEMERGER"

def is_demerger_action(subject):
    return bool(DEMERGER_ACTION_KW.search(subject or ""))

def is_demerger_ann(a):
    desc = (a.get("desc") or "").strip()
    text = a.get("attchmntText") or ""
    combined = f"{desc} {text}"
    # Direct desc match
    if desc in DEMERGER_DESC:
        return True
    # Keyword match
    if DEMERGER_ANN_KW.search(combined):
        return True
    return False

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
        subject, classify_category(subject),
        clean_dash(a.get("exDate") or ""), clean_dash(a.get("recDate") or ""),
        clean_dash(a.get("bcStartDate") or ""), clean_dash(a.get("bcEndDate") or ""),
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
    return [
        "ANNOUNCEMENT",
        clean(a.get("symbol")), clean(a.get("sm_name")),
        "", clean(a.get("sm_isin")), clean(a.get("smIndustry")),
        "", classify_category(f"{desc} {text}"),
        "", "", "", "",    # dates
        "", "",            # face_value, broadcast_date
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


# ── main ───────────────────────────────────────────────────────────────────
def main():
    global first_write_flag
    print("=" * 65)
    print("NSE DEMERGER — UNIFIED SCRAPER")
    print(f"  Pass 1 : Corporate Actions  (90-day windows)")
    print(f"  Pass 2 : Announcements + PDFs (30-day windows)")
    print(f"  Range  : Jan 2010 – May 2026")
    print(f"  Output : {CSV_PATH}")
    print("=" * 65)

    first_write_flag = not os.path.exists(CSV_PATH)
    done_w = load_progress()

    # Pass 1: Corporate Actions
    run_pass(
        pass_name="ACTIONS", api_url=ACTIONS_URL, referer=REFERER_ACT,
        window_days=90,
        filter_fn=lambda a: is_demerger_action((a.get("subject") or "")),
        row_fn=action_to_row,
        dedup_fn=lambda a: f"A|{clean(a.get('symbol'))}|{clean_dash(a.get('exDate') or '')}|{(a.get('subject') or '')[:50]}",
        done_w=done_w,
    )

    # Pass 2: Announcements + PDFs
    run_pass(
        pass_name="ANNOUNCE", api_url=ANNOUNCE_URL, referer=REFERER_ANN,
        window_days=30,
        filter_fn=is_demerger_ann,
        row_fn=ann_to_row,
        dedup_fn=lambda a: f"P|{str(a.get('seq_id') or '').strip()}",
        done_w=done_w,
    )

    # Final stats
    csv_rows = 0; pdf_count = 0; act_count = 0
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                csv_rows += 1
                if row.get("source") == "ACTION": act_count += 1
                if (row.get("pdf_url") or "").startswith("http"): pdf_count += 1

    print(f"\n{'='*65}")
    print(f"DONE — {csv_rows:,} total rows in unified CSV")
    print(f"  ACTION rows      : {act_count:,} (structured data)")
    print(f"  ANNOUNCEMENT rows: {csv_rows - act_count:,} ({pdf_count:,} with PDFs)")
    print(f"  Output: {CSV_PATH}")
    print("=" * 65)


if __name__ == "__main__":
    main()
