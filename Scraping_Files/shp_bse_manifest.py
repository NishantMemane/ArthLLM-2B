"""
Step 2A: BSE Shareholding Pattern — Manifest Builder
=====================================================
Queries BSE announcements API with category = "Shareholding Pattern"
across date windows from Jan 2019 to Mar 2025, paginates through all results,
and builds a CSV manifest of all SHP PDF links.

Usage:
    python shp_bse_manifest.py
"""

import os
import sys
import time
import json
import random
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from tqdm import tqdm

# ─── Config ───────────────────────────────────────────────────────────────────
MANIFEST_FILE = Path("ArthLLM-2B") / "section3" / "shareholding" / "shp_manifest.csv"
PROGRESS_FILE = Path("ArthLLM-2B") / "section3" / "shareholding" / "shp_manifest_progress.json"

# BSE API — the hidden announcements endpoint
# strCat values found by inspecting BSE network tab:
#   "Shareholding Pattern" or "Sh. Holding" — we try both
BSE_API = "https://api.bseindia.com/BseIndiaAPI/api/AnnGetData/w"

# Date range: Jan 2019 — Mar 2025
START_DATE = datetime(2019, 1, 1)
END_DATE = datetime(2025, 3, 31)

# Window size in days (BSE returns max ~500 results per query, so use 30-day windows)
WINDOW_DAYS = 30

# Category strings to try (BSE uses inconsistent naming)
CATEGORIES = [
    "Shareholding Pattern",
    "Sh. Holding",
    "Shr. Pat.",
]


def get_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.bseindia.com/corporates/ann.html",
        "Origin": "https://www.bseindia.com",
    })
    try:
        session.get("https://www.bseindia.com", timeout=15)
    except:
        pass
    return session


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed_windows": [], "working_category": None}


def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def generate_windows():
    """Generate 30-day date windows from START to END."""
    windows = []
    current = START_DATE
    while current < END_DATE:
        window_end = min(current + timedelta(days=WINDOW_DAYS - 1), END_DATE)
        windows.append((current.strftime("%Y%m%d"), window_end.strftime("%Y%m%d")))
        current = window_end + timedelta(days=1)
    return windows


def detect_category(session):
    """Try each category string and see which one returns data."""
    test_from = "20240101"
    test_to = "20240131"
    
    for cat in CATEGORIES:
        params = {
            "strCat": cat,
            "strType": "C",
            "strScrip": "",
            "strSearch": "P",
            "strFromdt": test_from,
            "strTodt": test_to,
            "PageNo": "1",
        }
        try:
            resp = session.get(BSE_API, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict):
                    table = data.get("Table", [])
                elif isinstance(data, list):
                    table = data
                else:
                    table = []
                    
                if len(table) > 0:
                    print(f"  Category '{cat}' returned {len(table)} results ✓")
                    return cat
                else:
                    print(f"  Category '{cat}' returned 0 results")
        except Exception as e:
            print(f"  Category '{cat}' error: {e}")
        time.sleep(1)
    
    return None


