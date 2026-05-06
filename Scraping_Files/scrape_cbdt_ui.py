import asyncio
from playwright.async_api import async_playwright
import json
import os
import re

out_dir = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\cbdt_playwright"
os.makedirs(out_dir, exist_ok=True)

async def scrape_list(page, base_url, out_file):
    print(f"Navigating to {base_url}...")
    await page.goto(base_url, wait_until="networkidle")
    await asyncio.sleep(5) # initial wait for components

    all_items = []
    
    for i in range(1, 5): # Just test 4 pages for now
        print(f"Scraping page {i} of {base_url}...")
        
        # We know from screenshot that items have title like "Circular No. x/xxxx"
        # We can extract all links and find those
        js = """() => {
            const items = [];
            // Target the links inside the container
            const links = document.querySelectorAll('a');
            for (let a of links) {
                const text = a.innerText.trim();
                if (text.includes('Circular No.') || text.includes('Notification No.')) {
                    items.push({
                        title: text,
                        url: a.href
                    });
                }
            }
            return items;
        }"""
        page_items = await page.evaluate(js)
        print(f"  Found {len(page_items)} items on page {i}")
        all_items.extend(page_items)
        
        # Click Next >
        try:
            # Finding the Next button
            # In Liferay it usually says "Next" inside an anchor
            next_btn = await page.query_selector("a:has-text('Next')")
            if next_btn:
                await next_btn.click()
                await asyncio.sleep(4) # wait for data load
            else:
                print("  No Next button found, stopping.")
                break
        except Exception as e:
            print(f"  Error clicking Next: {e}")
            break

    # Save
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_items, f, indent=2)
    print(f"Saved {len(all_items)} to {out_file}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # See what's happening
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        await scrape_list(page, "https://www.incometaxindia.gov.in/circulars", os.path.join(out_dir, "circulars.json"))
        await scrape_list(page, "https://www.incometaxindia.gov.in/notifications", os.path.join(out_dir, "notifications.json"))

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
