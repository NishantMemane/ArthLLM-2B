import json

meta = json.load(open(r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\_scrape_remaining_meta.json"))

print("=== SAMPLE FSR URLs ===")
fsr = [t for t in meta["tasks"] if t["source"] == "RBI_FSR"]
for t in fsr[:5]:
    print("  " + t["url"][:120])

print("\n=== SAMPLE FEMA URLs ===")
fema = [t for t in meta["tasks"] if t["source"] == "FEMA"]
for t in fema[:5]:
    print("  " + t["url"][:120])

# Now test downloading one FEMA PDF with requests
import requests
import urllib3
urllib3.disable_warnings()

print("\n=== TEST DOWNLOAD: First FEMA PDF ===")
if fema:
    url = fema[0]["url"]
    print(f"  URL: {url}")
    try:
        r = requests.get(url, timeout=30, verify=False, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        print(f"  Status: {r.status_code}")
        print(f"  Content-Type: {r.headers.get('Content-Type', 'N/A')}")
        print(f"  Size: {len(r.content)} bytes")
        print(f"  First 20 bytes: {r.content[:20]}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n=== TEST DOWNLOAD: First FSR PDF ===")
if fsr:
    url = fsr[0]["url"]
    print(f"  URL: {url}")
    try:
        r = requests.get(url, timeout=30, verify=False, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        print(f"  Status: {r.status_code}")
        print(f"  Content-Type: {r.headers.get('Content-Type', 'N/A')}")
        print(f"  Size: {len(r.content)} bytes")
        print(f"  First 20 bytes: {r.content[:20]}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Check how many FSR urls hit the same 5 common PDFs on every page
from collections import Counter
fsr_filenames = [t["url"].split("/")[-1] for t in fsr]
c = Counter(fsr_filenames)
print(f"\n=== FSR PDF filename frequency (top 10) ===")
for name, count in c.most_common(10):
    print(f"  {name}: {count} times")