def fetch_window(session, cat, from_dt, to_dt):
    """Fetch all pages of announcements for a date window."""
    all_records = []
    page = 1
    
    while True:
        params = {
            "strCat": cat,
            "strType": "C",
            "strScrip": "",
            "strSearch": "P",
            "strFromdt": from_dt,
            "strTodt": to_dt,
            "PageNo": str(page),
        }
        
        try:
            resp = session.get(BSE_API, params=params, timeout=30)
            
            if resp.status_code in [429, 503]:
                print(f"    Rate limited, waiting 60s...")
                time.sleep(60)
                continue
                
            if resp.status_code != 200:
                print(f"    HTTP {resp.status_code} on page {page}")
                break
                
            data = resp.json()
            
            if isinstance(data, dict):
                table = data.get("Table", [])
            elif isinstance(data, list):
                table = data
            else:
                break
                
            if not table:
                break
                
            for item in table:
                # Extract fields from BSE announcement JSON
                scrip_code = str(item.get("SCRIP_CD", item.get("scrip_cd", "")))
                company = item.get("SLONGNAME", item.get("COMPANY_NAME", ""))
                headline = item.get("HEADLINE", item.get("NEWS_HEADLINE", ""))
                dt_tm = item.get("DT_TM", item.get("NEWS_DT", ""))
                attachment = item.get("ATTACHMENTNAME", item.get("attachment", ""))
                news_id = item.get("NEWSID", item.get("news_id", ""))
                
                # Build PDF URL
                if attachment:
                    pdf_url = f"https://www.bseindia.com/xml-data/corpfiling/AttachLive/{attachment}"
                    alt_url = f"https://www.bseindia.com/xml-data/corpfiling/AttachHis/{attachment}"
                else:
                    pdf_url = ""
                    alt_url = ""
                
                all_records.append({
                    "scrip_code": scrip_code,
                    "company_name": company,
                    "headline": headline,
                    "filing_date": dt_tm,
                    "attachment_name": attachment,
                    "pdf_url": pdf_url,
                    "alt_pdf_url": alt_url,
                    "news_id": news_id,
                    "status": "pending",
                })
            
            page += 1
            time.sleep(1 + random.uniform(0.5, 1.5))
            
        except json.JSONDecodeError:
            print(f"    Invalid JSON on page {page}")
            break
        except Exception as e:
            print(f"    Error on page {page}: {e}")
            time.sleep(5)
            break
    
    return all_records


def main():
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    progress = load_progress()
    
    print("=" * 60)
    print("BSE Shareholding Pattern — Manifest Builder")
    print("=" * 60)
    
    session = get_session()
    
    # Detect working category
    cat = progress.get("working_category")
    if not cat:
        print("\nDetecting BSE category string...")
        cat = detect_category(session)
        if not cat:
            print("ERROR: Could not find a working category string.")
            print("Please inspect BSE network tab and update CATEGORIES list.")
            sys.exit(1)
        progress["working_category"] = cat
        save_progress(progress)
    print(f"Using category: '{cat}'")
    
    # Generate date windows
    windows = generate_windows()
    completed = set(progress.get("completed_windows", []))
    pending = [(f, t) for f, t in windows if f"{f}_{t}" not in completed]
    
    print(f"Total windows: {len(windows)}")
    print(f"Already done: {len(completed)}")
    print(f"Pending: {len(pending)}")
    
    # Load existing manifest if any
    if MANIFEST_FILE.exists():
        df_existing = pd.read_csv(MANIFEST_FILE, dtype=str)
        all_records = df_existing.to_dict("records")
        print(f"Existing manifest: {len(all_records)} records")
    else:
        all_records = []
    
    total_new = 0
    
    for i, (from_dt, to_dt) in enumerate(tqdm(pending, desc="Scanning BSE")):
        records = fetch_window(session, cat, from_dt, to_dt)
        if records:
            all_records.extend(records)
            total_new += len(records)
            tqdm.write(f"  {from_dt}–{to_dt}: {len(records)} filings found")
        
        # Mark window complete
        completed.add(f"{from_dt}_{to_dt}")
        progress["completed_windows"] = list(completed)
        save_progress(progress)
        
        # Save manifest every 10 windows
        if (i + 1) % 10 == 0:
            df = pd.DataFrame(all_records)
            df.to_csv(MANIFEST_FILE, index=False)
        
        time.sleep(2 + random.uniform(0.5, 2))
        
        # Re-warm session every 25 windows
        if (i + 1) % 25 == 0:
            try:
                session.get("https://www.bseindia.com", timeout=15)
            except:
                pass
    
    # Final save
    df = pd.DataFrame(all_records)
    df.drop_duplicates(subset=["pdf_url"], keep="first", inplace=True)
    df.to_csv(MANIFEST_FILE, index=False)
    
    print(f"\n{'='*60}")
    print(f"MANIFEST COMPLETE")
    print(f"Total records: {len(df)}")
    print(f"New records this run: {total_new}")
    print(f"Output: {MANIFEST_FILE}")


if __name__ == "__main__":
    main()
