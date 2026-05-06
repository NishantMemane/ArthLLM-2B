import requests, json

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
base = "https://www.incometaxindia.gov.in"
gid = "20117"

# Test direct document search
for q in ["Circular", "Notification"]:
    print(f"\n=== Searching Documents for '{q}' ===")
    url = f"{base}/o/headless-delivery/v1.0/sites/{gid}/documents?search={q}&page=1&pageSize=3"
    r = s.get(url, verify=False, timeout=10)
    if r.status_code == 200:
        data = r.json()
        print(f"Total documents found: {data.get('totalCount')}")
        for item in data.get("items", []):
            print(f"  Title: {item.get('title')}")
            print(f"  URL: {item.get('contentUrl')}")
            print(f"  ExternalRef: {item.get('externalReferenceCode', 'None')}")
            
# Also test looking for the taxonomy category
print("\n=== Searching by document folders ===")
url = f"{base}/o/headless-delivery/v1.0/sites/{gid}/document-folders?search=Circular&page=1&pageSize=3"
r = s.get(url, verify=False, timeout=10)
if r.status_code == 200:
    for item in r.json().get("items", []):
        print(f"  Folder: {item.get('name')} (ID: {item.get('id')})")
