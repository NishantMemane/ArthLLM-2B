import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("Navigating...")
        await page.goto("https://www.incometaxindia.gov.in/circulars", wait_until="networkidle")
        await asyncio.sleep(5)
        
        # Dump the HTML of the main custom element or the body
        html = await page.evaluate("() => document.querySelector('etds-circular-notification')?.shadowRoot?.innerHTML || document.body.innerHTML")
        
        with open("cbdt_html_dump.txt", "w", encoding="utf-8") as f:
            f.write(html)
        print("Dumped HTML.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
