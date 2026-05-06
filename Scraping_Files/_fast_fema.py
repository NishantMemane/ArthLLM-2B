import requests
from bs4 import BeautifulSoup
import json
import os
import urllib3
urllib3.disable_warnings()

out_dir = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\RBI_FEMA"
os.makedirs(out_dir, exist_ok=True)

url = "https://rbi.org.in/scripts/bs_viewfemanewnotification.aspx"

print(f"Fetching {url}...")
s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0"})
s.verify = False

r = s.get(url, timeout=15)
if r.status_code == 200:
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Usually RBI data tables are standard HTML tables.
    table = soup.find('table', class_='tablebg')
    if not table:
        table = soup.find('table') # Fallback to first table
        
    items = []
    if table:
        rows = table.find_all('tr')
        print(f"Found {len(rows)} rows in the table.")
        
        # Skip header row
        for row in rows[1:]:
            cols = row.find_all('td')
            if len(cols) >= 3:
                # Find the link in the first or second column
                a_tag = None
                for col in cols:
                    a_tag = col.find('a')
                    if a_tag and 'href' in a_tag.attrs:
                        break
                
                if a_tag:
                    title = a_tag.text.strip().replace('\r', '').replace('\n', ' ')
                    href = a_tag['href']
                    if href.startswith('http'):
                        pdf_url = href
                    else:
                        pdf_url = "https://rbi.org.in/scripts/" + href
                    
                    items.append({
                        "title": title,
                        "url": pdf_url
                    })
    
    print(f"Extracted {len(items)} FEMA notifications.")
    
    metadata_file = os.path.join(out_dir, "fema_metadata.json")
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    
    print("Saved metadata. Now downloading PDFs...")
    # Fast download
    import concurrent.futures
    from tqdm import tqdm
    import re
    
    def sanitize(name):
        return re.sub(r'[\\/*?:"<>|]', "", name)[:150]
        
    def download(item):
        title = sanitize(item['title'])
        out_path = os.path.join(out_dir, f"{title}.pdf")
        if os.path.exists(out_path): return True
        try:
            resp = s.get(item['url'], timeout=15, stream=True)
            if resp.status_code == 200:
                with open(out_path, 'wb') as f:
                    for chunk in resp.iter_content(1024*1024):
                        f.write(chunk)
                return True
        except:
            pass
        return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(download, i) for i in items]
        for _ in tqdm(concurrent.futures.as_completed(futures), total=len(items), desc="Downloading FEMA"):
            pass
            
    print("Done downloading FEMA notifications!")
else:
    print(f"Error fetching: {r.status_code}")
