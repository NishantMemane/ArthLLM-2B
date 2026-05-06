"""Extract the exact API endpoint from the etds-circular-notification JS bundle."""
import requests
import re
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False

# Get the main JS bundle
r = s.get("https://www.incometaxindia.gov.in/o/etds-circular-notification/assets/index-CwofedYr.js?t=1777566977227", timeout=15)
js = r.text

# Find all fetch/axios/get calls with URLs
print("=== All fetch/get calls ===")
# Pattern: fetch( or .get( or .post( followed by URL
fetches = re.findall(r'(?:fetch|\.get|\.post)\s*\(\s*[`"\']((?:https?://|/)[^`"\']+)[`"\']', js)
print(f"Found {len(fetches)} fetch calls")
for f in fetches:
    print(f"  {f[:150]}")

# Find template literal fetch calls
template_fetches = re.findall(r'(?:fetch|\.get|\.post)\s*\(\s*`([^`]+)`', js)
print(f"\nTemplate literal fetches: {len(template_fetches)}")
for f in template_fetches:
    print(f"  {f[:200]}")

# Look for /o/ paths
o_paths = re.findall(r'[`"\'](/o/[^`"\']+)[`"\']', js)
print(f"\n/o/ paths: {len(o_paths)}")
for p in list(set(o_paths)):
    print(f"  {p[:150]}")

# Look for headless-delivery
headless = re.findall(r'[`"\'](.*headless.*)[`"\']', js)
print(f"\nHeadless refs: {len(headless)}")
for h in headless[:10]:
    print(f"  {h[:150]}")

# Look for search or portal-search
search_refs = re.findall(r'[`"\'](.*(?:portal-search|search-results|search\?|keywords)[^`"\']*)[`"\']', js)
print(f"\nSearch refs: {len(search_refs)}")
for s_ref in search_refs[:10]:
    print(f"  {s_ref[:150]}")

# Look for groupId, siteId, etc.
ids = re.findall(r'(?:groupId|siteId|companyId|structureKey)\s*[:=]\s*[`"\']?(\w+)', js)
print(f"\nIDs: {list(set(ids))[:10]}")

# Find the actual API base URL
base_urls = re.findall(r'(?:baseURL|apiURL|serverURL|API_URL|endpoint)\s*[:=]\s*[`"\'](.*?)[`"\']', js)
print(f"\nBase URLs: {base_urls[:5]}")

# Find structureKey references
struct_keys = re.findall(r'structureKey\s*[:=]\s*[`"\'](.*?)[`"\']', js)
print(f"\nStructure keys: {struct_keys[:5]}")

# Try to find the data loading function
# Look for pageSize, page, or pagination patterns
pagination = re.findall(r'[\w.]*(?:page|pageSize|pagination|offset|limit)\s*[:=][^;]{5,100}', js[:100000])
print(f"\nPagination patterns: {len(pagination)}")
for p in pagination[:10]:
    print(f"  {p[:150]}")
