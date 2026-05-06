import os
import sys
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from tqdm import tqdm
except ImportError:
    os.system(f'"{sys.executable}" -m pip install tqdm -q')
    from tqdm import tqdm

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OUT_DIR = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\other_regulators\cbdt\downloads\pdfs"
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

def get_cbdt_links():
    print("Discovering CBDT Documents...")
    
    # Sections to scrape
    sections = [
        "https://incometaxindia.gov.in/Pages/communications/circulars.aspx",
        "https://incometaxindia.gov.in/Pages/communications/notifications.aspx",
        "https://incometaxindia.gov.in/Pages/communications/instructions.aspx"
    ]
    
    session = requests.Session()
    session.headers.update(HEADERS)
    session.verify = False
    
    pdf_tasks = []
    
    for url in sections:
        print(f"Scanning {url}...")
        try:
            resp = session.get(url, timeout=30)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
            
            for a in links:
                href = str(a.get('href', ''))
                pdf_url = urljoin(url, href)
                title = a.text.strip()
                if not title:
                    title = pdf_url.split('/')[-1]
                    
                clean_title = re.sub(r'[^\w\s-]', '', title)[:100].strip().replace(' ', '_')
                
                category = url.split('/')[-1].replace('.aspx', '')
                fname = f"CBDT_{category}_{clean_title}.pdf"
                
                pdf_tasks.append((pdf_url, fname))
                
        except Exception as e:
            print(f"Error on {url}: {e}")
            
    return list(set(pdf_tasks))

def download_file(url, filename):
    filepath = os.path.join(OUT_DIR, filename)
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1024:
        return "skipped"
        
    try:
        resp = requests.get(url, headers=HEADERS, timeout=60, verify=False)
        if resp.status_code == 200 and b"%PDF" in resp.content[:1024]:
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return "ok"
        return "error"
    except:
        return "error"

if __name__ == "__main__":
    tasks = get_cbdt_links()
    print(f"\nFound {len(tasks)} unique CBDT PDFs to download.")
    
    success = 0
    skipped = 0
    errors = 0
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(download_file, url, name): (url, name) for url, name in tasks}
        with tqdm(total=len(tasks), desc="Downloading CBDT") as pbar:
            for future in as_completed(futures):
                res = future.result()
                if res == "ok": success += 1
                elif res == "skipped": skipped += 1
                else: errors += 1
                pbar.update(1)
                pbar.set_postfix(ok=success, skip=skipped, err=errors)
                
    print(f"\nDone! Success: {success}, Skipped: {skipped}, Errors: {errors}")
