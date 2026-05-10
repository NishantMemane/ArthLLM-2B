"""
NSE Shareholding Pattern — UNIFIED Scraper  (PRODUCTION v2)

Two-pass approach (following shp_master_plan.md):
  Pass 1: /api/corporate-announcements  → SHP filings + PDF URLs (date-windowed)
  Pass 2: /api/shareholding-patterns?symbol=X → structured % data (per-symbol)

Output: nse_shareholding.csv  (unified, resume-safe)

• 30-day windows (announcements) • per-symbol API (structured data)
• 3 parallel sessions (thread-local, no sharing)  •  0.5s delay  •  Resume-safe
"""

import csv, json, os, sys, re, time, threading, io
import socket
from curl_cffi import requests, CurlHttpVersion
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# ── Force IPv4 to bypass broken IPv6 routing to NSE Akamai ────────────────
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only_getaddrinfo(*args, **kwargs):
    return [r for r in _orig_getaddrinfo(*args, **kwargs) if r[0] == socket.AF_INET]
socket.getaddrinfo = _ipv4_only_getaddrinfo

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE      = r"c:\Users\shree\Desktop\AA\ArthLLM-2B\nse_announcements"
LOGS      = os.path.join(BASE, "logs")
CSV_PATH  = os.path.join(BASE, "nse_shareholding.csv")
PROG_PATH = os.path.join(LOGS, "nse_progress_shp.json")
os.makedirs(LOGS, exist_ok=True)

ANNOUNCE_URL = "https://www.nseindia.com/api/corporate-announcements"
SHP_API_URL  = "https://www.nseindia.com/api/corporate-share-holdings-master"
HOMEPAGE     = "https://www.nseindia.com/"
REFERER_ANN  = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"
REFERER_SHP  = "https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern"

CONCURRENCY = 3; MIN_DELAY = 0.5; RETRY_WAIT = 30; COOKIE_TTL = 240
FLUSH_EVERY = 500
START = datetime(2015, 1, 1); END = datetime(2026, 5, 8)

# ── BUG 2 FIX: Include Referer in default headers ─────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Referer": REFERER_ANN,
}

# ── Unified CSV columns ───────────────────────────────────────────────────
CSV_COLUMNS = [
    "source",                                     # "ANNOUNCEMENT" or "SHP_DATA"
    "symbol", "company", "isin", "industry",
    # Structured % data (populated by SHP_DATA rows)
    "quarter_end",
    "promoter_pct", "public_pct", "institutions_pct",
    "pledged_pct", "govt_pct",
    # Announcement metadata + PDF (populated by ANNOUNCEMENT rows)
    "seq_id", "filing_date", "sort_date",
    "desc", "announcement_text",
    "pdf_url", "file_size", "status",
]

# ── SHP Announcement Filters ──────────────────────────────────────────────
SHP_DESC = {
    "Shareholding Pattern", "Shareholding Patterns",
    "Reg. 31(1)(b)", "Reg. 31(1)(a)",
    "Shareholding pattern under Regulation 31 of SEBI",
}

SHP_KW = re.compile(
    r"shareholding\s*pattern|share\s*holding\s*pattern|"
    r"reg[ulation]*[\.\\s]*31|lodr.*(?:reg|regulation).*31|"
    r"promoter.*shareholding.*pattern|"
    r"pattern\s*of\s*shareholding",
    re.IGNORECASE,
)

def is_shp_ann(a):
    desc = (a.get("desc") or "").strip()
    if desc in SHP_DESC: return True
    for kw in SHP_DESC:
        if kw.lower() in desc.lower(): return True
    text = a.get("attchmntText") or ""
    return bool(SHP_KW.search(f"{desc} {text}"))

def clean(v):
    return "" if v is None else str(v).strip()

def clean_dash(v):
    v = (v or "").strip(); return "" if v == "-" else v


