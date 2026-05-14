"""
NSE Shareholding Pattern — XBRL XML Downloader
================================================
Step 1: Downloads quarterly CSVs from NSE API (all quarters 2019-2025)
Step 2: Extracts XBRL XML URLs from those CSVs
Step 3: Downloads all XBRL XML files with 20 concurrent workers

Also supports manually placed CSVs in the input folder.

Usage:
    python shp_nse_xbrl_downloader.py

Output structure:
    ArthLLM-2B/section3/shareholding/
        nse_csv/          <- quarterly CSVs
        nse_xbrl/         <- downloaded XML files organized by quarter
        shp_nse_manifest.csv  <- master manifest with download status
"""

import os
import sys
import time
import random
import json
import glob
import hashlib
import requests
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import concurrent.futures
import threading

# ─── Config ───────────────────────────────────────────────────────────────────
BASE_DIR = Path("ArthLLM-2B") / "section3" / "shareholding"
CSV_DIR = BASE_DIR / "nse_csv"
XBRL_DIR = BASE_DIR / "nse_xbrl"
MANIFEST_FILE = BASE_DIR / "shp_nse_manifest.csv"
PROGRESS_FILE = BASE_DIR / "nse_progress.json"

MAX_WORKERS = 20
SAVE_INTERVAL = 200
DELAY_BASE = 0.5
DELAY_JITTER = 1.0

# NSE API
NSE_BASE = "https://www.nseindia.com"
NSE_SHP_API = "https://www.nseindia.com/api/corporates-shareholding"

# Quarter definitions: (label, from_date, to_date) in DD-MM-YYYY for NSE
QUARTERS = []
for year in range(2019, 2026):
    for q, (m_start, d_start, m_end, d_end) in enumerate([
        ("01", "01", "03", "31"),  # Q4 prev FY (Jan-Mar)
        ("04", "01", "06", "30"),  # Q1 (Apr-Jun)
        ("07", "01", "09", "30"),  # Q2 (Jul-Sep)
        ("10", "01", "12", "31"),  # Q3 (Oct-Dec)
    ], 1):
        from_dt = f"01-{m_start}-{year}"
        to_dt = f"{d_end}-{m_end}-{year}"

        # Normalize to YYYY-QN
        if q == 1:
            fy_label = f"{year-1}-{year}_Q4"
        elif q == 2:
            fy_label = f"{year}-{year+1}_Q1"
        elif q == 3:
            fy_label = f"{year}-{year+1}_Q2"
        else:
            fy_label = f"{year}-{year+1}_Q3"

        # Skip future
        from datetime import datetime
        try:
            end_date = datetime.strptime(to_dt, "%d-%m-%Y")
            if end_date > datetime.now():
                continue
        except:
            continue

        if year < 2019 or (year == 2019 and q == 1):
            continue

        QUARTERS.append((fy_label, from_dt, to_dt))

# ─── Locks ────────────────────────────────────────────────────────────────────
manifest_lock = threading.Lock()
save_lock = threading.Lock()
stats_lock = threading.Lock()
thread_local = threading.local()

stats = {"attempted": 0, "success": 0, "failed": 0, "skipped": 0}


# ─── Session ──────────────────────────────────────────────────────────────────
def get_nse_session():
    """Create NSE session with proper cookies."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern",
    })
    try:
        r = session.get(NSE_BASE, timeout=15)
        print(f"  NSE warmup: {r.status_code}")
        time.sleep(2)
    except Exception as e:
        print(f"  NSE warmup failed: {e}")
    return session


def get_download_session():
    """Per-thread session for XBRL downloads (nsearchives doesn't need cookies)."""
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
        thread_local.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        })
    return thread_local.session


