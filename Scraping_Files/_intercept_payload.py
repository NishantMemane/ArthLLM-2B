import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        async def handle_request(request):
            if "search/v1.0/search" in request.url and request.method == "POST":
                print(f"FOUND SEARCH POST!")
                print(f"URL: {request.url}")
                print(f"Payload: {request.post_data}")
                with open("cbdt_search_payload.json", "w", encoding="utf-8") as f:
                    try:
                        f.write(json.dumps(json.loads(request.post_data), indent=2))
                    except:
                        f.write(str(request.post_data))

        page.on("request", handle_request)
        
        print("Navigating...")
        await page.goto("https://www.incometaxindia.gov.in/circulars", wait_until="networkidle")
        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
