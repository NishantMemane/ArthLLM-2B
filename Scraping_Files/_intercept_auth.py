import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        api_url = None
        api_headers = {}
        api_post_data = None

        # Listen for all responses
        async def handle_request(request):
            nonlocal api_url, api_headers, api_post_data
            if "search" in request.url and request.method == "POST":
                print(f"[FOUND POST SEARCH] {request.url}")
                api_url = request.url
                api_headers = request.headers
                api_post_data = request.post_data
                
                with open("cbdt_auth.json", "w") as f:
                    json.dump({
                        "url": api_url,
                        "headers": api_headers,
                        "post_data": api_post_data
                    }, f, indent=2)

        page.on("request", handle_request)
        
        print("Navigating to circulars...")
        await page.goto("https://www.incometaxindia.gov.in/circulars", wait_until="networkidle")
        await asyncio.sleep(10)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
