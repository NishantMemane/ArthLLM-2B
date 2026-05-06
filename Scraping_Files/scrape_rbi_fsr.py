#!/usr/bin/env python3
"""
RBI Financial Stability Reports (FSR) Scraper v2
==================================================
Phase 1: Playwright discovers ALL PDF links across all years (with progress bar)
Phase 2: Downloads everything with 20 concurrent workers + tqdm

Run: venv\\Scripts\\python.exe scrape_rbi_fsr.py
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    print("Run: pip install tqdm")
    sys.exit(1)

# ── Config ─────────────────────────────────────────────────────────
OUT_DIR = Path(r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\rbi\financial_stability_reports")
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://rbi.org.in"
FSR_URL  = f"{BASE_URL}/Scripts/FsReports.aspx"
WORKERS  = 20

def safe_fn(name, max_len=120):
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', '_', name).strip('_')
    return name[:max_len]

# ═══════════════════════════════════════════════════════════════════
#  PHASE 1: DISCOVERY — Playwright finds all PDF links
# ═══════════════════════════════════════════════════════════════════
async def discover_all_pdfs(page):
    """Navigate through every year on FsReports.aspx and collect PDF URLs."""
    all_tasks = []  # list of {year, report_title, pdf_url, filename}

    # Go to the main FSR page
    await page.goto(FSR_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)

    # Get all clickable year links from the sidebar
    # Years 2017-2026 are directly visible, Archives 2010-2016 appear after clicking "Archives"
    years_to_scrape = list(range(2026, 2009, -1))  # 2026 down to 2010

    pbar = tqdm(years_to_scrape, desc="Phase 1: Discovering", unit="yr")
    for year in pbar:
        year_str = str(year)
        pbar.set_postfix(year=year_str, found=len(all_tasks))

        try:
            # Go back to FSR main page each time
            await page.goto(FSR_URL, wait_until="domcontentloaded")
            await page.wait_for_timeout(1000)

            # Find and click the year link
            # Archive years (<=2016) may be hidden — use JS click as fallback
            clicked = False
            links = await page.query_selector_all("a")
            for link in links:
                try:
                    text = (await link.inner_text()).strip()
                except Exception:
                    continue
                if text == year_str:
                    try:
                        # force=True bypasses visibility/stability checks
                        await link.click(force=True, timeout=5000)
                        clicked = True
                    except Exception:
                        # JS click fallback for truly hidden elements
                        try:
                            await link.evaluate("el => el.click()")
                            clicked = True
                        except Exception:
                            pass
                    break

            if not clicked:
                # Last resort: try direct URL with year parameter
                try:
                    await page.evaluate(f"""
                        var links = document.querySelectorAll('a');
                        for (var i = 0; i < links.length; i++) {{
                            if (links[i].textContent.trim() === '{year_str}') {{
                                links[i].click();
                                break;
                            }}
                        }}
                    """)
                    clicked = True
                except Exception:
                    continue

            await page.wait_for_timeout(1500)

            # Collect report links on this page (press releases or publication reports)
            report_links = []
            page_links = await page.query_selector_all("a[href]")
            for link in page_links:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()
                if not text:
                    continue
                if "BS_PressReleaseDisplay" in href or "PublicationReportDetails" in href:
                    full_url = href if href.startswith("http") else f"{BASE_URL}/Scripts/{href}"
                    report_links.append({"url": full_url, "title": text})

            if not report_links:
                continue

            # For each report, navigate and find PDF links
            for rpt in report_links:
                try:
                    await page.goto(rpt["url"], wait_until="domcontentloaded")
                    await page.wait_for_timeout(1000)

                    # If it's a press release page, follow to PublicationReportDetails
                    if "BS_PressReleaseDisplay" in rpt["url"]:
                        pub_links = await page.query_selector_all("a[href*='PublicationReportDetails']")
                        if pub_links:
                            pub_href = await pub_links[0].get_attribute("href")
                            pub_url = pub_href if pub_href.startswith("http") else f"{BASE_URL}/Scripts/{pub_href}"
                            await page.goto(pub_url, wait_until="domcontentloaded")
                            await page.wait_for_timeout(1000)

                    # Collect ALL PDF links on this page
                    a_tags = await page.query_selector_all("a[href]")
                    for a in a_tags:
                        href = await a.get_attribute("href") or ""
                        if not href.lower().endswith(".pdf"):
                            continue
                        # Resolve the full URL
                        if href.startswith("http"):
                            pdf_url = href
                        elif href.startswith("/"):
                            pdf_url = f"https://rbidocs.rbi.org.in{href}"
                        else:
                            pdf_url = f"https://rbidocs.rbi.org.in/rdocs/PublicationReport/Pdfs/{href}"

                        filename = safe_fn(f"{year_str}_{pdf_url.split('/')[-1]}")
                        if not filename.lower().endswith(".pdf"):
                            filename += ".pdf"

                        all_tasks.append({
                            "year": year_str,
                            "report": rpt["title"],
                            "url": pdf_url,
                            "filename": filename,
                        })

                except Exception:
                    pass

            pbar.set_postfix(year=year_str, found=len(all_tasks))

        except Exception:
            pbar.set_postfix(year=year_str, found=len(all_tasks), status="skip")
            continue

    pbar.close()
    return all_tasks


# ═══════════════════════════════════════════════════════════════════
#  PHASE 2: DOWNLOAD — 20 concurrent async workers + tqdm
# ═══════════════════════════════════════════════════════════════════
async def download_pdf(ctx, task, pbar, stats):
    """Download a single PDF using Playwright's API context (bypasses WAF)."""
    year_dir = OUT_DIR / task["year"]
    year_dir.mkdir(exist_ok=True)
    dest = year_dir / task["filename"]

    # Skip if already exists and valid
    if dest.exists() and dest.stat().st_size > 5000:
        stats["skip"] += 1
        pbar.update(1)
        pbar.set_postfix(ok=stats["ok"], skip=stats["skip"], err=stats["err"])
        return

    try:
        resp = await ctx.get(task["url"])
        body = await resp.body()

        if len(body) < 1000 or body[:4] != b"%PDF":
            stats["err"] += 1
            pbar.update(1)
            pbar.set_postfix(ok=stats["ok"], skip=stats["skip"], err=stats["err"])
            return

        with open(dest, "wb") as f:
            f.write(body)

        stats["ok"] += 1

    except Exception:
        stats["err"] += 1

    pbar.update(1)
    pbar.set_postfix(ok=stats["ok"], skip=stats["skip"], err=stats["err"])