# ── NSE Session (BUG 5 FIX: warm-up lock) ─────────────────────────────────
class NSESession:
    def __init__(self, sid=0, referer=REFERER_ANN):
        self.id = sid; self.referer = referer
        self.session = requests.Session(impersonate="chrome110")
        self.session.headers.update(HEADERS)
        self.session.headers["Referer"] = referer
        self.last_warm = 0
        self._warm_lock = threading.Lock()                   # BUG 5 FIX
        self._warm_up()

    def _warm_up(self):
        with self._warm_lock:                                 # BUG 5 FIX
            if time.monotonic() - self.last_warm <= COOKIE_TTL and self.last_warm > 0:
                return  # another thread already refreshed
            try:
                self.session.get(HOMEPAGE, timeout=15, http_version=CurlHttpVersion.v1_1)
                time.sleep(0.3)
                self.session.get(self.referer, timeout=15, http_version=CurlHttpVersion.v1_1)
                self.last_warm = time.monotonic()
            except Exception as e:
                print(f"  [S-{self.id}] warm-up warn: {e}")

    def get_json(self, url, params=None):
        if time.monotonic() - self.last_warm > COOKIE_TTL:
            self._warm_up()
        for attempt in range(3):
            try:
                time.sleep(MIN_DELAY)
                r = self.session.get(
                    url, params=params, timeout=60,
                    headers={"Referer": self.referer},
                    http_version=CurlHttpVersion.v1_1,
                )
                if r.status_code in (401, 403):
                    self._warm_up(); time.sleep(2); continue
                if r.status_code == 429:
                    time.sleep(RETRY_WAIT * (attempt + 1)); continue
                if r.status_code != 200: return None
                return r.json()
            except ValueError:
                return None       # BUG 1 FIX: was returning [], now returns None
            except Exception:
                if attempt == 2: return None
                time.sleep(5 * (attempt + 1))
        return None


# ── BUG 4 FIX: Paginated fetch ────────────────────────────────────────────
def fetch_all_pages(session, url, base_params):
    """Fetch all pages from a paginated NSE endpoint."""
    all_records = []
    start = 0
    length = 500

    while True:
        params = {**base_params, "start": start, "length": length}
        raw = session.get_json(url, params)

        if raw is None:
            return None   # request failed

        if isinstance(raw, list):
            all_records.extend(raw)
            break   # plain list = no pagination
        elif isinstance(raw, dict):
            page_data = raw.get("data") or raw.get("corporateActions") or []
            if not isinstance(page_data, list):
                page_data = []
            total = raw.get("total", len(page_data))
            all_records.extend(page_data)
            start += length
            if start >= total or not page_data:
                break
        else:
            break

        time.sleep(MIN_DELAY)

    return all_records


# ── Row converters ─────────────────────────────────────────────────────────
def ann_to_row(a):
    """Announcement record → unified CSV row."""
    return [
        "ANNOUNCEMENT",
        clean(a.get("symbol")), clean(a.get("sm_name")),
        clean(a.get("sm_isin")), clean(a.get("smIndustry")),
        "", "", "", "", "", "",       # structured % fields (empty for announcements)
        clean(a.get("seq_id")), clean(a.get("an_dt")), clean(a.get("sort_date")),
        clean(a.get("desc")), clean(a.get("attchmntText")),
        clean(a.get("attchmntFile")),
        clean(a.get("attFileSize") or a.get("fileSize")),
        "scraped",
    ]

