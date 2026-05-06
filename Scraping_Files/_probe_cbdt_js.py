"""Find the actual API call in the JS bundle."""
import requests
import re
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": "Mozilla/5.0"})

# Get the HTML
r = s.get("https://www.incometaxindia.gov.in/circulars", timeout=15)

# Find the etds-circular-notification JS bundle URL
bundles = re.findall(r'src="([^"]*etds[^"]*\.js[^"]*)"', r.text)
print(f"ETDS JS bundles: {bundles}")

# Also find any inline script with fetch/XMLHttpRequest to /o/
inline_fetches = re.findall(r'(?:fetch|XMLHttpRequest|axios|\.get|\.post)\s*\(["\']([^"\']*)["\']', r.text[:200000])
print(f"\nInline fetch URLs: {inline_fetches[:10]}")

# Find the CSS/JS resources from the etds client extension
etds_resources = re.findall(r'(https?://[^"\']*etds[^"\']*)', r.text)
print(f"\nETDS resources: {len(etds_resources)}")
for u in list(set(etds_resources))[:10]:
    print(f"  {u[:150]}")

# Get the JS bundle content
if bundles:
    for bundle_url in bundles[:3]:
        if not bundle_url.startswith("http"):
            bundle_url = "https://www.incometaxindia.gov.in" + bundle_url
        print(f"\nFetching bundle: {bundle_url[:100]}")
        r2 = s.get(bundle_url, timeout=10)
        js = r2.text
        print(f"  Size: {len(js)} chars")
        
        # Find API endpoints in JS
        endpoints = re.findall(r'["\']([^"\']*(?:/o/|/api/|headless|search)[^"\']*)["\']', js[:100000])
        print(f"  API endpoints: {len(endpoints)}")
        for e in list(set(endpoints))[:20]:
            print(f"    {e[:120]}")
        
        # Find fetch calls
        fetches = re.findall(r'(?:fetch|\.get|\.post)\s*\(([^)]{10,200})\)', js[:100000])
        print(f"  Fetch calls: {len(fetches)}")
        for f in fetches[:10]:
            print(f"    {f[:150]}")

# Also directly check the etds-circular-notification assets endpoint with index.js
print("\n=== Check etds assets ===")
# The browser had this open: /o/etds-circular-notification/assets/index-Cwof...
# Let's find the full URL
index_urls = re.findall(r'((?:/o/etds-circular-notification/assets/[^"\']+))', r.text)
print(f"Index URLs: {index_urls[:5]}")
for idx_url in index_urls[:3]:
    full = "https://www.incometaxindia.gov.in" + idx_url
    print(f"\n  Fetching: {full[:100]}")
    r3 = s.get(full, timeout=10)
    print(f"  Status: {r3.status_code}, Size: {len(r3.text)}")
    # Search for API endpoints in the JS
    apis = re.findall(r'["\']([^"\']*(?:search|circular|notification|document|headless)[^"\']*)["\']', r3.text[:50000])
    for a in list(set(apis))[:15]:
        print(f"    {a[:120]}")
