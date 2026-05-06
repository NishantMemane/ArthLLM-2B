import os
import sys
import re
import json
import html
import requests
import urllib3
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Suppress insecure request warnings for self-signed certificates or old SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OUT_DIR = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\cci"
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}

session = requests.Session()
session.verify = False
session.headers.update(HEADERS)

def get_csrf_token(url):
    try:
        resp = session.get(url, timeout=20)
        m = re.search(r'name="csrf-token" content="(.*?)"', resp.text)
        if not m:
            m = re.search(r'name:"_token", value:"(.*?)"', resp.text)
        return m.group(1) if m else None
    except Exception as e:
        print(f"Failed to get token from {url}: {e}")
        return None

def download_file(pdf_url, filename):
    if not pdf_url.startswith("http"):
        pdf_url = "https://www.cci.gov.in/" + pdf_url.lstrip("/")
        
    filepath = os.path.join(OUT_DIR, filename)
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        return "skipped"
        
    try:
        resp = session.get(pdf_url, timeout=60)
        if resp.status_code == 200 and b"%PDF" in resp.content[:1024]:
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return "ok"
        return "not_pdf"
    except Exception:
        return "error"

def clean_filename(text):
    text = html.unescape(text)
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '_', text.strip())[:150]

# ============================================================
# SCRAPE ANTITRUST ORDERS
# ============================================================
def scrape_antitrust():
    print("\nScraping Antitrust Orders...")
    url = "https://www.cci.gov.in/antitrust/orders"
    token = get_csrf_token(url)
    if not token: return []
    
    api_url = "https://www.cci.gov.in/antitrust/orders/list"
    found = []
    
    # We'll fetch in batches
    batch_size = 100
    start = 0
    
    while True:
        data = {
            'draw': 1,
            'start': start,
            'length': batch_size,
            '_token': token
        }
        try:
            resp = session.post(api_url, data=data, headers={'X-CSRF-TOKEN': token}, timeout=30).json()
            items = resp.get('data', [])
            if not items: break
            
            for item in items:
                case_no = clean_filename(item.get('case_no', 'unknown'))
                desc = clean_filename(item.get('description', 'order'))
                
                # Parse file_content JSON
                try:
                    f_raw = html.unescape(item.get('file_content', '[]'))
                    f_list = json.loads(f_raw)
                    for f in f_list:
                        pdf_path = f.get('file_name')
                        if pdf_path:
                            fname = f"CCI_Antitrust_{case_no}_{desc}.pdf"
                            found.append((pdf_path, fname))
                except:
                    continue
            
            print(f"  Collected {len(found)} antitrust PDFs so far...")
            if len(items) < batch_size: break
            start += batch_size
        except Exception as e:
            print(f"  Error fetching antitrust batch at {start}: {e}")
            break
            
    return found

# ============================================================
# SCRAPE COMBINATIONS / REGULATIONS (Detail Page Pattern)
# ============================================================
def scrape_pattern(name, base_url):
    print(f"\nScraping {name}...")
    found = []
    batch_size = 100
    start = 0
    
    while True:
        api_url = f"{base_url}?draw=1&start={start}&length={batch_size}"
        try:
            resp = session.get(api_url, timeout=30).json()
            items = resp.get('data', [])
            if not items: break
            
            for item in items:
                # Combinations use combination_no/party_name, Regulations use title
                title_key = 'combination_no' if 'combination_no' in item else 'title'
                id_val = clean_filename(item.get(title_key, 'unknown'))
                
                # Find detail links in order_files or summary_files or files
                html_snippets = [item.get('summary_files', ''), item.get('order_files', ''), item.get('files', '')]
                for snippet in html_snippets:
                    if not snippet: continue
                    links = re.findall(r'href="(.*?)"', snippet)
                    for link in links:
                        # Follow detail link to find PDF in script
                        try:
                            detail_html = session.get(link, timeout=20).text
                            # Extract PDF from script: $('#iframesrc').attr('src','URL')
                            pdf_links = re.findall(r'[\'"](https?://[^\'"]+\.pdf)[\'"]', detail_html)
                            for p in pdf_links:
                                suffix = "summary" if "summary" in link else "order"
                                fname = f"CCI_{name}_{id_val}_{suffix}.pdf"
                                found.append((p, fname))
                        except:
                            continue
            
            print(f"  Collected {len(found)} {name} PDFs so far...")
            if len(items) < batch_size: break
            start += batch_size
        except Exception as e:
            print(f"  Error fetching {name} batch at {start}: {e}")
            break
            
    return found

# ============================================================
# EXECUTION
# ============================================================
all_tasks = []
all_tasks.extend(scrape_antitrust())
all_tasks.extend(scrape_pattern("Combination", "https://www.cci.gov.in/combination/orders-section31"))
all_tasks.extend(scrape_pattern("Regulation", "https://www.cci.gov.in/combination/legal-framwork/regulations"))

# Dedup
unique_tasks = {}
for url, name in all_tasks:
    unique_tasks[url] = name

print(f"\nTotal unique PDFs to download: {len(unique_tasks)}")

success = 0
skipped = 0
errors = 0

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(download_file, url, name): (url, name) for url, name in unique_tasks.items()}
    with tqdm(total=len(unique_tasks), desc="Downloading", unit="pdf") as pbar:
        for future in as_completed(futures):
            res = future.result()
            if res == "ok": success += 1
            elif res == "skipped": skipped += 1
            else: errors += 1
            pbar.update(1)
            pbar.set_postfix(ok=success, skip=skipped, err=errors)

print(f"\nFinished CCI Scraping. Success: {success}, Skipped: {skipped}, Errors: {errors}")
