"""
Step 2B: BSE Shareholding Pattern — PDF Downloader
===================================================
Downloads all SHP PDFs from the manifest built by shp_bse_manifest.py.
Uses 25 concurrent workers with rate limiting, retry logic, and resume.

Prereq: Run shp_bse_manifest.py first to build the manifest.

Usage:
    python shp_bse_downloader.py
"""

import os
import sys
import time
import random
import pandas as pd
import requests
from pathlib import Path
from tqdm import tqdm
import concurrent.futures
import threading

# ─── Config ───────────────────────────────────────────────────────────────────
MANIFEST_FILE = Path("ArthLLM-2B") / "section3" / "shareholding" / "shp_manifest.csv"
OUTPUT_DIR = Path("ArthLLM-2B") / "section3" / "shareholding" / "bse_pdfs"
LOGS_DIR = Path("ArthLLM-2B") / "section3" / "shareholding" / "logs"
MAX_WORKERS = 25
SAVE_INTERVAL = 200  # Save manifest every N downloads
DELAY_BASE = 3.0
DELAY_JITTER = 1.5

manifest_lock = threading.Lock()
save_lock = threading.Lock()
stats_lock = threading.Lock()
thread_local = threading.local()

stats = {"attempted": 0, "success": 0, "failed": 0, "invalid": 0, "skipped": 0}
save_counter = 0


def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
        thread_local.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.bseindia.com/",
        })
        try:
            thread_local.session.get("https://www.bseindia.com", timeout=15)
        except:
            pass
    return thread_local.session


def clean_name(name):
    return "".join(c for c in str(name) if c.isalnum() or c in " -_").strip()[:80]


def download_shp_pdf(row, total):
    global save_counter
    idx = row["index"]
    scrip = str(row.get("scrip_code", "UNKNOWN"))
    company = clean_name(row.get("company_name", ""))
    pdf_url = str(row.get("pdf_url", ""))
    alt_url = str(row.get("alt_pdf_url", ""))
    status = str(row.get("status", "pending"))
    attachment = str(row.get("attachment_name", ""))

    with stats_lock:
        stats["attempted"] += 1

    if status == "downloaded":
        with stats_lock:
            stats["skipped"] += 1
        return idx, "downloaded"

    if not pdf_url or pdf_url == "nan":
        with stats_lock:
            stats["invalid"] += 1
        return idx, "invalid"

    # Build output path
    folder = OUTPUT_DIR / f"{scrip}_{company}"
    folder.mkdir(parents=True, exist_ok=True)
    filename = attachment if attachment and attachment != "nan" else f"{scrip}_shp.pdf"
    filepath = folder / filename

    if filepath.exists() and filepath.stat().st_size > 500:
        with stats_lock:
            stats["skipped"] += 1
        return idx, "downloaded"

    time.sleep(DELAY_BASE + random.uniform(0, DELAY_JITTER))

    session = get_session()
    urls_to_try = [pdf_url]
    if alt_url and alt_url != "nan" and alt_url != pdf_url:
        urls_to_try.append(alt_url)

    for url in urls_to_try:
        for attempt in range(3):
            try:
                resp = session.get(url, timeout=60)

                if resp.status_code in [429, 503]:
                    time.sleep(120)
                    continue

                if resp.status_code == 200:
                    content = resp.content
                    stripped = content.lstrip(b"\r\n \t")

                    if not stripped.startswith(b"%PDF"):
                        # Not a valid PDF
                        break

                    with open(filepath, "wb") as f:
                        f.write(content)

                    size_kb = len(content) / 1024
                    with stats_lock:
                        stats["success"] += 1
                        sc = stats["success"]
                    tqdm.write(f"  ✓ {sc}/{total} | {scrip} | {size_kb:.0f}KB")
                    return idx, "downloaded"

            except requests.exceptions.RequestException:
                if attempt < 2:
                    time.sleep(5)
                continue

    # All URLs and retries exhausted
    with stats_lock:
        stats["failed"] += 1
    return idx, "failed"


def main():
    if not MANIFEST_FILE.exists():
        print(f"Manifest not found: {MANIFEST_FILE}")
        print("Run shp_bse_manifest.py first.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(MANIFEST_FILE, dtype=str)
    if "status" not in df.columns:
        df["status"] = "pending"

    df = df.reset_index()
    to_download = df[df["status"] != "downloaded"].to_dict("records")
    total = len(to_download)
    already = len(df) - total

    print("=" * 60)
    print("BSE Shareholding Pattern — PDF Downloader")
    print(f"Total in manifest: {len(df)}")
    print(f"Already downloaded: {already}")
    print(f"Pending: {total}")
    print(f"Workers: {MAX_WORKERS}")
    print("=" * 60)

    if total == 0:
        print("Nothing to download!")
        return

    counter = 0
    with tqdm(total=total, desc="Downloading SHP PDFs") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(download_shp_pdf, row, total): row
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

    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"  Attempted:  {stats['attempted']}")
    print(f"  Success:    {stats['success']}")
    print(f"  Failed:     {stats['failed']}")
    print(f"  Invalid:    {stats['invalid']}")
    print(f"  Skipped:    {stats['skipped']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
