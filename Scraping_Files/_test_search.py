import requests, json
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
base = "https://www.incometaxindia.gov.in"
gid = "20117"

print("=== Searching structured contents ===")
url = f"{base}/o/headless-delivery/v1.0/sites/{gid}/structured-contents?search=Circular No&page=1&pageSize=5&flatten=true"
r = s.get(url, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Total: {data.get('totalCount')}")
    for item in data.get("items", []):
        print(f"Title: {item.get('title')}")
        # Print contentUrl if available
        for f in item.get("contentFields", []):
            if "document" in f.get("name", "").lower() or "pdf" in f.get("name", "").lower():
                doc = f.get('contentFieldValue', {}).get('document', {})
                print(f"  -> Doc: {doc.get('title')} ({doc.get('contentUrl')})")

print("\n=== Trying with document folders ===")
# Another approach: find all folders with 'Circular' in name
f_url = f"{base}/o/headless-delivery/v1.0/sites/{gid}/document-folders?search=Circular&page=1&pageSize=10"
r2 = s.get(f_url, timeout=10)
print(f"Status: {r2.status_code}")
if r2.status_code == 200:
    data = r2.json()
    print(f"Folders total: {data.get('totalCount')}")
    for item in data.get("items", []):
        print(f"  Folder: {item.get('name')} (ID: {item.get('id')})")
