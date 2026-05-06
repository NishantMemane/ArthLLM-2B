import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        async def handle_request(request):
            if "search" in request.url or "headless" in request.url or "api" in request.url:
                print(f"REQUEST: {request.url}")
                if request.method == "POST":
                    print(f"Payload: {request.post_data}")
                    
        async def handle_response(response):
            if "search" in response.url or "headless" in response.url or "api" in response.url:
                try:
                    text = await response.text()
                    if "{" in text:
                        print(f"RESPONSE from {response.url}:")
                        print(text[:500])
                except:
                    pass

        page.on("request", handle_request)
        page.on("response", handle_response)
        
        print("Navigating to income tax act...")
        await page.goto("https://www.incometaxindia.gov.in/income-tax-act", wait_until="networkidle")
        await asyncio.sleep(8)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
