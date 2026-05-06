"""
RBI Financial Stability Report Scraper v2
==========================================
Strategy: FSR PDFs use hash-based filenames that can't be guessed.
Each chapter has a unique PublicationReportDetails ID.
We scan the ID range and grab every PDF link from pages that 
contain "Financial Stability" in the title.

The Reports section IDs go from ~700 to ~1330 (covers 2010-2025).
Each FSR has ~7 chapters with consecutive IDs.
"""
import os
import sys
import io
import re
import time
import json
import urllib.request
import urllib.error

try:
    from tqdm import tqdm
except ImportError:
    os.system(f'"{sys.executable}" -m pip install tqdm -q')
    from tqdm import tqdm

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

OUT_PDF = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\rbi\financial_stability_reports\downloads\pdfs"
OUT_TEXT = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\rbi\financial_stability_reports\downloads\text"
CHECKPOINT = os.path.join(OUT_PDF, "_fsr_checkpoint.json")

os.makedirs(OUT_PDF, exist_ok=True)
os.makedirs(OUT_TEXT, exist_ok=True)

BASE_URL = "https://www.rbi.org.in/Scripts/PublicationReportDetails.aspx?ID={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.rbi.org.in/Scripts/Publications.aspx?publication=Reports",
}

# Resume support
done_ids = set()
fsr_pdfs = []
fsr_pages = []
if os.path.exists(CHECKPOINT):
    with open(CHECKPOINT, "r") as f:
        try:
            data = json.load(f)
            done_ids = set(data.get("scanned_ids", []))
            fsr_pdfs = data.get("fsr_pdfs", [])
            fsr_pages = data.get("fsr_pages", [])
        except:
            pass

# Force rescan if fsr_pdfs is suspiciously low
if len(fsr_pdfs) == 0:
    done_ids = set()

# ID range for Reports (FSR started in 2010, IDs ~700+)
# We scan 700-1330 to cover all possible FSR chapters
START_ID = 700
END_ID = 1340

non_fsr = 0
errors = 0
not_found = 0

ids_to_scan = [i for i in range(START_ID, END_ID + 1) if i not in done_ids]

print("=" * 70)
print("RBI Financial Stability Report Scraper v2")
print("=" * 70)
print(f"Scanning Publication IDs: {START_ID} to {END_ID}")
print(f"Already scanned: {len(done_ids)} | Remaining: {len(ids_to_scan)}")
print("=" * 70)

