import requests
import json
import os
import concurrent.futures
from tqdm import tqdm
import urllib3

urllib3.disable_warnings()

out_dir = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\cbdt_metadata"
os.makedirs(out_dir, exist_ok=True)

state_file = os.path.join(out_dir, "cbdt_scraper_state.json")
circ_file = os.path.join(out_dir, "cbdt_circulars_metadata.json")
notif_file = os.path.join(out_dir, "cbdt_notifications_metadata.json")

# Load existing state
completed_pages = []
if os.path.exists(state_file):
    with open(state_file, "r") as f:
        completed_pages = json.load(f)

# Load existing data
circulars = []
if os.path.exists(circ_file):
    with open(circ_file, "r", encoding="utf-8") as f:
        circulars = json.load(f)

notifications = []
if os.path.exists(notif_file):
    with open(notif_file, "r", encoding="utf-8") as f:
        notifications = json.load(f)

print(f"Loaded existing state: {len(completed_pages)} pages done, {len(circulars)} circulars, {len(notifications)} notifications.")

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})

base = "https://www.incometaxindia.gov.in"
gid = "20117"
page_size = 100
total_items = 103509
total_pages = (total_items // page_size) + 1

def fetch_page(page):
    url = f"{base}/o/headless-delivery/v1.0/sites/{gid}/structured-contents?page={page}&pageSize={page_size}&flatten=true"
    try:
        r = s.get(url, timeout=15)
        if r.status_code == 200:
            return page, r.json().get('items', [])
    except Exception as e:
        pass
    return page, []

pages_to_fetch = [p for p in range(1, total_pages + 1) if p not in completed_pages]
print(f"Pages left to fetch: {len(pages_to_fetch)}")

if len(pages_to_fetch) > 0:
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(fetch_page, p): p for p in pages_to_fetch}
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(pages_to_fetch), desc="Fetching CBDT Metadata"):
            page, items = future.result()
            
            # If items returned empty, might be an error or just empty page, but we mark it complete to avoid infinite loops on bad pages.
            # In a truly robust scraper, we might retry, but let's just mark it.
            if items:
                new_circs = []
                new_notifs = []
                for item in items:
                    title = item.get('title', '')
                    if 'circular' in title.lower() or 'notification' in title.lower():
                        # Extract PDF
                        pdf_url = None
                        for f in item.get('contentFields', []):
                            if "document" in f.get('name', '').lower() or "pdf" in f.get('name', '').lower():
                                doc = f.get('contentFieldValue', {}).get('document', {})
                                if doc and doc.get('contentUrl'):
                                    pdf_url = doc.get('contentUrl')
                                    break
                        if pdf_url:
                            doc_info = {"title": title, "url": base + pdf_url, "id": item.get('id')}
                            if 'circular' in title.lower():
                                new_circs.append(doc_info)
                            else:
                                new_notifs.append(doc_info)
                
                circulars.extend(new_circs)
                notifications.extend(new_notifs)
            
            completed_pages.append(page)
            
            # Save state frequently
            if len(completed_pages) % 50 == 0 or len(completed_pages) == total_pages:
                with open(circ_file, "w", encoding="utf-8") as f:
                    json.dump(circulars, f, indent=2)
                with open(notif_file, "w", encoding="utf-8") as f:
                    json.dump(notifications, f, indent=2)
                with open(state_file, "w") as f:
                    json.dump(completed_pages, f)

# Final save
with open(circ_file, "w", encoding="utf-8") as f:
    json.dump(circulars, f, indent=2)
with open(notif_file, "w", encoding="utf-8") as f:
    json.dump(notifications, f, indent=2)
with open(state_file, "w") as f:
    json.dump(completed_pages, f)

print(f"\nDone! Total Discovered: {len(circulars)} Circulars and {len(notifications)} Notifications.")