def shp_to_rows(symbol, company, data):
    """SHP API response → list of unified CSV rows (one per quarter)."""
    rows = []
    records = []
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        for key in ("data", "shareholdingPatterns", "shpData", "response"):
            if key in data and isinstance(data[key], list):
                records = data[key]; break

    for rec in records:
        if not isinstance(rec, dict): continue
        # Real NSE field names (discovered from live API):
        #   pr_and_prgrp = promoter & promoter group %
        #   public_val   = public shareholding %
        #   employeeTrusts = employee trusts %
        #   date         = quarter end e.g. "31-MAR-2026"
        #   xbrl         = XBRL XML download URL
        #   name         = company name
        promoter = _extract_pct(rec, ["pr_and_prgrp", "promoterAndPromoterGroup",
                                       "promoter", "promoterHolding",
                                       "totalPromoterHolding"])
        public = _extract_pct(rec, ["public_val", "publicShareholding", "public",
                                     "publicHolding", "totalPublicHolding"])
        institutions = _extract_pct(rec, ["institutions", "institutional",
                                           "institutionalHolding", "diiHolding",
                                           "totalInstitutions"])
        pledged = _extract_pct(rec, ["pledgedPercentage", "pledged", "pledgedPct",
                                      "promoterPledge", "sharesPledged",
                                      "pledgedPercentageWrtTotalShares"])
        govt = _extract_pct(rec, ["government", "govt", "governmentHolding"])
        emp_trust = _extract_pct(rec, ["employeeTrusts"])

        quarter = (rec.get("date") or rec.get("quarterEnd") or
                   rec.get("quarter") or rec.get("periodEnd") or "")
        comp_name = rec.get("name") or company or ""
        pdf = (rec.get("xbrl") or rec.get("pdfLink") or rec.get("pdfUrl") or
               rec.get("attchmntFile") or rec.get("xbrlLink") or "")

        if any([promoter, public, quarter]):
            rows.append([
                "SHP_DATA",
                symbol, comp_name, "", rec.get("industry", ""),
                str(quarter),
                promoter, public, institutions, pledged, govt,
                "", "", "",    # seq_id, filing_date, sort_date
                "", "",        # desc, announcement_text
                str(pdf), rec.get("xbrlFileSize", ""),
                "scraped",
            ])
    return rows

def _extract_pct(rec, keys):
    """Try multiple key names to extract a percentage value."""
    for k in keys:
        v = rec.get(k)
        if v is not None:
            try:
                return str(round(float(v), 2))
            except (ValueError, TypeError):
                if isinstance(v, str) and v.strip():
                    return v.strip()
    return ""


# ── CSV writer (BUG 6 FIX: first_write_flag always set before threads) ────
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


# ── Window & progress helpers ─────────────────────────────────────────────
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
        with open(PROG_PATH) as f: return json.load(f)
    return {"done_windows": [], "done_symbols": []}

def save_progress(prog):
    tmp = PROG_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump({**prog, "updated": datetime.now().isoformat()}, f)
    os.replace(tmp, PROG_PATH)


# ── BUG 3 FIX: Thread-local session factory ───────────────────────────────
_session_map = {}
_session_map_lock = threading.Lock()

def _get_thread_session(referer=REFERER_ANN):
    """Returns a session unique to the calling thread (double-checked locking)."""
    tid = threading.get_ident()
    key = (tid, referer)
    if key not in _session_map:
        with _session_map_lock:
            if key not in _session_map:
                _session_map[key] = NSESession(sid=tid % 10000, referer=referer)
    return _session_map[key]


