import os
import sys
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from tqdm import tqdm
except ImportError:
    os.system(f'"{sys.executable}" -m pip install tqdm -q')
    from tqdm import tqdm

OUT_DIR = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\other_regulators\fema\downloads\pdfs"
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

def get_fema_links():
    print("Discovering RBI FEMA Notifications...")
    # The main page lists years or notifications directly
    url = "https://www.rbi.org.in/Scripts/BS_FemaNotifications.aspx"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"Error fetching main FEMA page: {e}")
        return []

    # Extract all links that look like Notification Detail pages
    # Usually Fema.aspx or NotificationUser.aspx?Id=
    detail_links = re.findall(r'href="(NotificationUser\.aspx\?Id=\d+&Mode=0)"', html)
    detail_links = [f"https://www.rbi.org.in/Scripts/{l}" for l in detail_links]
    
    # Also check years
    years = re.findall(r'href="(BS_FemaNotifications\.aspx\?year=\d+)"', html)
    for y in set(years):
        y_url = f"https://www.rbi.org.in/Scripts/{y}"
        try:
            y_html = urllib.request.urlopen(urllib.request.Request(y_url, headers=HEADERS), timeout=30).read().decode('utf-8', errors='replace')
            more_links = re.findall(r'href="(NotificationUser\.aspx\?Id=\d+&Mode=0)"', y_html)
            detail_links.extend([f"https://www.rbi.org.in/Scripts/{l}" for l in more_links])
        except:
            pass

    detail_links = list(set(detail_links))
    print(f"Found {len(detail_links)} detail pages to scan for PDFs.")
    
    pdf_tasks = []
    
    for dlink in tqdm(detail_links, desc="Scanning for PDFs"):
        try:
            dhtml = urllib.request.urlopen(urllib.request.Request(dlink, headers=HEADERS), timeout=20).read().decode('utf-8', errors='replace')
            pdfs = re.findall(r'href="(https?://rbidocs\.rbi\.org\.in/rdocs/notification/PDFs/[^"]+\.pdf)"', dhtml, re.I)
            
            title_match = re.search(r'<title>(.*?)</title>', dhtml, re.I)
            title = title_match.group(1).strip() if title_match else "FEMA_Notification"
            clean_title = re.sub(r'[^\w\s-]', '', title)[:100].strip().replace(' ', '_')
            
            for p in pdfs:
                fname = f"RBI_FEMA_{clean_title}_{p.split('/')[-1]}"
                pdf_tasks.append((p, fname))
        except:
            pass

    return list(set(pdf_tasks))

def download_file(url, filename):
    filepath = os.path.join(OUT_DIR, filename)
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1024:
        return "skipped"
        
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            if data[:4] == b"%PDF":
                with open(filepath, "wb") as f:
                    f.write(data)
                return "ok"
            return "error"
    except:
        return "error"

if __name__ == "__main__":
    tasks = get_fema_links()
    print(f"\nFound {len(tasks)} unique RBI FEMA PDFs to download.")
    
    success = 0
    skipped = 0
    errors = 0
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(download_file, url, name): (url, name) for url, name in tasks}
        with tqdm(total=len(tasks), desc="Downloading FEMA") as pbar:
            for future in as_completed(futures):
                res = future.result()
                if res == "ok": success += 1
                elif res == "skipped": skipped += 1
                else: errors += 1
                pbar.update(1)
                pbar.set_postfix(ok=success, skip=skipped, err=errors)
                
    print(f"\nDone! Success: {success}, Skipped: {skipped}, Errors: {errors}")
