#!/usr/bin/env python3
"""
IndiaCode 5-Act Direct Downloader
=================================
This script downloads the 5 target Acts directly from IndiaCode using requests.
It uses the correct, verified bitstream URLs for each Act.

NOTE on 403 Errors:
IndiaCode is protected by Akamai WAF. If you receive "403 Forbidden" errors,
it means Akamai has temporarily blocked your IP address due to too many rapid requests.
If this happens, you can wait an hour, change your IP (VPN/Mobile hotspot),
or download these 5 specific links manually in your browser.
"""

import os
import requests
import urllib3
from pathlib import Path
from tqdm import tqdm

urllib3.disable_warnings()

# Verified Correct IndiaCode Bitstream Links
DIRECT_PDFS = [
    # Income Tax Act, 1961 (Handle 2435)
    ("https://www.indiacode.nic.in/bitstream/123456789/2435/1/a1961-43.pdf", "Income_Tax_Act_1961"),
    
    # Reserve Bank of India Act, 1934 (Handle 2398)
    ("https://www.indiacode.nic.in/bitstream/123456789/2398/1/a1934-2.pdf", "RBI_Act_1934"),
    
    # Central Goods and Services Tax Act, 2017 (Handle 15689)
    ("https://www.indiacode.nic.in/bitstream/123456789/15689/5/a2017-12.pdf", "CGST_Act_2017"),
    
    # Integrated Goods and Services Tax Act, 2017 (Handle 2251)
    ("https://www.indiacode.nic.in/bitstream/123456789/2251/1/A201713.pdf", "IGST_Act_2017"),
    
    # Foreign Exchange Management Act, 1999 (FEMA)
    # Note: If this specific URL is outdated, FEMA can also be found at indiacode.nic.in search
    ("https://www.indiacode.nic.in/bitstream/123456789/17290/1/A1999-42.pdf", "FEMA_1999"),
]

OUT_DIR = Path(r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\indiacode_acts")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def download_act(url, name):
    dest = OUT_DIR / f"{name}.pdf"
    
    # Skip if already downloaded and valid size
    if dest.exists() and dest.stat().st_size > 5000:
        print(f"[{name}] Already exists, skipping.")
        return True

    print(f"\nDownloading {name}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }

    try:
        r = requests.get(url, headers=headers, verify=False, stream=True, timeout=30)
        
        if r.status_code == 403:
            print(f"[FAIL] [403 Forbidden] Akamai WAF blocked the request for {name}.")
            print(f"   Link: {url}")
            return False
            
        if r.status_code != 200:
            print(f"[FAIL] [Error {r.status_code}] Failed to download {name}")
            return False

        # Verify it's actually a PDF and not an HTML error page
        chunk = r.raw.read(10)
        if chunk[:4] != b"%PDF":
            print(f"[FAIL] [Error] URL did not return a valid PDF (returned HTML instead).")
            print(f"   Link: {url}")
            return False
            
        total_size = int(r.headers.get('content-length', 0))
        
        with open(dest, "wb") as f, tqdm(
            desc=name,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            f.write(chunk)
            bar.update(len(chunk))
            for data in r.iter_content(chunk_size=1024):
                size = f.write(data)
                bar.update(size)
                
        print(f"[OK] Successfully downloaded {name}.pdf")
        return True
        
    except Exception as e:
        print(f"[FAIL] Exception occurred for {name}: {e}")
        return False

def main():
    print("======================================================")
    print("   IndiaCode Direct Scraper (5 Target Acts)")
    print("======================================================")
    print(f"Output Directory: {OUT_DIR}\n")
    
    success_count = 0
    for url, name in DIRECT_PDFS:
        if download_act(url, name):
            success_count += 1
            
    print("\n======================================================")
    print(f"   COMPLETED: {success_count}/{len(DIRECT_PDFS)} successfully downloaded.")
    print("======================================================")
    
    if success_count < len(DIRECT_PDFS):
        print("\n[WARN] Note: If you encountered 403 Forbidden errors, IndiaCode's Akamai")
        print("   firewall has temporarily rate-limited your IP address.")
        print("   To fix this: Switch to a mobile hotspot or VPN, then run this again.")
        print("   Alternatively, click the links above and download them manually.")

if __name__ == "__main__":
    main()
