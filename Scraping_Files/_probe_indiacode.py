"""Probe indiacode.nic.in — find the full scope of what's available."""
import requests
import re
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

# Test 1: Do the known bitstream URLs work?
print("=== TEST 1: Known Bitstream PDFs ===")
test_urls = [
    ("https://www.indiacode.nic.in/bitstream/123456789/2435/1/a1961-43.pdf", "Income Tax Act"),
    ("https://www.indiacode.nic.in/bitstream/123456789/2256/1/a1999-42.pdf", "FEMA 1999"),
    ("https://www.indiacode.nic.in/bitstream/123456789/2255/1/a2017-12.pdf", "CGST Act 2017"),
    ("https://www.indiacode.nic.in/bitstream/123456789/2398/1/a1934-02.pdf", "RBI Act 1934"),
]
for url, name in test_urls:
    try:
        r = s.get(url, timeout=30, stream=True)
        ct = r.headers.get("Content-Type", "")
        size = int(r.headers.get("Content-Length", 0))
        first = r.raw.read(10)
        is_pdf = first[:4] == b"%PDF"
        print(f"  {name:25s} | {r.status_code} | {ct[:30]:30s} | {size:>10} bytes | PDF: {is_pdf}")
    except Exception as e:
        print(f"  {name:25s} | ERROR: {e}")

# Test 2: Can we browse the repository to find ALL acts?
print("\n=== TEST 2: Browse Repository ===")
browse_urls = [
    "https://www.indiacode.nic.in/handle/123456789/1362/browse?type=title",
    "https://www.indiacode.nic.in/handle/123456789/1362",
    "https://www.indiacode.nic.in/browse?type=title",
    "https://www.indiacode.nic.in",
]
for url in browse_urls:
    try:
        r = s.get(url, timeout=30)
        pdf_links = re.findall(r'href="([^"]*bitstream[^"]*\.pdf)"', r.text, re.I)
        handle_links = re.findall(r'href="(/handle/123456789/\d+)"', r.text)
        total_links = len(re.findall(r'href="([^"]*)"', r.text))
        print(f"  {url[:70]:70s}")
        print(f"    Status: {r.status_code}, Size: {len(r.text)}, Links: {total_links}, PDFs: {len(pdf_links)}, Handles: {len(handle_links)}")
        if handle_links:
            print(f"    Sample handles: {handle_links[:5]}")
        if pdf_links:
            print(f"    Sample PDFs: {pdf_links[:3]}")
    except Exception as e:
        print(f"  {url[:70]} -> ERROR: {e}")

# Test 3: Search API
print("\n=== TEST 3: Search/Discovery ===")
search_urls = [
    "https://www.indiacode.nic.in/simple-search?query=income+tax",
    "https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=&sort_by=dc.title&order=asc&rpp=100",
]
for url in search_urls:
    try:
        r = s.get(url, timeout=30)
        handle_links = re.findall(r'href="(/handle/123456789/\d+)"', r.text)
        print(f"  {url[:80]:80s}")
        print(f"    Status: {r.status_code}, Handles: {len(handle_links)}")
    except Exception as e:
        print(f"  ERROR: {e}")
