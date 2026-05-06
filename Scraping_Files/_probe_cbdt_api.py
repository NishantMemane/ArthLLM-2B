"""Probe incometaxindia.gov.in API endpoints directly."""
import requests
import json
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
})

# Test 1: Liferay headless delivery API
print("=== Test 1: Liferay Headless API ===")
urls = [
    "https://www.incometaxindia.gov.in/o/headless-delivery/v1.0/sites/guest/structured-contents?page=1&pageSize=10",
    "https://www.incometaxindia.gov.in/o/headless-delivery/v1.0/sites/guest/structured-contents?page=1&pageSize=10&filter=contentStructureId eq 44101",
    "https://www.incometaxindia.gov.in/api/jsonws/",
]
for url in urls:
    try:
        r = s.get(url, timeout=10)
        print(f"  {r.status_code}: {url[:90]}")
        if r.status_code == 200 and r.text.strip().startswith("{"):
            data = r.json()
            print(f"    Keys: {list(data.keys())[:5]}")
            if "items" in data:
                print(f"    Items: {len(data['items'])}, Page: {data.get('page')}, LastPage: {data.get('lastPage')}")
                if data["items"]:
                    print(f"    First item keys: {list(data['items'][0].keys())[:8]}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Test 2: The etds-circular-notification API
print("\n=== Test 2: ETDS API ===")
etds_urls = [
    "https://www.incometaxindia.gov.in/o/etds-circular-notification/assets",
    "https://www.incometaxindia.gov.in/o/etds-circular-notification/assets?page=1&pageSize=10",
    "https://www.incometaxindia.gov.in/o/etds-circular-notification/assets?type=circular&page=1&pageSize=10",
]
for url in etds_urls:
    try:
        r = s.get(url, timeout=10)
        print(f"  {r.status_code}: {url[:90]}")
        if r.status_code == 200:
            print(f"    Content: {r.text[:200]}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Test 3: Direct PDF download
print("\n=== Test 3: Direct PDF Download ===")
pdf_urls = [
    "https://www.incometaxindia.gov.in/documents/d/guest/circular-4-2026-pdf",
    "https://www.incometaxindia.gov.in/documents/d/guest/notification-58-2026-1-pdf",
]
for url in pdf_urls:
    try:
        r = s.get(url, timeout=10, stream=True)
        chunk = r.raw.read(20)
        is_pdf = chunk[:4] == b"%PDF"
        ct = r.headers.get("Content-Type", "?")
        cl = r.headers.get("Content-Length", "?")
        print(f"  {r.status_code} | PDF: {is_pdf} | Type: {ct[:30]} | Size: {cl} | {url.split('/')[-1]}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Test 4: Try scraping the circulars page HTML for the API call
print("\n=== Test 4: Scrape circulars page for API URLs ===")
r = s.get("https://www.incometaxindia.gov.in/circulars", headers={"Accept": "text/html"}, timeout=15)
print(f"  Status: {r.status_code}, Size: {len(r.text)}")
# Look for API URLs in the page source
import re
api_urls = re.findall(r'(https?://[^"\']*(?:api|headless|etds|assets|jsonws)[^"\']*)', r.text)
print(f"  API URLs found in page source: {len(api_urls)}")
for u in set(api_urls)[:10]:
    print(f"    {u[:120]}")

# Look for data attributes
data_attrs = re.findall(r'data-[a-z-]+="([^"]*(?:api|endpoint|url)[^"]*)"', r.text, re.I)
print(f"  Data attributes with URLs: {data_attrs[:5]}")

# Look for JSON config in script tags
configs = re.findall(r'Liferay\..*?({[^}]+})', r.text[:50000])
print(f"  Liferay configs found: {len(configs)}")
