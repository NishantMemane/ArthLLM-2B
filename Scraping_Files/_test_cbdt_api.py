"""Test the Liferay Search API on incometaxindia.gov.in."""
import requests
import json
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
})

# First get the scopeGroupId from the page
r = s.get("https://www.incometaxindia.gov.in/circulars", timeout=15)
import re
gid = re.findall(r'getScopeGroupId\(\)\{return\s*"?(\d+)', r.text)
portal_url = re.findall(r'getPortalURL\(\)\{return\s*"([^"]+)"', r.text)
print(f"ScopeGroupId: {gid}")
print(f"PortalURL: {portal_url}")

# Also try to find Liferay.ThemeDisplay
theme = re.findall(r'Liferay\.ThemeDisplay\s*=\s*\{([^}]+)\}', r.text)
if theme:
    print(f"ThemeDisplay: {theme[0][:200]}")

# Try the search API
base = "https://www.incometaxindia.gov.in"
scope_id = gid[0] if gid else "20099"

# Test: Search API for circulars
print(f"\n=== Test Search API (scopeGroupId={scope_id}) ===")
search_url = f"{base}/o/search/v1.0/search?page=1&pageSize=5&restrictFields=actions%2Ccreator&nestedFields=embedded&fields=embedded.taxonomyCategoryBriefs,embedded.contentFields,itemURL,title"
r2 = s.get(search_url, timeout=10)
print(f"Status: {r2.status_code}")
if r2.status_code == 200:
    data = r2.json()
    print(f"Page: {data.get('page')}, LastPage: {data.get('lastPage')}, TotalCount: {data.get('totalCount')}")
    if data.get("items"):
        item = data["items"][0]
        print(f"First item keys: {list(item.keys())}")
        print(f"Title: {item.get('title')}")
        print(f"itemURL: {item.get('itemURL')}")
        if "embedded" in item:
            print(f"Embedded keys: {list(item['embedded'].keys()) if isinstance(item['embedded'], dict) else 'not dict'}")

# Also test the scoped search
print(f"\n=== Test Scoped Search ===")
scoped_url = f"{base}/o/search/v1.0/search/scopes/{scope_id}?page=1&pageSize=5&nestedFields=embedded&fields=embedded.taxonomyCategoryBriefs,embedded.contentFields,itemURL,title"
r3 = s.get(scoped_url, timeout=10)
print(f"Status: {r3.status_code}")
if r3.status_code == 200:
    data = r3.json()
    print(f"TotalCount: {data.get('totalCount')}")

# Test structured-contents endpoint
print(f"\n=== Test Structured Contents ===")
sc_url = f"{base}/o/headless-delivery/v1.0/sites/{scope_id}/structured-contents?page=1&pageSize=5&flatten=true"
r4 = s.get(sc_url, timeout=10)
print(f"Status: {r4.status_code}")
if r4.status_code == 200:
    data = r4.json()
    print(f"TotalCount: {data.get('totalCount')}, LastPage: {data.get('lastPage')}")
    if data.get("items"):
        item = data["items"][0]
        print(f"First item title: {item.get('title')}")
        print(f"First item keys: {list(item.keys())[:10]}")
