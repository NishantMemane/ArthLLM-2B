import requests, json

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
base = "https://www.incometaxindia.gov.in"
gid = "20117"

cat_circ = "37776"
cat_notif = "37788"

for cat_id, cat_name in [(cat_circ, "Circulars"), (cat_notif, "Notifications")]:
    print(f"\n=== Testing {cat_name} (Cat ID: {cat_id}) ===")
    url = f"{base}/o/headless-delivery/v1.0/taxonomy-categories/{cat_id}/structured-contents?page=1&pageSize=2&flatten=true"
    r = s.get(url, verify=False, timeout=10)
    if r.status_code == 200:
        data = r.json()
        print(f"Total: {data.get('totalCount')}")
        for item in data.get("items", []):
            print(f"  Title: {item.get('title')}")
            # Find PDF
            for f in item.get("contentFields", []):
                if "document" in f.get("name", "").lower() or "pdf" in f.get("name", "").lower():
                    doc = f.get('contentFieldValue', {}).get('document', {})
                    print(f"    -> Doc: {doc.get('title')} ({doc.get('contentUrl')})")
