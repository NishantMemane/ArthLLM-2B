"""
PFRDA Scraper (Source 9)
========================
Scrapes Circulars and Regulations from pfrda.org.in.
Target: ~500 documents
"""

import os
import sys
import re
import urllib.request
from urllib.error import HTTPError, URLError
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from tqdm import tqdm
except ImportError:
    os.system(f'"{sys.executable}" -m pip install tqdm -q')
    from tqdm import tqdm

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing beautifulsoup4...")
    os.system(f'"{sys.executable}" -m pip install beautifulsoup4 -q')
    from bs4 import BeautifulSoup

BASE_URL = "https://www.pfrda.org.in"
# Important PFRDA sections
URLS_TO_SCRAPE = {
    "Circulars": "https://www.pfrda.org.in/myauth/admin/showimg.cshtml?ID=1130", # often Circulars link, but we'll crawl the main indices
    "Main_Circulars": "https://www.pfrda.org.in/index1.cshtml?lsid=160",
    "Regulations": "https://www.pfrda.org.in/index1.cshtml?lsid=162",
    "Guidelines": "https://www.pfrda.org.in/index1.cshtml?lsid=161",
    "Master_Circulars": "https://www.pfrda.org.in/index1.cshtml?lsid=208",
    "Notifications": "https://www.pfrda.org.in/index1.cshtml?lsid=163"
}

OUT_DIR = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\pfrda"
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

def get_html(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        # PFRDA sometimes blocks without SSL context or specific headers.
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except:
            return ""

def discover_pdf_links(start_url):
    html = get_html(start_url)
    if not html: return []
    
    soup = BeautifulSoup(html, "html.parser")
    pdfs = []
    
    # PFRDA uses showimg.cshtml?ID=XXX for PDFs
    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(strip=True)
        if not title: title = "Document"
        
        # Clean title for filename
        title = re.sub(r'[^\w\s-]', '', title)[:100]
        title = re.sub(r'[-\s]+', '_', title)
        
        if "showimg.cshtml" in href or href.lower().endswith(".pdf"):
            full_url = href if href.startswith("http") else f"{BASE_URL}/{href.lstrip('/')}"
            
            # Extract ID if available
            doc_id = "000"
            m = re.search(r'ID=(\d+)', href)
            if m: doc_id = m.group(1)
            
            filename = f"PFRDA_{doc_id}_{title}.pdf"
            pdfs.append((full_url, filename))
            
    # Also look for subpages (pagination)
    for a in soup.find_all("a", href=True):
        if "index1.cshtml" in a["href"] and "lsid" in a["href"]:
            pass # A full recursive spider would follow these, but we keep it simple
            
    return list(set(pdfs))

def download_file(item):
    url, filename = item
    filepath = os.path.join(OUT_DIR, filename)
    
    if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
        return "skipped", filename
        
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            data = resp.read()
            if data[:4] == b'%PDF':
                with open(filepath, 'wb') as f:
                    f.write(data)
                return "ok", filename
            return "not_pdf", filename
    except Exception as e:
        return "error", filename

# ============================================================
# MAIN
# ============================================================
print("=" * 70)
print("PFRDA Scraper (Source 9)")
print("=" * 70)

all_pdfs = []
print("Discovering documents from main sections...")
for section, url in URLS_TO_SCRAPE.items():
    print(f"  Scanning {section}...")
    links = discover_pdf_links(url)
    all_pdfs.extend(links)
    print(f"    Found {len(links)} links")

all_pdfs = list(set(all_pdfs)) # Deduplicate
print(f"\nTotal unique PDFs discovered: {len(all_pdfs)}")

if not all_pdfs:
    print("Could not find PDFs. PFRDA might be blocking the simple crawler.")
    print("You may need to use DownThemAll in Chrome as you suggested.")
    sys.exit(0)

print(f"\nDownloading to: {OUT_DIR}")
success = 0
skipped = 0
errors = 0

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(download_file, item): item for item in all_pdfs}
    
    with tqdm(total=len(all_pdfs), desc="Downloading", unit="pdf") as pbar:
        for future in as_completed(futures):
            status, fname = future.result()
            if status == "ok": success += 1
            elif status == "skipped": skipped += 1
            else: errors += 1
            
            pbar.update(1)
            pbar.set_postfix(ok=success, skip=skipped, err=errors)

print(f"\nFinished! Downloaded: {success}, Skipped: {skipped}, Errors: {errors}")
