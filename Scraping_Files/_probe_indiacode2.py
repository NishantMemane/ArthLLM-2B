"""Probe 2: Follow redirects on indiacode and brute-force scan IDs."""
import requests
import re
import urllib3
urllib3.disable_warnings()
from concurrent.futures import ThreadPoolExecutor, as_completed

s = requests.Session()
s.verify = False
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

# Test: Follow redirects for FEMA
print("=== FOLLOW REDIRECTS ===")
url = "https://www.indiacode.nic.in/bitstream/123456789/2256/1/a1999-42.pdf"
r = s.get(url, timeout=30, allow_redirects=True)
print(f"  FEMA: final URL = {r.url[:120]}")
print(f"  Status: {r.status_code}, Content-Type: {r.headers.get('Content-Type','?')[:40]}")
print(f"  Size: {len(r.content)}, PDF: {r.content[:4] == b'%PDF'}")
if r.content[:4] != b"%PDF":
    # Check if it's a handle page with a different bitstream link
    alt_pdfs = re.findall(r'href="([^"]*bitstream[^"]*)"', r.text)
    print(f"  Alternative bitstream links: {alt_pdfs[:5]}")

# Now scan handle pages to find bitstream PDFs
print("\n=== SCAN HANDLE PAGES FOR BITSTREAM LINKS ===")
# Test a few handle IDs
for hid in [2435, 2256, 2255, 2398, 15689, 2251, 1362, 1500, 2000, 2500, 3000]:
    url = f"https://www.indiacode.nic.in/handle/123456789/{hid}"
    try:
        r = s.get(url, timeout=15)
        title_m = re.search(r'<title>(.*?)</title>', r.text, re.S)
        title = title_m.group(1).strip() if title_m else "?"
        bs_links = re.findall(r'href="([^"]*bitstream[^"]*\.pdf)"', r.text, re.I)
        print(f"  ID {hid:6d}: {title[:60]:60s} | PDFs: {len(bs_links)}")
        for bl in bs_links[:2]:
            print(f"             {bl}")
    except:
        print(f"  ID {hid:6d}: ERROR")

# Now let's brute-force a range of IDs to find all acts with PDFs
print("\n=== BRUTE FORCE SCAN: IDs 1-100 (sample) ===")
found = []

def check_id(hid):
    try:
        url = f"https://www.indiacode.nic.in/handle/123456789/{hid}"
        r = s.get(url, timeout=10)
        if r.status_code == 200 and len(r.text) > 5000:
            bs = re.findall(r'href="([^"]*bitstream[^"]*\.pdf)"', r.text, re.I)
            if bs:
                title_m = re.search(r'<title>(.*?)</title>', r.text, re.S)
                title = title_m.group(1).strip()[:80] if title_m else "?"
                return (hid, title, bs)
    except:
        pass
    return None

with ThreadPoolExecutor(max_workers=20) as ex:
    futs = {ex.submit(check_id, i): i for i in range(1, 101)}
    for f in as_completed(futs):
        result = f.result()
        if result:
            hid, title, pdfs = result
            found.append(result)
            print(f"  ID {hid:5d}: {title[:60]} ({len(pdfs)} PDFs)")

print(f"\nFound {len(found)} handles with PDFs in range 1-100")

# Now try a bigger range to estimate total
print("\n=== ESTIMATE: Sample IDs 2400-2500 ===")
found2 = []
with ThreadPoolExecutor(max_workers=20) as ex:
    futs = {ex.submit(check_id, i): i for i in range(2400, 2501)}
    for f in as_completed(futs):
        result = f.result()
        if result:
            hid, title, pdfs = result
            found2.append(result)
            print(f"  ID {hid:5d}: {title[:60]} ({len(pdfs)} PDFs)")

print(f"\nFound {len(found2)} handles with PDFs in range 2400-2500")

# Try high range
print("\n=== ESTIMATE: Sample IDs 15000-15100 ===")
found3 = []
with ThreadPoolExecutor(max_workers=20) as ex:
    futs = {ex.submit(check_id, i): i for i in range(15000, 15101)}
    for f in as_completed(futs):
        result = f.result()
        if result:
            hid, title, pdfs = result
            found3.append(result)

print(f"Found {len(found3)} handles with PDFs in range 15000-15100")