# ─── Step 1: Download quarterly CSVs ─────────────────────────────────────────
def download_quarterly_csvs(session, progress):
    """Try to download CSVs from NSE API for each quarter."""
    print("\n" + "=" * 60)
    print("STEP 1: Downloading quarterly CSVs from NSE")
    print("=" * 60)

    CSV_DIR.mkdir(parents=True, exist_ok=True)
    downloaded_qtrs = progress.get("csvs_downloaded", [])

    for label, from_dt, to_dt in QUARTERS:
        if label in downloaded_qtrs:
            print(f"  [{label}] Already have CSV, skipping")
            continue

        csv_file = CSV_DIR / f"shp_{label}.csv"
        if csv_file.exists() and csv_file.stat().st_size > 100:
            print(f"  [{label}] CSV exists on disk, skipping")
            downloaded_qtrs.append(label)
            continue

        # Try NSE API
        params = {
            "index": "equities",
            "from_date": from_dt,
            "to_date": to_dt,
        }

        try:
            time.sleep(3 + random.uniform(1, 3))
            resp = session.get(NSE_SHP_API, params=params, timeout=30)

            if resp.status_code == 401:
                print(f"  [{label}] 401 — refreshing session...")
                session.get(NSE_BASE, timeout=15)
                time.sleep(3)
                resp = session.get(NSE_SHP_API, params=params, timeout=30)

            if resp.status_code == 200:
                ct = resp.headers.get("Content-Type", "")
                body = resp.text.strip()

                if body.startswith(("[", "{")):
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        df = pd.DataFrame(data)
                        df.to_csv(csv_file, index=False)
                        print(f"  [{label}] JSON → CSV ({len(df)} rows)")
                        downloaded_qtrs.append(label)
                    elif isinstance(data, dict) and "data" in data:
                        df = pd.DataFrame(data["data"])
                        df.to_csv(csv_file, index=False)
                        print(f"  [{label}] JSON.data → CSV ({len(df)} rows)")
                        downloaded_qtrs.append(label)
                    else:
                        print(f"  [{label}] Empty response")
                elif "," in body and len(body) > 100:
                    with open(csv_file, "w", encoding="utf-8") as f:
                        f.write(resp.text)
                    print(f"  [{label}] Direct CSV saved")
                    downloaded_qtrs.append(label)
                else:
                    print(f"  [{label}] Unexpected response ({len(body)} bytes)")
            else:
                print(f"  [{label}] HTTP {resp.status_code}")

        except Exception as e:
            print(f"  [{label}] Error: {e}")

        # Refresh session every 8 quarters
        if len(downloaded_qtrs) % 8 == 0 and len(downloaded_qtrs) > 0:
            print("  Refreshing session...")
            try:
                session.get(NSE_BASE, timeout=15)
                time.sleep(2)
            except:
                pass

    progress["csvs_downloaded"] = downloaded_qtrs
    save_progress(progress)
    return downloaded_qtrs


