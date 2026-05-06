import asyncio
from playwright.async_api import async_playwright
import json
import os

os.makedirs("cbdt_responses", exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        res_count = 0

        async def handle_response(response):
            nonlocal res_count
            if response.request.resource_type in ["fetch", "xhr"]:
                try:
                    text = await response.text()
                    if "{" in text:
                        res_count += 1
                        with open(f"cbdt_responses/res_{res_count}.json", "w", encoding="utf-8") as f:
                            json.dump({
                                "url": response.url,
                                "method": response.request.method,
                                "status": response.status,
                                "text": text
                            }, f, indent=2)
                except Exception as e:
                    pass

        page.on("response", handle_response)
        
        print("Navigating to circulars...")
        await page.goto("https://www.incometaxindia.gov.in/circulars", wait_until="networkidle")
        await asyncio.sleep(10)
        await browser.close()
        print(f"Captured {res_count} JSON responses.")

if __name__ == "__main__":
    asyncio.run(main())
