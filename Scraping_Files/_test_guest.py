import requests
import json
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})

base = "https://www.incometaxindia.gov.in"
url = f"{base}/o/headless-delivery/v1.0/sites/guest/structured-contents?search=Circular%20No&page=1&pageSize=10"

print(f"Fetching {url}")
r = s.get(url, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Total: {data.get('totalCount')}")
    for item in data.get("items", []):
        print(f"  Title: {item.get('title')}")
else:
    print(r.text)