# ─── Step 2: Build manifest from all CSVs ────────────────────────────────────
def build_manifest():
    """Parse all available CSVs and extract XBRL URLs into a single manifest."""
    print("\n" + "=" * 60)
    print("STEP 2: Building manifest from CSVs")
    print("=" * 60)

    all_records = []

    # Scan CSV_DIR for any CSVs
    csv_files = list(CSV_DIR.glob("*.csv"))

    # Also check Downloads folder for manually downloaded CSVs
    downloads = Path(os.path.expanduser("~")) / "Downloads"
    manual_csvs = list(downloads.glob("CF-Shareholding-Pattern*.csv"))
    if manual_csvs:
        print(f"  Found {len(manual_csvs)} manual CSVs in Downloads:")
        for mc in manual_csvs:
            print(f"    {mc.name}")
            # Copy to CSV_DIR
            import shutil
            dest = CSV_DIR / mc.name
            if not dest.exists():
                shutil.copy2(mc, dest)
                csv_files.append(dest)

    print(f"  Total CSVs to process: {len(csv_files)}")

    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, dtype=str)
            # Find the column with XML/XBRL URLs
            url_col = None
            for col in df.columns:
                if "ACTION" in col.upper() or "URL" in col.upper() or "XBRL" in col.upper():
                    url_col = col
                    break
            if not url_col:
                # Check if any column has nsearchives URLs
                for col in df.columns:
                    sample = df[col].dropna().head(5).tolist()
                    if any("nsearchives" in str(s) for s in sample):
                        url_col = col
                        break

            if not url_col:
                print(f"  [{csv_file.name}] No URL column found, skipping")
                continue

            # Find company column
            co_col = None
            for col in df.columns:
                if "COMPANY" in col.upper() or "NAME" in col.upper():
                    co_col = col
                    break
            if not co_col:
                co_col = df.columns[0]

            # Find date column
            date_col = None
            for col in df.columns:
                if "AS ON" in col.upper() or "DATE" in col.upper():
                    date_col = col
                    break

            count = 0
            for _, row in df.iterrows():
                url = str(row.get(url_col, "")).strip()
                if not url or url == "nan" or "nsearchives" not in url:
                    continue

                company = str(row.get(co_col, "")).strip()
                as_on = str(row.get(date_col, "")).strip() if date_col else ""
                promoter = str(row.get([c for c in df.columns if "PROMOTER" in c.upper()][0], "")) if any("PROMOTER" in c.upper() for c in df.columns) else ""
                public = str(row.get([c for c in df.columns if "PUBLIC" in c.upper()][0], "")) if any("PUBLIC" in c.upper() for c in df.columns) else ""

                # Extract filename for dedup
                filename = url.split("/")[-1]

                all_records.append({
                    "company": company,
                    "as_on_date": as_on,
                    "promoter_pct": promoter,
                    "public_pct": public,
                    "xbrl_url": url,
                    "filename": filename,
                    "source_csv": csv_file.name,
                    "status": "pending",
                })
                count += 1

            print(f"  [{csv_file.name}] {count} XBRL URLs extracted")

        except Exception as e:
            print(f"  [{csv_file.name}] Error: {e}")

    if not all_records:
        print("\n  NO XBRL URLs found. Place NSE CSVs in:")
        print(f"    {CSV_DIR}")
        print("  Or download from: https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern")
        return None

    df_manifest = pd.DataFrame(all_records)
    df_manifest.drop_duplicates(subset=["filename"], keep="first", inplace=True)

    # Merge with existing manifest to preserve download status
    if MANIFEST_FILE.exists():
        df_old = pd.read_csv(MANIFEST_FILE, dtype=str)
        # Keep old statuses
        old_status = dict(zip(df_old["filename"], df_old["status"]))
        df_manifest["status"] = df_manifest["filename"].map(
            lambda f: old_status.get(f, "pending")
        )

    df_manifest.to_csv(MANIFEST_FILE, index=False)
    print(f"\n  Manifest: {len(df_manifest)} unique XBRL files")
    print(f"  Pending:  {(df_manifest['status'] == 'pending').sum()}")
    print(f"  Done:     {(df_manifest['status'] == 'downloaded').sum()}")

    return df_manifest


