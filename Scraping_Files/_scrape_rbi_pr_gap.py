"""
RBI Press Release Gap Filler — PRIDs 44520 to 62579
=====================================================
20 concurrent workers with tqdm progress bar.
Downloads ~18,000 missing press releases (mid-2018 to March 2026).
Resume-capable via checkpoint file.
"""
import os, sys, io, re, json, time
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

try:
    from tqdm import tqdm
except ImportError:
    print("Installing tqdm...")
    os.system(f'"{sys.executable}" -m pip install tqdm -q')
    from tqdm import tqdm

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ============================================================
# CONFIG
# ============================================================
OUT_DIR = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\rbi\press_releases\downloads\text"
CHECKPOINT = os.path.join(OUT_DIR, "_gap_checkpoint.json")
BASE_URL = "https://rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid={}"

START_PRID = 44520
END_PRID = 62579
WORKERS = 20
DELAY_PER_WORKER = 0.3  # 20 workers × 0.3s = ~6 req/sec total

# Thread-safe counters
lock = Lock()
stats = {"success": 0, "not_found": 0, "errors": 0, "mp_found": 0}
mp_titles = []

# ============================================================
# LOAD EXISTING / CHECKPOINT
# ============================================================
existing_prids = set()
for fname in os.listdir(OUT_DIR):
    m = re.match(r"(\d+)_", fname)
    if m:
        existing_prids.add(int(m.group(1)))

if os.path.exists(CHECKPOINT):
    with open(CHECKPOINT, "r") as f:
        data = json.load(f)
        for p in data.get("downloaded", []):
            existing_prids.add(p)
        for p in data.get("not_found", []):
            existing_prids.add(p)

# PRIDs to download
all_prids = [p for p in range(START_PRID, END_PRID + 1) if p not in existing_prids]
print(f"Total range: {START_PRID}-{END_PRID} ({END_PRID - START_PRID + 1} PRIDs)")
print(f"Already have: {len(existing_prids)} | To download: {len(all_prids)}")
print(f"Workers: {WORKERS} | Est. time: {len(all_prids) * DELAY_PER_WORKER / WORKERS / 60:.0f} min")
print("=" * 70)