async def download_all(ctx, tasks):
    """Download all PDFs with WORKERS concurrent async tasks."""
    stats = {"ok": 0, "skip": 0, "err": 0}
    sem = asyncio.Semaphore(WORKERS)
    pbar = tqdm(total=len(tasks), desc="Phase 2: Downloading", unit="pdf")

    async def bounded(task):
        async with sem:
            await download_pdf(ctx, task, pbar, stats)

    await asyncio.gather(*(bounded(t) for t in tasks))
    pbar.close()
    return stats


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════
async def main():
    print("=" * 66)
    print("  RBI Financial Stability Reports Scraper v2")
    print("  Phase 1: Discover   |   Phase 2: 20-worker Download + tqdm")
    print("=" * 66)
    print(f"  Output: {OUT_DIR}\n")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        )
        ctx.set_default_timeout(30000)
        page = await ctx.new_page()

        # ── Phase 1 ───────────────────────────────────────────────
        tasks = await discover_all_pdfs(page)

        # Deduplicate by URL
        seen = set()
        unique = []
        for t in tasks:
            if t["url"] not in seen:
                seen.add(t["url"])
                unique.append(t)
        tasks = unique

        print(f"\n  Discovered {len(tasks)} unique PDFs across all years.\n")

        if not tasks:
            print("  Nothing to download!")
            await browser.close()
            return

        # Save discovery cache
        cache = OUT_DIR / "_discovery_cache.json"
        with open(cache, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)

        # ── Phase 2 ───────────────────────────────────────────────
        api = ctx.request  # Playwright's APIRequestContext (shares browser cookies/TLS)
        stats = await download_all(api, tasks)

        await browser.close()

    # ── Summary ────────────────────────────────────────────────────
    print()
    print("=" * 66)
    print(f"  DONE")
    print(f"  Downloaded: {stats['ok']}")
    print(f"  Skipped:    {stats['skip']}")
    print(f"  Failed:     {stats['err']}")
    print("=" * 66)

    # Count total PDFs per year folder
    print("\n  Files per year:")
    for d in sorted(OUT_DIR.iterdir()):
        if d.is_dir() and d.name.isdigit():
            count = len(list(d.glob("*.pdf")))
            print(f"    {d.name} -> {count} PDFs")


if __name__ == "__main__":
    asyncio.run(main())
