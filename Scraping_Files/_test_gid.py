import requests, re, json
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
})

base = "https://www.incometaxindia.gov.in"
gid = "20117"

# Try all possible API patterns with the correct groupId
endpoints = [
    f"/o/headless-delivery/v1.0/sites/{gid}/structured-contents?page=1&pageSize=2&flatten=true",
    f"/o/headless-delivery/v1.0/sites/guest/structured-contents?page=1&pageSize=2&flatten=true",
    f"/o/search/v1.0/search/scopes/{gid}?page=1&pageSize=2&nestedFields=embedded",
    f"/o/search/v1.0/search?page=1&pageSize=2&nestedFields=embedded",
    # The JS showed: /o/search/v1.0/search?page=1&pageSize=50&restrictFields=actions%2Ccreator&nestedFields=embedded
    f"/o/search/v1.0/search?page=1&pageSize=2&restrictFields=actions%2Ccreator&nestedFields=embedded&fields=embedded.taxonomyCategoryBriefs,embedded.contentFields,itemURL,title",
]

for ep in endpoints:
    url = base + ep
    r = s.get(url, timeout=10)
    print(f"{r.status_code}: {ep[:100]}")
    if r.status_code == 200 and r.text.strip():
        try:
            data = r.json()
            tc = data.get("totalCount", "?")
            items = data.get("items", [])
            print(f"  totalCount={tc}, items={len(items)}")
            if items:
                print(f"  First: {json.dumps(items[0], indent=2)[:500]}")
        except:
            print(f"  Response: {r.text[:200]}")

# Also try POST to the search API (the JS bundle uses POST for scoped search)
print("\n=== POST test ===")
post_url = f"{base}/o/search/v1.0/search/scopes/{gid}"
payload = {
    "page": 1,
    "pageSize": 2,
}
r2 = s.post(post_url, json=payload, timeout=10)
print(f"POST {post_url}: {r2.status_code}")
if r2.status_code == 200:
    print(f"  {r2.text[:300]}")

# Test: Can we just get ALL document folder contents?
print("\n=== Document folders ===")
for gid2 in ["20117", "20120", "guest"]:
    url = f"{base}/o/headless-delivery/v1.0/sites/{gid2}/documents?page=1&pageSize=2&flatten=true"
    r3 = s.get(url, timeout=10)
    print(f"  {r3.status_code}: sites/{gid2}/documents")
    if r3.status_code == 200:
        data = r3.json()
        print(f"    totalCount={data.get('totalCount')}")
        if data.get('items'):
            item = data['items'][0]
            print(f"    First: title={item.get('title')}, contentUrl={item.get('contentUrl')}")
