import os
import sys
import re
import urllib.request
import ssl
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

BASE_URL = "https://www.pfrda.org.in"

SECTIONS = {
    "circulars_active": "https://www.pfrda.org.in/regulatory-framework/circulars/active-circulars",
    "circulars_archived": "https://www.pfrda.org.in/regulatory-framework/circulars/inoperative",
    "master_circulars_active": "https://www.pfrda.org.in/regulatory-framework/master-circulars/active-master-circulars",
    "master_circulars_archived": "https://www.pfrda.org.in/regulatory-framework/master-circulars/archived-master-circulars",
    "regulations": "https://www.pfrda.org.in/regulatory-framework/regulations",
    "guidelines": "https://www.pfrda.org.in/regulatory-framework/guidelines",
    "notifications": "https://www.pfrda.org.in/regulatory-framework/notifications"
}

OUT_DIR = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\pfrda"
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch_html(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return ""

def download_file(item):
    pdf_url, filename = item
    if not pdf_url.startswith("http"):
        pdf_url = BASE_URL.rstrip('/') + '/' + pdf_url.lstrip('/')
        
    filepath = os.path.join(OUT_DIR, filename)
    
    if os.path.exists(filepath) and os.path.getsize(filepath) > 5000:
        return "skipped", filename
        
    try:
        req = urllib.request.Request(pdf_url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            data = resp.read()
            if data[:4] == b'%PDF':
                with open(filepath, 'wb') as f:
                    f.write(data)
                return "ok", filename
            return "not_pdf", filename
    except Exception as e:
        return "error", filename

def clean_filename(title):
    title = re.sub(r'[^\w\s-]', '', title)[:100]
    return re.sub(r'[-\s]+', '_', title.strip())

# ============================================================
# MAIN
# ============================================================
print("=" * 70)
print("PFRDA Scraper v2 (Source 9)")
print("=" * 70)

all_pdf_links = set()

print("Discovering documents from main sections...")
for section, base_url in SECTIONS.items():
    print(f"  Scanning {section}...")
    start_page = 1
    section_links = set()
    while True:
        page_url = f"{base_url}?delta=60&start={start_page}"
        html = fetch_html(page_url)
        if not html: break
        
        soup = BeautifulSoup(html, "html.parser")
        detail_links = set()
        for a in soup.find_all("a", href=True):
            if "/w/" in a["href"] and "?" in a["href"]:
                href = a["href"]
                if not href.startswith("http"):
                    href = BASE_URL.rstrip('/') + '/' + href.lstrip('/')
                detail_links.add(href)
        
        if not detail_links:
            break
            
        print(f"    Page {start_page}: Found {len(detail_links)} detail links")
        
        # Now fetch detail links
        for detail_url in detail_links:
            detail_html = fetch_html(detail_url)
            if not detail_html: continue
            dsoup = BeautifulSoup(detail_html, "html.parser")
            
            # Find PDF links
            for a in dsoup.find_all("a", href=True):
                href = a["href"]
                if href.lower().endswith(".pdf"):
                    title = a.get_text(strip=True)
                    if not title or title.lower() == "pdf":
                        # Try to get title from the detail page heading
                        h2 = dsoup.find("h2")
                        if h2: title = h2.get_text(strip=True)
                        else: title = "Document"
                    
                    filename = f"PFRDA_{section}_{clean_filename(title)}.pdf"
                    section_links.add((href, filename))
        
        all_pdf_links.update(section_links)
        
        # If less than 60 detail links on this page, it's the last page
        if len(detail_links) < 60:
            break
            
        start_page += 1
        
    print(f"    -> Found {len(section_links)} total PDFs for {section}")

all_pdfs_list = list(all_pdf_links)
print(f"\nTotal unique PDFs discovered: {len(all_pdfs_list)}")

if not all_pdfs_list:
    print("Could not find any PDFs. PFRDA structure might have changed again.")
    sys.exit(0)

print(f"\nDownloading to: {OUT_DIR}")
success = 0
skipped = 0
errors = 0

with ThreadPoolExecutor(max_workers=10) as executor:
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
