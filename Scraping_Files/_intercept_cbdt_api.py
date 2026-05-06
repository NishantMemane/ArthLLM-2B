import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        api_info = {}

        # Listen for all responses
        async def handle_response(response):
            if "search" in response.url or "headless" in response.url or "circular" in response.url:
                try:
                    if response.request.resource_type in ["fetch", "xhr"] and response.status == 200:
                        content_type = response.headers.get("content-type", "")
                        if "application/json" in content_type:
                            text = await response.text()
                            if "totalCount" in text or "items" in text:
                                print(f"\n[FOUND API] {response.url}")
                                print(f"Method: {response.request.method}")
                                print(f"Headers: {response.request.headers}")
                                if response.request.post_data:
                                    print(f"Post Data: {response.request.post_data}")
                                print(f"Response snippet: {text[:200]}")
                                
                                api_info['url'] = response.url
                                api_info['method'] = response.request.method
                                api_info['headers'] = response.request.headers
                                api_info['post_data'] = response.request.post_data
                except Exception as e:
                    pass

        page.on("response", handle_response)
        
        print("Navigating to circulars...")
        await page.goto("https://www.incometaxindia.gov.in/circulars", wait_until="networkidle")
        
        # Wait a bit
        await asyncio.sleep(5)
        
        # Try to click next
        try:
            print("Clicking Next...")
            await page.click("text=Next")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Could not click Next: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
