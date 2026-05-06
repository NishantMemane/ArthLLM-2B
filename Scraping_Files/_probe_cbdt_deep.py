"""Deep probe: Find the exact Liferay API that powers circulars/notifications pagination."""
import requests
import re
import json
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
})

# Get the circulars page HTML and find the JavaScript bundle that makes API calls
r = s.get("https://www.incometaxindia.gov.in/circulars", timeout=15)
html = r.text

# Find all script src URLs
scripts = re.findall(r'src="([^"]*\.js[^"]*)"', html)
print(f"Found {len(scripts)} JS files")

# Find API URLs
api_urls = re.findall(r'["\']([^"\']*(?:/o/|/api/|headless|etds)[^"\']*)["\']', html)
print(f"\nAPI URLs in HTML: {len(api_urls)}")
for u in list(set(api_urls))[:20]:
    print(f"  {u[:120]}")

# Find data-lfr or Liferay config
lfr_data = re.findall(r'data-lfr[^=]*="([^"]*)"', html)
print(f"\nLiferay data attributes: {len(lfr_data)}")
for d in lfr_data[:10]:
    print(f"  {d[:100]}")

# Find contentStructureId or similar
struct_ids = re.findall(r'(?:structureId|contentStructureId|classNameId|classPK|groupId|companyId)["\s:=]+["\']?(\d+)', html)
print(f"\nStructure/Class IDs: {list(set(struct_ids))}")

# Look for the specific app config that powers the circulars list
# Liferay fragment/widget configs are often in data-lfr-editmode-content-id
fragments = re.findall(r'<div[^>]*class="[^"]*fragment[^"]*"[^>]*>(.*?)</div>', html[:100000], re.S)
print(f"\nFragments: {len(fragments)}")

# Try the /o/ API with different patterns
print("\n=== Testing /o/ API endpoints ===")
test_apis = [
    "/o/headless-delivery/v1.0/content-structures",
    "/o/headless-delivery/v1.0/sites/20099/structured-contents",
    "/o/headless-delivery/v1.0/sites/20099/structured-contents?page=1&pageSize=5",
    "/o/etds-circular-notification/circulars",
    "/o/etds-circular-notification/circulars?page=1&pageSize=10",
    "/o/etds-circular-notification/notifications",
    "/o/etds-circular-notification/notifications?page=1&pageSize=10",
    "/o/etds-circular-notification/v1.0/circulars",
    "/o/etds-circular-notification/v1.0/circulars?page=1",
]
for path in test_apis:
    url = f"https://www.incometaxindia.gov.in{path}"
    try:
        r = s.get(url, timeout=5, headers={"Accept": "application/json"})
        content = r.text[:200] if r.text else "(empty)"
        print(f"  {r.status_code} | {path}")
        if r.status_code == 200 and content.strip():
            print(f"       {content[:150]}")
    except:
        print(f"  ERR | {path}")

# Check if there's a search-results widget with specific config
# Look for the widget-export JSON
widget_configs = re.findall(r'"classNameId":\s*"?(\d+)', html)
print(f"\nclassNameId values: {widget_configs[:5]}")

# Search for assetListEntryId
asset_list = re.findall(r'"assetListEntryId":\s*"?(\d+)', html)
print(f"assetListEntryId values: {asset_list[:5]}")

# Look for Liferay.Search or search-results fragment config
search_config = re.findall(r'search-results[^{]*(\{[^}]{50,500})', html)
print(f"\nSearch results configs: {len(search_config)}")
for sc in search_config[:3]:
    print(f"  {sc[:200]}")
