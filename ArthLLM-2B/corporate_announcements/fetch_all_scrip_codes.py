"""
Phase 1 — Fetch All BSE Scrip Codes
=====================================
Loops all 16 BSE stock groups × 3 statuses (Active, Suspended, Delisted)
to build a comprehensive master file of all listed securities.

Output: all_scrip_codes.csv
Columns: scrip_code | company_name | group | segment | status | isin
Expected: ~7,000–8,000 unique scrip codes

Usage:
  python fetch_all_scrip_codes.py
"""

import requests
import csv
import time
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
OUTPUT   = BASE_DIR / "all_scrip_codes.csv"

# ─── BSE API (correct endpoint discovered via browser network capture) ───────
# Note: lowercase 'f' in 'Listof', params are case-sensitive
LIST_API = "https://api.bseindia.com/BseIndiaAPI/api/ListofScripData/w"

# All 16 BSE stock groups
GROUPS = ["A", "B", "E", "F", "G", "M", "MT", "P", "R", "S", "T", "W", "X", "XT", "Z", "ZP"]

# Status values (as the API expects them)
STATUSES = ["Active", "Suspended", "Delisted"]

# Segments to try
SEGMENTS = ["Equity"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bseindia.com/corporates/List_Scrips.html",
    "Origin": "https://www.bseindia.com",
}


def warm_session(sess):
    """Warm cookies so BSE accepts API requests."""
    print("  -> Warming session...", flush=True)
    try:
        sess.get("https://www.bseindia.com", timeout=15)
        time.sleep(1)
        sess.get("https://www.bseindia.com/corporates/List_Scrips.html", timeout=15)
        time.sleep(0.5)
        print("  [OK] Session ready", flush=True)
    except Exception as e:
        print(f"  [!] Warm-up warning: {e}", flush=True)


def fetch_group_status(sess, group, status, segment="Equity"):
    """
    Fetch securities for one group×status×segment combination.
    BSE API params (case-sensitive, discovered via browser network tab):
      Group, Scripcode, segment, status
    Returns list of dicts.
    """
    params = {
        "Group":      group,
        "Scripcode":  "",
        "segment":    segment,
        "status":     status,
    }

    try:
        r = sess.get(LIST_API, params=params, timeout=60)
        if r.status_code != 200:
            print(f"  [!] HTTP {r.status_code} for group={group} status={status}", flush=True)
            return []

        # Check if response is JSON
        ct = r.headers.get("Content-Type", "")
        if "json" not in ct.lower() and "text" not in ct.lower():
            return []

        data = r.json()
    except Exception as e:
        print(f"  [!] Error group={group} status={status}: {e}", flush=True)
        return []

    if not isinstance(data, list):
        return []

    results = []
    for item in data:
        # Try multiple possible field names for scrip code
        sc = str(
            item.get("SCRIP_CD", "") or
            item.get("Scrip_Code", "") or
            item.get("scrip_cd", "") or
            ""
        ).strip()
        if not sc or sc == "0":
            continue

        company_name = (
            item.get("Scrip_Name", "") or
            item.get("SLONGNAME", "") or
            item.get("LongName", "") or
            item.get("Issuer_Name", "") or
            item.get("scrip_name", "") or
            ""
        ).strip()

        isin = (
            item.get("ISIN_NUMBER", "") or
            item.get("ISIN", "") or
            item.get("Isin", "") or
            item.get("isin", "") or
            ""
        ).strip()

        seg = (
            item.get("Segment", "") or
            item.get("segment", "") or
            segment
        ).strip()

        grp = (
            item.get("GROUP", "") or
            item.get("Group", "") or
            group
        ).strip()

        sts = (
            item.get("Status", "") or
            item.get("status", "") or
            status
        ).strip()

        results.append({
            "scrip_code":   sc,
            "company_name": company_name,
            "group":        grp,
            "segment":      seg,
            "status":       sts,
            "isin":         isin,
        })
    return results


def load_existing_master():
    """Load existing bse_company_master.csv as fallback."""
    master_path = BASE_DIR / "bse_company_master.csv"
    if not master_path.exists():
        return {}

    companies = {}
    with open(master_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sc = row.get("scrip_code", "").strip()
            if sc:
                companies[sc] = {
                    "scrip_code":   sc,
                    "company_name": row.get("company_name", "").strip(),
                    "group":        "",
                    "segment":      "",
                    "status":       row.get("status", "Active").strip(),
                    "isin":         row.get("isin", "").strip(),
                }
    return companies


def main():
    print("=" * 60, flush=True)
    print("PHASE 1: FETCH ALL BSE SCRIP CODES", flush=True)
    print(f"API      : {LIST_API}", flush=True)
    print(f"Groups   : {len(GROUPS)} ({', '.join(GROUPS)})", flush=True)
    print(f"Statuses : {STATUSES}", flush=True)
    print("=" * 60, flush=True)

    sess = requests.Session()
    sess.headers.update(HEADERS)
    warm_session(sess)

    # Collect all companies by scrip_code (dedup)
    all_companies = {}
    total_calls = len(STATUSES) * len(GROUPS)
    call_num = 0

    for status in STATUSES:
        for group in GROUPS:
            call_num += 1
            label = f"[{call_num}/{total_calls}] group={group:3s} status={status}"

            rows = fetch_group_status(sess, group, status, "Equity")
            new_count = 0
            for r in rows:
                sc = r["scrip_code"]
                if sc not in all_companies:
                    all_companies[sc] = r
                    new_count += 1
                else:
                    # Update group/isin if missing
                    if r["group"] and not all_companies[sc]["group"]:
                        all_companies[sc]["group"] = r["group"]
                    if r["isin"] and not all_companies[sc]["isin"]:
                        all_companies[sc]["isin"] = r["isin"]

            print(f"  {label} -> {len(rows)} found, {new_count} new (total: {len(all_companies)})", flush=True)
            time.sleep(1.5)  # polite delay

        # Re-warm between statuses
        print("  -> Re-warming session...", flush=True)
        time.sleep(3)
        warm_session(sess)

    # If API returned very few results, merge with existing master
    api_count = len(all_companies)
    if api_count < 1000:
        print(f"\n  [!] API returned only {api_count} companies.", flush=True)
        print("  -> Merging with existing bse_company_master.csv...", flush=True)
        existing = load_existing_master()
        for sc, data in existing.items():
            if sc not in all_companies:
                all_companies[sc] = data
        print(f"  -> After merge: {len(all_companies)} unique companies", flush=True)
    else:
        # Still merge to capture any the API missed
        existing = load_existing_master()
        merged = 0
        for sc, data in existing.items():
            if sc not in all_companies:
                all_companies[sc] = data
                merged += 1
        if merged:
            print(f"  -> Merged {merged} extra companies from master CSV", flush=True)

    # Write output
    companies_list = sorted(
        all_companies.values(),
        key=lambda x: int(x["scrip_code"]) if x["scrip_code"].isdigit() else 0
    )

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["scrip_code", "company_name", "group", "segment", "status", "isin"])
        writer.writeheader()
        writer.writerows(companies_list)

    # Summary
    statuses = {}
    for c in companies_list:
        s = c["status"] or "Unknown"
        statuses[s] = statuses.get(s, 0) + 1

    print(f"\n{'='*60}", flush=True)
    print(f"OUTPUT: {OUTPUT}", flush=True)
    print(f"TOTAL : {len(companies_list)} unique scrip codes", flush=True)
    print(f"  From API  : {api_count:,}", flush=True)
    for s, cnt in sorted(statuses.items()):
        print(f"  {s:12s}: {cnt:,}", flush=True)
    print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    main()
