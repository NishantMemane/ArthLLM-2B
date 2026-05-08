"""
Phase 1 — Build CSV manifests of all BSE corporate announcement PDF links.
API only, no downloads. Test locally, run full on Colab.

Usage:
  python build_manifests.py buyback         # test one category
  python build_manifests.py                 # all 6 categories
  python build_manifests.py --status        # check CSV stats
"""
import requests, os, sys, json, time, random, csv
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = {
    "board_meetings":  "Board Meeting",
    "insider_trading": "Insider Trading/SAST",
    "dividend":        "Dividend",
    "bonus_splits":    "Sub-Division/Splits/Consolidation",
    "buyback":         "Buy Back",
    "demerger":        "Scheme of Arrangement/Amalgamation",
}

RATE_LIMIT  = 3
RETRY_WAIT  = 60
WINDOW_DAYS = 15

BSE_API  = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w"
PDF_LIVE = "https://www.bseindia.com/xml-data/corpfiling/AttachLive/{}"
PDF_HIST = "https://www.bseindia.com/xml-data/corpfiling/AttachHis/{}"

START = datetime(2011, 1, 1)
END   = datetime(2026, 5, 8)


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
        self._warm()

    def _warm(self):
        try:
            print("  Warming BSE session...", flush=True)
            self.s.get("https://www.bseindia.com", timeout=15)
            time.sleep(1)
            self.s.get("https://www.bseindia.com/corporates/ann.html", timeout=15)
            print("  Session ready.", flush=True)
        except Exception as e:
            print(f"  Warm-up warning: {e}", flush=True)

    def _wait(self):
        gap = time.time() - self.last
        if gap < RATE_LIMIT:
            time.sleep(RATE_LIMIT - gap + random.uniform(0.2, 0.8))
        self.last = time.time()

    def api(self, params):
        self._wait()
        r = self.s.get(BSE_API, params=params, timeout=60)
        if r.status_code in (429, 503):
            print(f"  Rate limited ({r.status_code}), waiting 60s...", flush=True)
            time.sleep(60)
            r = self.s.get(BSE_API, params=params, timeout=60)
        r.raise_for_status()
        return r.json()


def make_windows():
    wins, cur = [], START
    while cur < END:
        w_end = min(cur + timedelta(days=WINDOW_DAYS - 1), END)
        wins.append((cur.strftime("%Y%m%d"), w_end.strftime("%Y%m%d")))
        cur = w_end + timedelta(days=1)
    return wins


def load_prog(cat):
    p = LOGS_DIR / f"manifest_progress_{cat}.json"
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return {"done_windows": []}

def save_prog(cat, d):
    d["updated"] = datetime.now().isoformat()
    with open(LOGS_DIR / f"manifest_progress_{cat}.json", "w") as f:
        json.dump(d, f)


CSV_HEADER = ["scrip_code","company_name","category","attachment",
              "pdf_url","pdf_url_hist","filing_date","headline","status"]