# ── Pass 1: Announcements (date-windowed) ─────────────────────────────────
def run_announcements_pass(prog):
    global first_write_flag
    done_w = set(prog.get("done_windows", []))
    done_lock = threading.Lock()
    windows = make_windows(30)
    pending = [(f, t) for f, t in windows if wkey("ANN", f, t) not in done_w]

    print(f"\n  [PASS 1 — ANNOUNCEMENTS] {len(windows)} windows, {len(pending)} pending")
    if not pending:
        print("  All announcement windows done!"); return set()

    # BUG 6 FIX: set first_write_flag strictly BEFORE spawning any threads
    first_write_flag = not os.path.exists(CSV_PATH)

    total_new = 0; total_scan = 0; failed_w = []
    buffer = []; buf_lock = threading.Lock()

    # ── RESUME FIX: pre-populate seen seq_ids from existing CSV ──
    seen = set(); seen_lock = threading.Lock()
    if os.path.exists(CSV_PATH):
        try:
            with open(CSV_PATH, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    sid = (row.get("seq_id") or "").strip()
                    if sid: seen.add(sid)
            print(f"  ↻ Resume: loaded {len(seen):,} existing seq_ids (dedup)")
        except: pass

    discovered_symbols = set(); sym_lock = threading.Lock()

    pbar = tqdm(total=len(pending), desc="shp_announce", unit="win",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]  +{postfix}")
    pbar.set_postfix_str("0 rows")

    def process(idx, wf, wt):
        nonlocal total_new, total_scan
        s = _get_thread_session(referer=REFERER_ANN)      # BUG 3 FIX: thread-local
        params = {"index": "equities", "from_date": fmt_date(wf), "to_date": fmt_date(wt)}

        # BUG 4 FIX: use paginated fetch
        data = fetch_all_pages(s, ANNOUNCE_URL, params)

        # BUG 1 FIX: ok = isinstance check, not `is not None`
        ok = isinstance(data, list)
        anns = data if ok else []

        new_rows = []
        with seen_lock:
            total_scan += len(anns)
            for a in anns:
                if not is_shp_ann(a): continue
                sid = str(a.get("seq_id") or "").strip()
                if not sid or sid in seen: continue
                seen.add(sid); new_rows.append(ann_to_row(a))
                sym = (a.get("symbol") or "").strip()
                if sym:
                    with sym_lock:
                        discovered_symbols.add(sym)
        with done_lock:
            k = wkey("ANN", wf, wt)
            if ok: done_w.add(k)
            else: failed_w.append(k)
        rows_to_write = []
        with buf_lock:
            if new_rows: buffer.extend(new_rows); total_new += len(new_rows)
            if len(buffer) >= FLUSH_EVERY:
                rows_to_write = list(buffer); buffer.clear()
        if rows_to_write:
            append_csv(rows_to_write)
            with done_lock:                                  # BUG 7 FIX: snapshot under lock
                save_progress({**prog, "done_windows": list(done_w)})
        pbar.update(1); pbar.set_postfix_str(f"{total_new:,} shp / {total_scan:,} scanned")

    try:
        with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
            futs = {pool.submit(process, i, wf, wt): (wf, wt) for i, (wf, wt) in enumerate(pending)}
            for fut in as_completed(futs):
                try: fut.result()
                except Exception as e:
                    wf, wt = futs[fut]; print(f"\n  ERR {wf}-{wt}: {e}")
    except KeyboardInterrupt:
        print("\n  ⚠ Ctrl+C detected — flushing buffer and saving progress...")

    if buffer: append_csv(buffer)
    with done_lock:                                          # BUG 7 FIX
        prog["done_windows"] = list(done_w); save_progress(prog)
    pbar.close()

    if failed_w:
        print(f"  ⚠ {len(failed_w)} windows FAILED — re-run to retry")
    print(f"  Pass 1 done: +{total_new:,} announcement rows | {len(discovered_symbols):,} unique symbols found")
    return discovered_symbols


# ── Pass 2: Per-Symbol SHP API (structured %) ────────────────────────────
def run_shp_api_pass(symbols, prog):
    global first_write_flag
    done_sym = set(prog.get("done_symbols", []))
    done_lock = threading.Lock()
    pending = [s for s in sorted(symbols) if s not in done_sym]

    print(f"\n  [PASS 2 — SHP API] {len(symbols)} symbols total, {len(pending)} pending")
    if not pending:
        print("  All symbols done!"); return

    # BUG 6 FIX: set first_write_flag strictly BEFORE spawning any threads
    first_write_flag = not os.path.exists(CSV_PATH)

    total_new = 0; total_ok = 0; total_fail = 0
    buffer = []; buf_lock = threading.Lock()
    api_logged = False; api_log_lock = threading.Lock()

    pbar = tqdm(total=len(pending), desc="shp_api", unit="sym",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]  +{postfix}")
    pbar.set_postfix_str("0 rows")

    def process(idx, sym):
        nonlocal total_new, total_ok, total_fail, api_logged
        s = _get_thread_session(referer=REFERER_SHP)       # BUG 3 FIX: thread-local

        # Real NSE SHP endpoint (discovered via browser DevTools)
        data = s.get_json(SHP_API_URL, params={"index": "equities", "symbol": sym})

        # BUG 1 FIX: ok only when we got real data (not None from failed/decode-error)
        ok = data is not None
        new_rows = []
        if ok and data:
            # Log first response structure for debugging
            with api_log_lock:
                if not api_logged:
                    api_logged = True
                    log_file = os.path.join(LOGS, "shp_api_sample_response.json")
                    try:
                        with open(log_file, "w", encoding="utf-8") as f:
                            json.dump({"symbol": sym, "response": data}, f, indent=2, default=str)
                        print(f"\n  📝 API sample logged → {log_file}")
                    except: pass
            new_rows = shp_to_rows(sym, "", data)

        with done_lock:
            if ok:
                done_sym.add(sym); total_ok += 1
            else:
                total_fail += 1

        rows_to_write = []
        with buf_lock:
            if new_rows: buffer.extend(new_rows); total_new += len(new_rows)
            if len(buffer) >= FLUSH_EVERY:
                rows_to_write = list(buffer); buffer.clear()
        if rows_to_write:
            append_csv(rows_to_write)
            with done_lock:                                  # BUG 7 FIX: snapshot under lock
                prog["done_symbols"] = list(done_sym)
                save_progress(prog)
        pbar.update(1)
        pbar.set_postfix_str(f"{total_new:,} rows | {total_ok:,}✓ {total_fail:,}✗")

    try:
        with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
            futs = {pool.submit(process, i, sym): sym for i, sym in enumerate(pending)}
            for fut in as_completed(futs):
                try: fut.result()
                except Exception as e:
                    sym = futs[fut]; print(f"\n  ERR {sym}: {e}")
    except KeyboardInterrupt:
        print("\n  ⚠ Ctrl+C detected — flushing buffer and saving progress...")

    if buffer: append_csv(buffer)
    with done_lock:                                          # BUG 7 FIX
        prog["done_symbols"] = list(done_sym); save_progress(prog)
    pbar.close()

    print(f"  Pass 2 done: +{total_new:,} structured rows | {total_ok:,} OK / {total_fail:,} failed")


# ── main ───────────────────────────────────────────────────────────────────
def main():
    global first_write_flag
    print("=" * 65)
    print("NSE SHAREHOLDING PATTERN — UNIFIED SCRAPER  v2")
    print(f"  Pass 1 : Announcements + PDFs  (30-day windows, 2015–2026)")
    print(f"  Pass 2 : Per-symbol SHP API    (structured % data)")
    print(f"  Output : {CSV_PATH}")
    print("=" * 65)

    first_write_flag = not os.path.exists(CSV_PATH)
    prog = load_progress()

    # Pass 1 — Announcements → PDF URLs + discover symbols
    discovered = run_announcements_pass(prog)

    # Also collect symbols already in CSV (if re-running)
    if os.path.exists(CSV_PATH):
        try:
            with open(CSV_PATH, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    sym = (row.get("symbol") or "").strip()
                    if sym: discovered.add(sym)
        except: pass

    # Pass 2 — Per-symbol SHP API → structured percentage data
    if discovered:
        print(f"\n  Discovered {len(discovered):,} unique symbols from Pass 1")
        run_shp_api_pass(discovered, prog)
    else:
        print("\n  ⚠ No symbols discovered — skipping Pass 2")

    # Final stats
    csv_rows = 0; ann_count = 0; api_count = 0; pdf_count = 0
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                csv_rows += 1
                src = row.get("source", "")
                if src == "ANNOUNCEMENT": ann_count += 1
                elif src == "SHP_DATA": api_count += 1
                if (row.get("pdf_url") or "").startswith("http"): pdf_count += 1

    print(f"\n{'='*65}")
    print(f"DONE — {csv_rows:,} total rows in unified CSV")
    print(f"  ANNOUNCEMENT rows: {ann_count:,} ({pdf_count:,} with PDFs)")
    print(f"  SHP_DATA rows    : {api_count:,} (structured %)")
    print(f"  Output: {CSV_PATH}")
    print("=" * 65)


if __name__ == "__main__":
    main()
