#!/usr/bin/env python3
"""
IndiaCode 5-Act Scraper (Bypasses 403 WAF)
==========================================
The indiacode.nic.in server uses a strict Web Application Firewall (WAF)
that returns HTTP 403 Access Denied for the DSpace REST API and for
bare `requests` or `wget` downloads.

This script uses Playwright to perfectly simulate a real browser,
fetching the exact 5 Acts requested from IndiaCode.
"""

import asyncio
import os
import re
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    os.system("pip install playwright")
    os.system("playwright install chromium")
    from playwright.async_api import async_playwright

OUT_DIR = Path(r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\indiacode_acts")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Known Handle IDs for 4 out of the 5 Acts
ACTS = [
    {"name": "Income_Tax_Act_1961", "handle": "2435"},
    {"name": "RBI_Act_1934", "handle": "2398"},
    {"name": "CGST_Act_2017", "handle": "15689"},
    {"name": "IGST_Act_2017", "handle": "2251"},
]

async def main():
    print("=" * 60)
    print("  IndiaCode 5-Act Downloader (Playwright WAF Bypass)")
    print("=" * 60)
    
    async with async_playwright() as pw:
        # Use a real user agent
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            accept_downloads=True
        )
        page = await ctx.new_page()

        # 1. Download the 4 known acts
        for act in ACTS:
            print(f"\
Fetching {act['name']}...")
            url = f"https://www.indiacode.nic.in/handle/123456789/{act['handle']}"
            try:
                await page.goto(url, wait_until="networkidle")
                
                # Find the bitstream PDF link
                pdf_elem = await page.query_selector("a[href*='bitstream'][href$='.pdf']")
                if pdf_elem:
                    pdf_url = await pdf_elem.get_attribute("href")
                    if not pdf_url.startswith("http"):
                        pdf_url = "https://www.indiacode.nic.in" + pdf_url
                    
                    print(f"  Found PDF: {pdf_url.split('/')[-1]}")
                    
                    # Wait for download
                    async with page.expect_download() as download_info:
                        await pdf_elem.click()
                    download = await download_info.value
                    
                    dest = OUT_DIR / f"{act['name']}.pdf"
                    await download.save_as(dest)
                    print(f"  [OK] Saved: {dest.name} ({dest.stat().st_size // 1024} KB)")
                else:
                    print(f"  [FAIL] No PDF found on handle page.")
            except Exception as e:
                print(f"  [FAIL] Error: {e}")

        # 2. Search and Download FEMA dynamically
        print(f"\
Fetching FEMA_1999...")
        try:
            await page.goto("https://www.indiacode.nic.in/simple-search?query=Foreign+Exchange+Management+Act", wait_until="networkidle")
            
            # Find the first valid act link
            handles = await page.query_selector_all("a[href*='/handle/123456789/']")
            fema_href = None
            for h in handles:
                text = await h.inner_text()
                if "Foreign Exchange Management Act" in text:
                    fema_href = await h.get_attribute("href")
                    break
            
            if fema_href:
                fema_url = "https://www.indiacode.nic.in" + fema_href
                await page.goto(fema_url, wait_until="networkidle")
                
                pdf_elem = await page.query_selector("a[href*='bitstream'][href$='.pdf']")
                if pdf_elem:
                    async with page.expect_download() as download_info:
                        await pdf_elem.click()
                    download = await download_info.value
                    
                    dest = OUT_DIR / "FEMA_1999.pdf"
                    await download.save_as(dest)
                    print(f"  [OK] Saved: {dest.name} ({dest.stat().st_size // 1024} KB)")
                else:
                    print(f"  [FAIL] No PDF found on FEMA handle page.")
            else:
                print(f"  [FAIL] Could not find FEMA handle in search.")
        except Exception as e:
            print(f"  [FAIL] Error: {e}")

        await browser.close()
        
    print(f"\
Done! Check folder: {OUT_DIR}")

if __name__ == "__main__":
    asyncio.run(main())