with tqdm(total=len(ids_to_scan), desc="Scanning IDs", unit="id",
          bar_format="{l_bar}{bar:40}{r_bar}") as pbar:
    
    for pub_id in ids_to_scan:
        url = BASE_URL.format(pub_id)
        
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                html = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 403:
                tqdm.write(f"  [403] Blocked at ID {pub_id} — waiting 30s...")
                time.sleep(30)
                errors += 1
                pbar.update(1)
                continue
            not_found += 1
            done_ids.add(pub_id)
            pbar.update(1)
            time.sleep(0.3)
            continue
        except Exception:
            errors += 1
            pbar.update(1)
            time.sleep(0.3)
            continue
        
        # Check if this page is about Financial Stability Report
        if "financial stability" not in html.lower():
            non_fsr += 1
            done_ids.add(pub_id)
            pbar.update(1)
            pbar.set_postfix(fsr=len(fsr_pdfs), skip=non_fsr, err=errors)
            time.sleep(0.3)
            continue
        
        # It's an FSR page! Extract the PDF link
        # Pattern: href="https://rbidocs.rbi.org.in/rdocs//PublicationReport/Pdfs/XXXXX.PDF"
        pdf_links = re.findall(
            r'href=[\'"](https?://rbidocs\.rbi\.org\.in/[^\'"]+\.(?:PDF|pdf))[\'"]',
            html, re.IGNORECASE
        )
        
        # Extract the chapter/section title
        title = ""
        title_match = re.search(r"<title>(.*?)</title>", html, re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()
        
        # Try to find the specific report title in the content
        report_title = ""
        # Look for the report name in the page content
        rt_match = re.search(r'(?:Financial Stability Report[^<]*(?:June|December|January|July|March|September)\s*\d{4})', html, re.IGNORECASE)
        if rt_match:
            report_title = rt_match.group(0).strip()
        else:
            # Try to find date context
            date_match = re.search(r'((?:June|December|January|July|March)\s*\d{4})', html)
            if date_match:
                report_title = f"FSR_{date_match.group(1).replace(' ', '_')}"
            else:
                report_title = f"FSR_ID_{pub_id}"
        
        # Find chapter info
        chapter = ""
        ch_patterns = [
            r'(Chapter\s+[IVX]+[^<]*)',
            r'(Contents)',
            r'(Foreword)',
            r'(Overview)',
            r'(Annex)',
            r'(List of Select Abbreviations)',
        ]
        for pat in ch_patterns:
            ch_match = re.search(pat, html, re.IGNORECASE)
            if ch_match:
                chapter = ch_match.group(1).strip()[:60]
                break
        
        if pdf_links:
            for pdf_url in pdf_links:
                # Download the PDF
                pdf_name = re.sub(r'[^\w.-]', '_', report_title)
                if chapter:
                    pdf_name += f"_{re.sub(r'[^\w]', '_', chapter)}"
                pdf_name = f"ID{pub_id}_{pdf_name}.pdf"
                pdf_path = os.path.join(OUT_PDF, pdf_name)
                
                if not os.path.exists(pdf_path):
                    try:
                        pdf_req = urllib.request.Request(pdf_url, headers=HEADERS)
                        with urllib.request.urlopen(pdf_req, timeout=120) as pdf_resp:
                            pdf_data = pdf_resp.read()
                            if pdf_data[:4] == b'%PDF':
                                with open(pdf_path, 'wb') as f:
                                    f.write(pdf_data)
                                fsr_pdfs.append({
                                    "id": pub_id,
                                    "title": report_title,
                                    "chapter": chapter,
                                    "pdf_url": pdf_url,
                                    "pdf_file": pdf_name,
                                    "size": len(pdf_data),
                                })
                                tqdm.write(f"  [PDF] ID {pub_id}: {report_title} | {chapter} ({len(pdf_data)//1024} KB)")
                            else:
                                tqdm.write(f"  [BAD] ID {pub_id}: Not a valid PDF")
                    except Exception as e:
                        tqdm.write(f"  [ERR] ID {pub_id}: Failed to download PDF: {str(e)[:50]}")
                        errors += 1
                else:
                    fsr_pdfs.append({"id": pub_id, "title": report_title, "chapter": chapter, "pdf_file": pdf_name})
                    tqdm.write(f"  [SKIP] ID {pub_id}: Already have {pdf_name}")
        else:
            # FSR page but no PDF link found — save page info anyway
            fsr_pages.append({"id": pub_id, "title": report_title, "chapter": chapter})
            tqdm.write(f"  [PAGE] ID {pub_id}: FSR page found but no PDF link: {report_title} | {chapter}")
        
        done_ids.add(pub_id)
        pbar.update(1)
        pbar.set_postfix(fsr=len(fsr_pdfs), skip=non_fsr, err=errors)
        
        # Save checkpoint every 50 IDs
        if len(done_ids) % 50 == 0:
            with open(CHECKPOINT, "w") as f:
                json.dump({
                    "scanned_ids": list(done_ids),
                    "fsr_pdfs": fsr_pdfs,
                    "fsr_pages": fsr_pages,
                }, f, indent=2)
        
        time.sleep(0.5)

# Final checkpoint
with open(CHECKPOINT, "w") as f:
    json.dump({
        "scanned_ids": list(done_ids),
        "fsr_pdfs": fsr_pdfs,
        "fsr_pages": fsr_pages,
    }, f, indent=2)

# ============================================================
# SUMMARY
# ============================================================
print(f"\n{'=' * 70}")
print("SCAN COMPLETE")
print(f"{'=' * 70}")
print(f"IDs scanned:     {len(done_ids)}")
print(f"FSR PDFs found:  {len(fsr_pdfs)}")
print(f"FSR pages (no PDF): {len(fsr_pages)}")
print(f"Non-FSR pages:   {non_fsr}")
print(f"Not found (404): {not_found}")
print(f"Errors:          {errors}")
print(f"PDFs saved to:   {OUT_PDF}")

if fsr_pdfs:
    print(f"\nDownloaded FSR PDFs:")
    for p in fsr_pdfs:
        size_kb = p.get('size', 0) // 1024
        print(f"  ID {p['id']:4d} | {p['title'][:40]:40s} | {p['chapter'][:30]:30s} | {size_kb} KB")
