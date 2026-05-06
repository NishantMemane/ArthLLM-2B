import os
import sys
import re
import time
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from tqdm import tqdm
except ImportError:
    os.system(f'"{sys.executable}" -m pip install tqdm -q')
    from tqdm import tqdm

OUT_DIR = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\sebi\enforcement_orders\downloads\pdfs"
os.makedirs(OUT_DIR, exist_ok=True)

# Note: SEBI may block requests without proper headers or delay
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def get_sebi_orders():
    print("Discovering SEBI Enforcement Orders...")
    url = "https://www.sebi.gov.in/sebiweb/ajax/home/getnewslistinfo.jsp"
    
    # Session to keep cookies if needed
    session = requests.Session()
    session.headers.update(HEADERS)
    
    items_to_download = []
    
    # We'll scan a set number of pages or until empty
    for page in tqdm(range(1, 50), desc="Scanning Pages"):
        data = {
            "nextValue": page,
            "next": "n",
            "search": "",
            "deptId": -1,
            "sid": 2,
            "ssid": 9,
            "smid": 2,
            "orgid": -1,
            "year": "",
            "month": ""
        }
        
        try:
            resp = session.post(url, data=data, timeout=30)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            links = soup.find_all('a', href=True)
            if not links:
                break
                
            for a in links:
                href = str(a.get('href', ''))
                title = a.text.strip()
                if "sebi.gov.in" in href and "orders" in href.lower():
                    # Go to detail page to get PDF link
                    try:
                        detail = session.get(href, timeout=20)
                        detail_soup = BeautifulSoup(detail.text, 'html.parser')
                        pdf_iframe = detail_soup.find('iframe', src=re.compile(r'\.pdf'))
                        
                        if pdf_iframe:
                            pdf_url = pdf_iframe['src'].split('?file=')[1] if '?file=' in pdf_iframe['src'] else pdf_iframe['src']
                            clean_title = re.sub(r'[^\w\s-]', '', title)[:100].strip().replace(' ', '_')
                            pdf_name = f"SEBI_Order_{clean_title}.pdf"
                            items_to_download.append((pdf_url, pdf_name))
                    except:
                        pass
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break
            
    return list(set(items_to_download))

def download_file(url, filename):
    filepath = os.path.join(OUT_DIR, filename)
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1024:
        return "skipped"
        
    try:
        resp = requests.get(url, headers=HEADERS, timeout=60)
        if resp.status_code == 200 and b"%PDF" in resp.content[:1024]:
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return "ok"
        return "error"
    except:
        return "error"

if __name__ == "__main__":
    tasks = get_sebi_orders()
    print(f"\nFound {len(tasks)} unique SEBI Enforcement Orders to download.")
    
    success = 0
    skipped = 0
    errors = 0
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(download_file, url, name): (url, name) for url, name in tasks}
        with tqdm(total=len(tasks), desc="Downloading Orders") as pbar:
            for future in as_completed(futures):
                res = future.result()
                if res == "ok": success += 1
                elif res == "skipped": skipped += 1
                else: errors += 1
                pbar.update(1)
                pbar.set_postfix(ok=success, skip=skipped, err=errors)
                
    print(f"\nDone! Success: {success}, Skipped: {skipped}, Errors: {errors}")