# ============================================================
# DOWNLOADER
# ============================================================
def download_one(prid):
    """Download and save a single press release. Returns (prid, status, title)."""
    url = BASE_URL.format(prid)
    
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    })
    
    time.sleep(DELAY_PER_WORKER)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            return (prid, "not_found", "")
        if e.code == 403:
            time.sleep(30)
            return (prid, "error_403", "")
        if e.code == 429:
            time.sleep(60)
            return (prid, "error_429", "")
        return (prid, "error", str(e))
    except Exception as e:
        return (prid, "error", str(e))
    
    if len(html) < 500:
        return (prid, "not_found", "")
    
    # Extract title
    title_match = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
    title = title_match.group(1).strip() if title_match else ""
    title = re.sub(r"\s+", " ", title).replace(" - Reserve Bank of India", "").strip()
    
    if not title or "page not found" in title.lower() or "error" in title.lower():
        return (prid, "not_found", "")
    
    # Extract date
    date = ""
    m = re.search(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}", html)
    if m:
        date = m.group(0)
    
    # Extract body text
    body = ""
    main = re.search(r'id="mainsection".*?>(.*?)(?:</div>\s*){3,}', html, re.DOTALL)
    if not main:
        main = re.search(r'class="tablebg".*?>(.*?)(?:</div>\s*){2,}', html, re.DOTALL)
    if main:
        raw = main.group(1)
    else:
        body_m = re.search(r"<body.*?>(.*?)</body>", html, re.DOTALL)
        raw = body_m.group(1) if body_m else html
    
    text = re.sub(r"<script.*?</script>", "", raw, flags=re.DOTALL)
    text = re.sub(r"<style.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "\n", text)
    for old, new in [("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&#39;", "'"), ("&quot;", '"')]:
        text = text.replace(old, new)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    body = text.strip()
    
    if len(body) < 20:
        return (prid, "not_found", "")
    
    # Detect category
    category = "general"
    combined = (title + " " + body[:500]).lower()
    mp_keywords = ["monetary policy", "mpc", "repo rate", "reverse repo", "liquidity adjustment",
                    "money market", "bi-monthly", "bimonthly", "policy rate", "bank rate",
                    "developmental and regulatory", "governor's statement"]
    for kw in mp_keywords:
        if kw in combined:
            category = "monetary_policy"
            break
    
    # Save file
    title_clean = re.sub(r'[^\w\s-]', '', title)[:80].strip().replace(" ", "_")
    fname = f"{prid}_{title_clean}.txt"
    fpath = os.path.join(OUT_DIR, fname)
    
    content = f"PRID: {prid}\nURL: {url}\nTITLE: {title}\nDATE: {date}\nCATEGORY: {category}\n{'=' * 70}\n\n{body}\n"
    
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    
    return (prid, "success", title, category)

# ============================================================
# RUN WITH THREAD POOL
# ============================================================
downloaded_prids = []
not_found_prids = []

global_total = END_PRID - START_PRID + 1
already_done_count = len(existing_prids) - 44490 # Subtract the ones we had before this gap fill
if already_done_count < 0: already_done_count = 0

with ThreadPoolExecutor(max_workers=WORKERS) as executor:
    futures = {executor.submit(download_one, prid): prid for prid in all_prids}
    
    with tqdm(total=global_total, desc="Downloading PRs", unit="pr",
              bar_format="{l_bar}{bar:40}{r_bar}{bar:-10b}", initial=already_done_count) as pbar:
        for future in as_completed(futures):
            try:
                result = future.result()
                prid = result[0]
                status = result[1]
                
                with lock:
                    if status == "success":
                        stats["success"] += 1
                        downloaded_prids.append(prid)
                        title = result[2]
                        cat = result[3] if len(result) > 3 else ""
                        if cat == "monetary_policy":
                            stats["mp_found"] += 1
                            mp_titles.append(f"PRID {prid}: {title[:70]}")
                    elif status == "not_found":
                        stats["not_found"] += 1
                        not_found_prids.append(prid)
                    else:
                        stats["errors"] += 1
                    
                    pbar.set_postfix(
                        ok=stats["success"],
                        miss=stats["not_found"],
                        err=stats["errors"],
                        mp=stats["mp_found"]
                    )
                pbar.update(1)
                
                # Checkpoint every 500
                if (stats["success"] + stats["not_found"]) % 500 == 0:
                    with lock:
                        with open(CHECKPOINT, "w") as f:
                            json.dump({
                                "downloaded": downloaded_prids,
                                "not_found": not_found_prids,
                                "stats": stats,
                            }, f)
                            
            except Exception as e:
                with lock:
                    stats["errors"] += 1
                pbar.update(1)

# Final checkpoint
with open(CHECKPOINT, "w") as f:
    json.dump({
        "downloaded": downloaded_prids,
        "not_found": not_found_prids,
        "stats": stats,
    }, f)

# ============================================================
# SUMMARY
# ============================================================
print(f"\n{'=' * 70}")
print(f"DOWNLOAD COMPLETE")
print(f"{'=' * 70}")
print(f"Successfully downloaded: {stats['success']}")
print(f"Not found (404/empty):  {stats['not_found']}")
print(f"Errors:                 {stats['errors']}")
print(f"Monetary policy found:  {stats['mp_found']}")
total_files = len([f for f in os.listdir(OUT_DIR) if f.endswith('.txt') and not f.startswith('_')])
print(f"Total text files now:   {total_files}")

if mp_titles:
    print(f"\nMonetary Policy Documents Found:")
    for t in mp_titles:
        print(f"  {t}")
