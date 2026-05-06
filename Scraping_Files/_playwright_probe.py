import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("Navigating to circulars...")
        await page.goto("https://www.incometaxindia.gov.in/circulars", wait_until="load")
        
        # Wait for the table/list to load
        await page.wait_for_timeout(3000)

        # Get all links
        links = await page.eval_on_selector_all("a", "elements => elements.map(e => ({text: e.innerText, href: e.href}))")
        
        pdf_links = [l for l in links if l['href'] and ('/documents/d/guest' in l['href'] or 'circular' in l['href'].lower() and 'pdf' in l['href'].lower())]
        print(f"Found {len(pdf_links)} PDF links on first page:")
        for l in pdf_links[:5]:
            print(f"  {l['text'][:50]} -> {l['href']}")

        # Look for the pagination Next button
        print("\nPagination buttons:")
        buttons = await page.eval_on_selector_all("a, button, li", """elements => elements.map(e => ({
            text: e.innerText, 
            class: e.className,
            tag: e.tagName
        })).filter(e => e.text && e.text.toLowerCase().includes('next'))""")
        
        for b in buttons:
            print(f"  {b['tag']} | {b['class']} | {b['text']}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
