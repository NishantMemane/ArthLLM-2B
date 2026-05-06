import asyncio
from playwright.async_api import async_playwright
import json
import os

os.makedirs("cbdt_responses", exist_ok=True)

async def main():
    async with async_playwright() as p:
        # Launch headed to bypass WAF
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        res_count = 0
        endpoints = set()

        async def handle_response(response):
            nonlocal res_count
            if response.request.resource_type in ["fetch", "xhr"]:
                url = response.url
                # Only log incometaxindia API calls
                if "incometaxindia.gov.in" in url and ("/o/" in url or "api" in url):
                    endpoints.add(url)
                    try:
                        text = await response.text()
                        if "{" in text:
                            res_count += 1
                            with open(f"cbdt_responses/res_{res_count}.json", "w", encoding="utf-8") as f:
                                json.dump({
                                    "url": url,
                                    "method": response.request.method,
                                    "status": response.status,
                                    "text": text[:2000] # just save a snippet to identify
                                }, f, indent=2)
                    except Exception as e:
                        pass

        page.on("response", handle_response)
        
        print("Navigating to circulars...")
        await page.goto("https://www.incometaxindia.gov.in/circulars", wait_until="networkidle")
        await asyncio.sleep(15) # Wait for component to fetch data
        
        print(f"Captured {res_count} JSON responses.")
        print("Endpoints found:")
        for ep in endpoints:
            print(f" - {ep}")

        with open("cbdt_endpoints.txt", "w") as f:
            for ep in endpoints:
                f.write(ep + "\n")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
