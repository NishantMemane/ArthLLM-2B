import os
import sys
import re
import urllib.request
import ssl
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from tqdm import tqdm
except ImportError:
    os.system(f'"{sys.executable}" -m pip install tqdm -q')
    from tqdm import tqdm

try:
    from bs4 import BeautifulSoup
except ImportError:
    os.system(f'"{sys.executable}" -m pip install beautifulsoup4 -q')
    from bs4 import BeautifulSoup

BASE_URL = "https://irdai.gov.in"

SECTIONS = {
    "circulars": "https://irdai.gov.in/circulars",
    "regulations": "https://irdai.gov.in/regulations",
    "consolidated_regulations": "https://irdai.gov.in/consolidated-gazette-notified-regulations",
    "annual_reports": "https://irdai.gov.in/annual-reports"
}

OUT_DIR = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\irdai"
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_html(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return ""

def download_file(item):
    pdf_url, filename = item
    if not pdf_url.startswith("http"):
        pdf_url = BASE_URL.rstrip('/') + '/' + pdf_url.lstrip('/')
        
    filepath = os.path.join(OUT_DIR, filename)
    
    # IRDAI annual reports can be 50-100MB, normal PDFs are < 10MB
    if os.path.exists(filepath) and os.path.getsize(filepath) > 10000:
        return "skipped", filename
        
    try:
        req = urllib.request.Request(pdf_url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
            data = resp.read()
            if data[:4] == b'%PDF':
                with open(filepath, 'wb') as f:
                    f.write(data)
                return "ok", filename
            return "not_pdf", filename
    except Exception as e:
        return "error", filename

def clean_filename(title):
    title = urllib.parse.unquote(title) # Decode %20, etc.
    title = re.sub(r'[^\w\s-]', '', title)[:150] # Keep longer titles for annual reports
    return re.sub(r'[-\s]+', '_', title.strip())

# ============================================================
# MAIN
# ============================================================
print("=" * 70)
print("IRDAI Scraper (Source 8)")
print("=" * 70)

all_pdf_links = {}

print("Discovering documents from main sections...")
for section, base_url in SECTIONS.items():
    print(f"\nScanning {section}...")
    start_page = 1
    section_links = {}
    
    while True:
        # Liferay pagination
        if start_page == 1:
            page_url = base_url
        else:
            page_url = f"{base_url}?p_p_id=com_irdai_document_media_IRDAIDocumentMediaPortlet&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&_com_irdai_document_media_IRDAIDocumentMediaPortlet_delta=20&_com_irdai_document_media_IRDAIDocumentMediaPortlet_resetCur=false&_com_irdai_document_media_IRDAIDocumentMediaPortlet_cur={start_page}"
        
        html = fetch_html(page_url)
        if not html: break
        
        soup = BeautifulSoup(html, "html.parser")
        
        found_pdfs = 0
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if ".pdf" in href.lower() and "documents/" in href.lower():
                # Format: /documents/37343/365525/FILENAME.pdf/UUID?version=1.0...
                
                # Extract original PDF name from URL
                m = re.search(r'/([^/]+\.[pP][dD][fF])', href)
                if m:
                    raw_name = m.group(1)
                else:
                    raw_name = f"document_page{start_page}"
                    
                title = clean_filename(raw_name)
                # Fallback to avoid empty names
                if not title or title.lower() == "pdf": 
                    title = a.get_text(strip=True)
                    title = clean_filename(title)
                    if not title: title = f"document_{start_page}"
                    
                filename = f"IRDAI_{section}_{title}.pdf"
                
                # Base URL for deduplication
                base_href = href.split("?")[0]
                
                if base_href not in section_links:
                    section_links[base_href] = filename
                    found_pdfs += 1
        
        print(f"  Page {start_page}: Found {found_pdfs} new PDFs")
        
        # Check if we hit the end of pagination (Liferay usually returns same page or no PDFs)
        if found_pdfs == 0:
            break
            
        start_page += 1
        
    print(f"-> Found {len(section_links)} total PDFs for {section}")
    for link, fname in section_links.items():
        all_pdf_links[link] = fname

all_pdfs_list = list(all_pdf_links.items())
print(f"\nTotal unique PDFs discovered: {len(all_pdfs_list)}")

if not all_pdfs_list:
    print("Could not find any PDFs. Check site structure.")
    sys.exit(0)

print(f"\nDownloading to: {OUT_DIR}")
success = 0
skipped = 0
errors = 0

with ThreadPoolExecutor(max_workers=5) as executor: # 5 workers as files can be large
    futures = {executor.submit(download_file, item): item for item in all_pdfs_list}
    
    with tqdm(total=len(all_pdfs_list), desc="Downloading", unit="pdf") as pbar:
        for future in as_completed(futures):
            status, fname = future.result()
            if status == "ok": success += 1
            elif status == "skipped": skipped += 1
            else: errors += 1
            
            pbar.update(1)
            pbar.set_postfix(ok=success, skip=skipped, err=errors)

print(f"\nFinished! Downloaded: {success}, Skipped: {skipped}, Errors: {errors}")