# ─── Step 3: Download XBRL XMLs ──────────────────────────────────────────────
def download_xbrl(row, total):
    """Download a single XBRL XML file."""
    idx = row["index"]
    url = str(row.get("xbrl_url", ""))
    filename = str(row.get("filename", ""))
    status = str(row.get("status", "pending"))
    company = str(row.get("company", "unknown"))

    with stats_lock:
        stats["attempted"] += 1

    if status == "downloaded":
        with stats_lock:
            stats["skipped"] += 1
        return idx, "downloaded"

    if not url or url == "nan":
        with stats_lock:
            stats["failed"] += 1
        return idx, "failed"

    # Organize by quarter from filename or as_on_date
    as_on = str(row.get("as_on_date", ""))
    quarter_folder = "unknown"
    if as_on and as_on != "nan":
        try:
            from datetime import datetime as dt
            for fmt in ["%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d"]:
                try:
                    d = dt.strptime(as_on, fmt)
                    m = d.month
                    y = d.year
                    if m <= 3:
                        quarter_folder = f"{y-1}-{y}_Q4"
                    elif m <= 6:
                        quarter_folder = f"{y}-{y+1}_Q1"
                    elif m <= 9:
                        quarter_folder = f"{y}-{y+1}_Q2"
                    else:
                        quarter_folder = f"{y}-{y+1}_Q3"
                    break
                except:
                    continue
        except:
            pass

    out_dir = XBRL_DIR / quarter_folder
    out_dir.mkdir(parents=True, exist_ok=True)
    filepath = out_dir / filename

    if filepath.exists() and filepath.stat().st_size > 100:
        with stats_lock:
            stats["skipped"] += 1
        return idx, "downloaded"

    time.sleep(DELAY_BASE + random.uniform(0, DELAY_JITTER))

    session = get_download_session()

    for attempt in range(3):
        try:
            resp = session.get(url, timeout=45)

            if resp.status_code in [429, 503]:
                time.sleep(30)
                continue

            if resp.status_code == 200:
                content = resp.content
                if len(content) < 50:
                    with stats_lock:
                        stats["failed"] += 1
                    return idx, "failed"

                with open(filepath, "wb") as f:
                    f.write(content)

                size_kb = len(content) / 1024
                with stats_lock:
                    stats["success"] += 1
                    sc = stats["success"]
                tqdm.write(f"  OK {sc}/{total} | {company[:30]} | {size_kb:.0f}KB")
                return idx, "downloaded"
            else:
                if attempt == 2:
                    with stats_lock:
                        stats["failed"] += 1
                    return idx, "failed"

        except requests.exceptions.RequestException:
            if attempt < 2:
                time.sleep(3)
            continue

    with stats_lock:
        stats["failed"] += 1
    return idx, "failed"


# ─── Progress ────────────────────────────────────────────────────────────────
def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}


def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    XBRL_DIR.mkdir(parents=True, exist_ok=True)
    progress = load_progress()

    print("=" * 60)
    print("NSE Shareholding Pattern — XBRL Downloader")
    print(f"Workers: {MAX_WORKERS}")
    print("=" * 60)

    # Step 1: Try to get CSVs from NSE API
    session = get_nse_session()
    download_quarterly_csvs(session, progress)

    # Step 2: Build manifest from all available CSVs
    df = build_manifest()
    if df is None or len(df) == 0:
        print("\nNothing to download. Exiting.")
        sys.exit(0)

    # Step 3: Download XBRL XMLs
    print("\n" + "=" * 60)
    print("STEP 3: Downloading XBRL XML files")
    print("=" * 60)

    df = df.reset_index()
    to_download = df[df["status"] != "downloaded"].to_dict("records")
    total = len(to_download)
    already = len(df) - total

    print(f"  Total in manifest: {len(df)}")
    print(f"  Already downloaded: {already}")
    print(f"  Pending: {total}")

    if total == 0:
        print("  All done!")
        return

    counter = 0
    with tqdm(total=total, desc="Downloading XBRL") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(download_xbrl, row, total): row
                for row in to_download
            }

            for future in concurrent.futures.as_completed(futures):
                idx, status = future.result()

                with manifest_lock:
                    df.loc[df["index"] == idx, "status"] = status

                pbar.update(1)
                counter += 1

                if counter >= SAVE_INTERVAL:
                    with save_lock:
                        try:
                            df.drop(columns=["index"]).to_csv(MANIFEST_FILE, index=False)
                        except:
                            pass
                    counter = 0

    # Final save
    df.drop(columns=["index"]).to_csv(MANIFEST_FILE, index=False)

    print(f"\n{'=' * 60}")
    print("FINAL SUMMARY")
    print(f"  Attempted:  {stats['attempted']}")
    print(f"  Success:    {stats['success']}")
    print(f"  Failed:     {stats['failed']}")
    print(f"  Skipped:    {stats['skipped']}")
    print(f"  Output:     {XBRL_DIR}")
    print(f"  Manifest:   {MANIFEST_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
