import requests
import json
import os
import concurrent.futures
from tqdm import tqdm
import urllib3

urllib3.disable_warnings()

out_dir = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\cbdt_metadata"
os.makedirs(out_dir, exist_ok=True)

s = requests.Session()
s.verify = False
s.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Content-Type": "application/json"
})

url = "https://www.incometaxindia.gov.in/o/search/v1.0/search?nestedFields=embedded&pageSize=100&restrictFields=embedded.actions%2Cembedded.creator&page="

def fetch_data(doc_type, structure_id, structure_key):
    print(f"Fetching total count for {doc_type}...")
    payload = {
        "attributes": {
            "search.empty.search": True,
            "search.experiences.blueprint.external.reference.code": "CIRCULAR_NOTIFICATION_BP_ERC",
            "search.experiences.structure_id": structure_id,
            "search.experiences.structure_key": structure_key
        }
    }
    
    # Get total count first
    r = s.post(url + "1", json=payload, timeout=20)
    if r.status_code != 200:
        print(f"Error getting {doc_type}: {r.status_code} - {r.text}")
        return []
    
    total = r.json().get('totalCount', 0)
    total_pages = (total // 100) + 1
    print(f"{doc_type} Total: {total} ({total_pages} pages)")
    
    all_results = []
    
    def fetch_page(page):
        try:
            r = s.post(url + str(page), json=payload, timeout=30)
            if r.status_code == 200:
                items = r.json().get('items', [])
                extracted = []
                for item in items:
                    title = item.get('title', '')
                    pdf_url = ""
                    date_val = ""
                    
                    fields = item.get("embedded", {}).get("contentFields", [])
                    for f in fields:
                        name = f.get("name", "")
                        if name == "reportFile" or name == "documentFile":
                            pdf_url = f.get("contentFieldValue", {}).get("document", {}).get("contentUrl", "")
                        elif name == "circularNotificationDate":
                            date_val = f.get("contentFieldValue", {}).get("data", "")
                    
                    if pdf_url:
                        pdf_url = "https://www.incometaxindia.gov.in" + pdf_url
                    
                    extracted.append({
                        "title": title,
                        "url": pdf_url,
                        "date": date_val
                    })
                return extracted
        except Exception as e:
            print(f"Error on page {page}: {e}")
        return []

    # Run concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_page, p) for p in range(1, total_pages + 1)]
        for future in tqdm(concurrent.futures.as_completed(futures), total=total_pages, desc=f"Fetching {doc_type}"):
            res = future.result()
            if res:
                all_results.extend(res)
                
    return all_results

circulars = fetch_data("Circulars", "36050", "CIRCULAR_KEY")
with open(os.path.join(out_dir, "cbdt_circulars_final.json"), "w", encoding="utf-8") as f:
    json.dump(circulars, f, indent=2)

notifications = fetch_data("Notifications", "36052", "NOTIFICATION_KEY")
with open(os.path.join(out_dir, "cbdt_notifications_final.json"), "w", encoding="utf-8") as f:
    json.dump(notifications, f, indent=2)

print(f"Successfully scraped {len(circulars)} Circulars and {len(notifications)} Notifications.")
