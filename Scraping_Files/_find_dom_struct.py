import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("Navigating to Circulars...")
        await page.goto("https://www.incometaxindia.gov.in/circulars", wait_until="networkidle")
        
        # Wait for the table to appear by waiting for "items" or "Circular No."
        try:
            await page.wait_for_selector("text=Circular No.", timeout=30000)
            print("Found 'Circular No.' text on page!")
        except Exception as e:
            print("Could not find 'Circular No.' text via wait_for_selector.")

        # Let's try to evaluate to find exactly where it is
        js = """() => {
            function findNodesWithText(root, text) {
                let found = [];
                const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
                let node;
                while (node = walker.nextNode()) {
                    if (node.nodeValue.includes(text)) {
                        found.push(node.parentElement);
                    }
                }
                
                // Also check shadow DOMs
                const allElements = root.querySelectorAll('*');
                for (let el of allElements) {
                    if (el.shadowRoot) {
                        found.push(...findNodesWithText(el.shadowRoot, text));
                    }
                }
                return found;
            }
            
            const nodes = findNodesWithText(document.body, "Circular No.");
            return nodes.map(n => ({
                tag: n.tagName,
                class: n.className,
                html: n.outerHTML.substring(0, 500)
            }));
        }"""
        
        results = await page.evaluate(js)
        print(f"Found {len(results)} nodes containing 'Circular No.'")
        for idx, r in enumerate(results[:5]):
            print(f"\n--- Node {idx} ---")
            print(f"Tag: {r['tag']}, Class: {r['class']}")
            print(f"HTML: {r['html']}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
