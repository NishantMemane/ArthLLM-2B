import requests, json
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
base = "https://www.incometaxindia.gov.in"
gid = "20117"

print("=== Scanning structured-contents for Circulars ===")
# Use Liferay filter instead of search to be exact.
# Or just search and parse the JSON.
url = f"{base}/o/headless-delivery/v1.0/sites/{gid}/structured-contents?search=Circular%20No&page=1&pageSize=50&flatten=true"
r = s.get(url, timeout=10)

valid_circulars = []
if r.status_code == 200:
    data = r.json()
    items = data.get("items", [])
    print(f"Total returned by search: {data.get('totalCount')}")
    
    for item in items:
        title = item.get('title', '')
        
        # Check if title looks like a Circular or Notification
        if "Circular No" in title or "Notification No" in title:
            # Find document attached
            pdf_url = None
            for f in item.get("contentFields", []):
                doc = f.get('contentFieldValue', {}).get('document', {})
                if doc and doc.get('contentUrl'):
                    pdf_url = doc.get('contentUrl')
                    break
            
            if pdf_url:
                valid_circulars.append({"title": title, "url": pdf_url})

    print(f"Found {len(valid_circulars)} valid circulars in first 50 items:")
    for c in valid_circulars[:10]:
        print(f"  {c['title'][:80]} -> {c['url']}")
else:
    print(f"API Error {r.status_code}: {r.text}")
