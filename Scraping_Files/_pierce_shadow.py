import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("Navigating to circulars...")
        await page.goto("https://www.incometaxindia.gov.in/circulars", wait_until="networkidle")
        
        await asyncio.sleep(5)
        
        # Inject JS to find ALL links, piercing shadow DOMs
        js = """() => {
            function getAllLinks(root) {
                let links = [];
                // Get links in current root
                links.push(...Array.from(root.querySelectorAll('a')).map(a => ({href: a.href, text: a.innerText})));
                
                // Get all shadow roots
                const allElements = root.querySelectorAll('*');
                for (let el of allElements) {
                    if (el.shadowRoot) {
                        links.push(...getAllLinks(el.shadowRoot));
                    }
                }
                return links;
            }
            return getAllLinks(document);
        }"""
        
        links = await page.evaluate(js)
        pdf_links = [l for l in links if l['href'] and ('/documents/' in l['href'] and ('circular' in l['href'].lower() or 'notification' in l['href'].lower() or 'pdf' in l['href'].lower()))]
        
        print(f"Found {len(pdf_links)} PDF links!")
        for l in pdf_links[:10]:
            print(f"  {l['text'].replace(chr(0x200b), '').strip()[:80]} -> {l['href']}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
