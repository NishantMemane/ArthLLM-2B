import json
import os
import requests
import concurrent.futures
from tqdm import tqdm
import re

metadata_dir = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\cbdt_metadata"
out_dir = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\IncomeTax"
circulars_dir = os.path.join(out_dir, "Circulars")
notifications_dir = os.path.join(out_dir, "Notifications")

os.makedirs(circulars_dir, exist_ok=True)
os.makedirs(notifications_dir, exist_ok=True)

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)[:100]

def download_file(url, out_path):
    if os.path.exists(out_path):
        return True
    try:
        r = requests.get(url, stream=True, timeout=15, verify=False)
        if r.status_code == 200:
            with open(out_path, 'wb') as f:
                for chunk in r.iter_content(1024 * 1024):
                    f.write(chunk)
            return True
    except:
        pass
    return False

def process_items(json_file, target_dir, prefix):
    with open(json_file, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    # Filter items that have a URL
    valid_items = [i for i in items if i.get('url')]
    
    print(f"Starting download of {len(valid_items)} {prefix} files...")
    
    def task(item):
        title = sanitize_filename(item.get('title', 'Unknown'))
        url = item.get('url')
        ext = url.split('.')[-1] if '.' in url[-6:] else 'pdf'
        filename = f"{prefix}_{title}.{ext}"
        out_path = os.path.join(target_dir, filename)
        
        success = download_file(url, out_path)
        return success

    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(task, item) for item in valid_items]
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(valid_items), desc=f"Downloading {prefix}"):
            if future.result():
                success_count += 1
                
    print(f"Downloaded {success_count}/{len(valid_items)} files to {target_dir}")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    
    circ_json = os.path.join(metadata_dir, "cbdt_circulars_final.json")
    notif_json = os.path.join(metadata_dir, "cbdt_notifications_final.json")
    
    if os.path.exists(circ_json):
        process_items(circ_json, circulars_dir, "Circular")
    if os.path.exists(notif_json):
        process_items(notif_json, notifications_dir, "Notification")
    
    print("All downloads complete!")
