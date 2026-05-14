"""
Step 1: NSE Shareholding Pattern — Bulk CSV Download
=====================================================
Downloads quarterly CSV files from NSE's corporate filings page.
24 quarters (Q1 FY2020 → Q4 FY2025) = 24 CSV files.
Each CSV has summary-level data (Promoter%, FII%, DII%, Public%) for ALL NSE-listed companies.

Usage:
    python shp_nse_csv_bulk.py
"""

import os
import sys
import time
import json
import random
import requests
from pathlib import Path
from datetime import datetime

# ─── Config ───────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path("ArthLLM-2B") / "section3" / "shareholding" / "nse_csv"
PROGRESS_FILE = OUTPUT_DIR / "nse_csv_progress.json"

# NSE shareholding pattern API endpoint (discovered via network inspection)
# This returns JSON with shareholding data; we also try the CSV download endpoint
NSE_BASE = "https://www.nseindia.com"
NSE_API = "https://www.nseindia.com/api/corporates-shareholding"

# Quarter definitions: (quarter_label, from_date, to_date)
# NSE uses quarter-end dates for filtering
QUARTERS = []
for year in range(2019, 2026):
    for q, (m_start, m_end, d_end) in enumerate([
        ("04", "06", "30"),  # Q1 (Apr-Jun)
        ("07", "09", "30"),  # Q2 (Jul-Sep)
        ("10", "12", "31"),  # Q3 (Oct-Dec)
        ("01", "03", "31"),  # Q4 (Jan-Mar) — next calendar year for FY
    ], 1):
        if q == 4:
            cal_year = year + 1
        else:
            cal_year = year
        fy = year + 1
        label = f"Q{q}FY{fy}"
        qtr_end = f"{cal_year}-{m_end}-{d_end}"
        
        # Skip future quarters
        if datetime.strptime(qtr_end, "%Y-%m-%d") > datetime.now():
            continue
        # Start from FY2020
        if fy < 2020:
            continue
            
        QUARTERS.append((label, qtr_end))


def get_nse_session():
    """Create a session with proper NSE cookies."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern",
    })
    # Hit main page to get cookies
    try:
        r = session.get(NSE_BASE, timeout=15)
        print(f"  NSE homepage: {r.status_code}")
        time.sleep(2)
        # Hit the shareholding page to warm up
        r2 = session.get(
            f"{NSE_BASE}/companies-listing/corporate-filings-shareholding-pattern",
            timeout=15
        )
        print(f"  SHP page: {r2.status_code}")
        time.sleep(1)
    except Exception as e:
        print(f"  Warning: Could not warm up NSE session: {e}")
    return session


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}


def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def download_quarter_csv(session, label, quarter_end, progress):
    """Download the shareholding pattern CSV for a single quarter."""
    if progress.get(label) == "downloaded":
        print(f"  [{label}] Already downloaded, skipping")
        return True

    output_file = OUTPUT_DIR / f"shp_{label}.csv"
    
    # NSE API params — try multiple known patterns
    # Pattern 1: Direct API with quarter param
    urls_to_try = [
        f"{NSE_API}?index=equities&from_date=&to_date=&quarter={quarter_end}",
        f"{NSE_API}?index=equities&quarter={quarter_end}",
        f"https://www.nseindia.com/api/corporate-shareholding?index=equities&quarter_end={quarter_end}",
    ]
    
    for attempt, url in enumerate(urls_to_try):
        try:
            time.sleep(3 + random.uniform(1, 3))
            resp = session.get(url, timeout=30)
            
            if resp.status_code == 401:
                print(f"  [{label}] 401 — session expired, refreshing...")
                session.get(NSE_BASE, timeout=15)
                time.sleep(2)
                resp = session.get(url, timeout=30)
            
            if resp.status_code == 200:
                content_type = resp.headers.get("Content-Type", "")
                
                if "json" in content_type or resp.text.strip().startswith(("[", "{")):
                    # JSON response — save as JSON and also convert to CSV
                    data = resp.json()
                    json_file = OUTPUT_DIR / f"shp_{label}.json"
                    with open(json_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    # Try to flatten to CSV
                    try:
                        import pandas as pd
                        if isinstance(data, list):
                            df = pd.DataFrame(data)
                        elif isinstance(data, dict) and "data" in data:
                            df = pd.DataFrame(data["data"])
                        else:
                            df = pd.DataFrame([data])
                        df.to_csv(output_file, index=False)
                        print(f"  [{label}] JSON → CSV saved ({len(df)} rows)")
                    except Exception as e:
                        print(f"  [{label}] JSON saved, CSV conversion failed: {e}")
                    
                    progress[label] = "downloaded"
                    save_progress(progress)
                    return True
                    
                elif "csv" in content_type or "text" in content_type:
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(resp.text)
                    lines = resp.text.strip().count("\n")
                    print(f"  [{label}] CSV saved ({lines} rows)")
                    progress[label] = "downloaded"
                    save_progress(progress)
                    return True
                else:
                    print(f"  [{label}] Unexpected content-type: {content_type} (attempt {attempt+1})")
            else:
                print(f"  [{label}] HTTP {resp.status_code} (attempt {attempt+1})")
                
        except Exception as e:
            print(f"  [{label}] Error (attempt {attempt+1}): {e}")
    
    progress[label] = "failed"
    save_progress(progress)
    return False


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    progress = load_progress()
    
    print("=" * 60)
    print("NSE Shareholding Pattern — Bulk CSV Download")
    print(f"Quarters to process: {len(QUARTERS)}")
    print(f"Already done: {sum(1 for v in progress.values() if v == 'downloaded')}")
    print("=" * 60)
    
    session = get_nse_session()
    
    success = 0
    failed = 0
    
    for i, (label, qtr_end) in enumerate(QUARTERS, 1):
        print(f"\n[{i}/{len(QUARTERS)}] {label} (quarter end: {qtr_end})")
        if download_quarter_csv(session, label, qtr_end, progress):
            success += 1
        else:
            failed += 1
        
        # Re-warm session every 8 quarters
        if i % 8 == 0:
            print("  Refreshing NSE session...")
            session = get_nse_session()
    
    print(f"\n{'='*60}")
    print(f"DONE: {success} success, {failed} failed out of {len(QUARTERS)}")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