def build_manifest(bse, cat_name, cat_filter):
    csv_path = BASE_DIR / f"{cat_name}.csv"
    prog = load_prog(cat_name)
    done_w = set(prog["done_windows"])

    # Create CSV if new
    if not csv_path.exists():
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(CSV_HEADER)

    # Load existing attachments for dedup
    seen = set()
    try:
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("attachment"):
                    seen.add(row["attachment"])
    except Exception:
        pass

    windows = make_windows()
    pending = [(f, t) for f, t in windows if f"{f}_{t}" not in done_w]

    print(f"\n{'='*60}", flush=True)
    print(f"  Category : {cat_name} ({cat_filter})", flush=True)
    print(f"  Windows  : {len(windows)} total, {len(pending)} pending", flush=True)
    print(f"  Existing : {len(seen)} rows in CSV", flush=True)
    print(f"  Output   : {csv_path}", flush=True)
    print(f"{'='*60}", flush=True)

    total_new = 0

    for wi, (wf, wt) in enumerate(pending):
        window_ok = False
        window_new = 0
        total_count = 0
        collected = 0
        page = 1

        while True:
            params = {
                "strCat": cat_filter, "strPrevDate": wf, "strScrip": "",
                "strSearch": "P", "strToDate": wt, "strType": "C",
                "strPageNo": str(page),
            }
            try:
                data = bse.api(params)
                window_ok = True
            except Exception as e:
                print(f"  [!] API error {wf}-{wt} p{page}: {e}", flush=True)
                time.sleep(RETRY_WAIT)
                try:
                    data = bse.api(params)
                    window_ok = True
                except Exception:
                    break

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

            # Build batch
            batch = []
            for ann in rows:
                att = (ann.get("ATTACHMENTNAME") or "").strip()
                if not att or att in seen:
                    continue
                seen.add(att)

                scrip = str(ann.get("SCRIP_CD", ""))
                company = (ann.get("SLONGNAME") or ann.get("SCRIP_NAME") or "").strip()
                headline = (ann.get("NEWSSUB") or "").strip()
                dt = (ann.get("DT_TM") or "").strip()

                batch.append([
                    scrip, company, cat_name, att,
                    PDF_LIVE.format(att), PDF_HIST.format(att),
                    dt, headline, "pending"
                ])

            if batch:
                with open(csv_path, "a", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerows(batch)
                window_new += len(batch)

            if total_count > 0 and collected >= total_count:
                break
            page += 1

        # Checkpoint
        if window_ok:
            done_w.add(f"{wf}_{wt}")
            prog["done_windows"] = list(done_w)
            save_prog(cat_name, prog)

        total_new += window_new

        if window_new > 0 or wi % 20 == 0:
            print(f"  [{wi+1}/{len(pending)}] {wf}-{wt} | "
                  f"p{page} pages | +{window_new} rows | total: {total_new}", flush=True)

        if (wi + 1) % 25 == 0:
            bse._warm()

    print(f"\n  [OK] {cat_name} DONE -- {total_new} new, {len(seen)} total in CSV", flush=True)
    return total_new


def show_status():
    windows = make_windows()
    total = 0
    print(f"{'Category':20s} {'Windows':>12s} {'CSV Rows':>10s} {'CSV Size':>12s}")
    print("-" * 58)
    for cat in CATEGORIES:
        p = load_prog(cat)
        w = len(p.get("done_windows", []))
        csv_path = BASE_DIR / f"{cat}.csv"
        rows, sz = 0, 0
        if csv_path.exists():
            sz = csv_path.stat().st_size
            with open(csv_path) as f:
                rows = sum(1 for _ in f) - 1
        total += rows
        print(f"{cat:20s} {w:>5d}/{len(windows):>5d}   {rows:>8,d}   {sz/1e6:>8.1f} MB")
    print("-" * 58)
    print(f"{'TOTAL':20s} {'':>12s} {total:>8,d}")


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--status":
            show_status()
            return
        if arg not in CATEGORIES:
            print(f"Unknown: {arg}")
            print(f"Available: {', '.join(CATEGORIES.keys())}")
            return
        cats = {arg: CATEGORIES[arg]}
    else:
        cats = CATEGORIES

    print("=" * 60, flush=True)
    print("BSE CORPORATE ANNOUNCEMENTS -- CSV MANIFEST BUILDER", flush=True)
    print(f"Categories : {len(cats)}", flush=True)
    print(f"Date range : Jan 2011 - May 2026", flush=True)
    print(f"Started    : {datetime.now()}", flush=True)
    print("=" * 60, flush=True)

    bse = BSE()
    grand = 0
    for name, filt in cats.items():
        try:
            grand += build_manifest(bse, name, filt)
        except KeyboardInterrupt:
            print(f"\n[!] Interrupted at {name}. Run again to resume.", flush=True)
            break
        except Exception as e:
            print(f"\n[X] {name} crashed: {e}", flush=True)
            import traceback; traceback.print_exc()

    print(f"\n{'='*60}", flush=True)
    print(f"DONE -- {grand:,} new rows added", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()
