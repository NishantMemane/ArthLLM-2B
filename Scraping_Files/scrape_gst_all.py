"""
GST Complete Document Scraper
=============================
Scrapes ALL GST documents from gstcouncil.gov.in, cbic-gst.gov.in, and taxinformation.cbic.gov.in.
Resume-capable (skips existing files). Progress bars throughout.

Usage:  python scrape_gst_all.py
"""

import requests, os, re, json, time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import urllib3
urllib3.disable_warnings()

# ─── CONFIG ───────────────────────────────────────────────────────────────────
BASE = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\GST"
STATE_FILE = os.path.join(BASE, "_scraper_state.json")

SECTIONS = {
    # (url_path, max_pages or None to auto-detect, subfolder)
    "CGST_Notifications":           ("cgst-tax-notification",              54, "Notifications/CGST"),
    "CGST_Rate_Notifications":      ("cgst-tax-rate-notification",         None, "Notifications/CGST_Rate"),
    "IGST_Notifications":           ("igst-tax-notification",              None, "Notifications/IGST"),
    "IGST_Rate_Notifications":      ("igst-tax-rate-notification",         None, "Notifications/IGST_Rate"),
    "UTGST_Notifications":          ("utgst-tax-notification",             None, "Notifications/UTGST"),
    "UTGST_Rate_Notifications":     ("utgst-tax-rate-notification",        None, "Notifications/UTGST_Rate"),
    "Compensation_Cess":            ("compensation-cess-notification",     None, "Notifications/Compensation_Cess"),
    "Compensation_Cess_Rate":       ("compensation-cess-rate-notification",None, "Notifications/Compensation_Cess_Rate"),
    "CGST_Circulars":               ("cgst-circulars",                     None, "Circulars/CGST"),
    "IGST_Circulars":               ("igst-circulars",                     None, "Circulars/IGST"),
    "CGST_Orders":                  ("cgst-orders",                        None, "Orders"),
    "CGST_Instructions":            ("cgst-instructions",                  None, "Instructions"),
    "Press_Releases":               ("archive-press-release",              9,    "Press_Releases"),
}

# ─── GST Council Meeting Minutes — exact filenames from user ──────────────────
MINUTES_BASE = "https://gstcouncil.gov.in/sites/default/files/Minutes/"
AGENDA_BASE  = "https://gstcouncil.gov.in/sites/default/files/Agenda/"
MINUTES = {
    "01st": f"{MINUTES_BASE}Signed-Minutes-1st-GST-Council-Meeting.pdf",
    "02nd": f"{MINUTES_BASE}Signed-Minutes-2nd-GST-Council-Meeting.pdf",
    "03rd": f"{MINUTES_BASE}Signed-Minutes-3rd-GST-Council-Meeting.pdf",
    "04th": f"{MINUTES_BASE}Signed-Minutes-4th-GST-Council-Meeting.pdf",
    "05th": f"{MINUTES_BASE}Signed-Minutes-5th-GST-Council-Meeting.pdf",
    "06th": f"{MINUTES_BASE}Signed-Minutes-6th-GST-Council-Meeting.pdf",
    "07th": f"{MINUTES_BASE}Signed-Minutes-7th-GST-Council-Meeting.pdf",
    "08th": f"{MINUTES_BASE}Signed-Minutes-8th-GST-Council-Meeting.pdf",
    "09th": f"{MINUTES_BASE}Signed-Minutes-9th-GST-Council-Meeting.pdf",
    "10th": f"{MINUTES_BASE}Signed-Minutes-10th-GST-Council-Meeting.pdf",
    "11th": f"{MINUTES_BASE}Signed-Minutes-11th-GST-Council-Meeting.pdf",
    "12th": f"{MINUTES_BASE}Signed-Minutes-12th-GST-Council-Meeting.pdf",
    "13th": f"{MINUTES_BASE}Signed-Minutes-13th-GST-Council-Meeting.pdf",
    "14th": f"{MINUTES_BASE}Signed-Minutes-14th-GST-Council-Meeting.pdf",
    "15th": f"{MINUTES_BASE}Signed-Minutes-15th-GST-Council-Meeting.pdf",
    "16th": f"{MINUTES_BASE}Signed-Minutes-16th-GST-Council-Meeting.pdf",
    "17th": f"{MINUTES_BASE}Signed-Minutes-17th-GST-Council-Meeting.pdf",
    "18th": f"{MINUTES_BASE}Signed-Minutes-18th-GST-Council-Meeting.pdf",
    "19th": f"{MINUTES_BASE}Signed_Minutes-19th_GST_Council_Meeting.pdf",
    "20th": f"{MINUTES_BASE}Signed-Minutes-20th-GST-Council-Meeting.pdf",
    "21st": f"{MINUTES_BASE}Signed-Minutes-21st-GST-Council-Meeting.pdf",
    "22nd": f"{MINUTES_BASE}Signed-Minutes-22nd-GST-Council-Meeting.pdf",
    "23rd": f"{MINUTES_BASE}Signed-Minutes-23rd-GST-Council-Meeting.pdf",
    "24th": f"{MINUTES_BASE}Signed-Minutes-24th-GST-Council-Meeting.pdf",
    "25th": f"{MINUTES_BASE}Signed-Minutes-25th-GST-Council-Meeting.pdf",
    "26th": f"{MINUTES_BASE}Signed-Minutes-26th-GST-Council-Meeting.pdf",
    "27th": f"{MINUTES_BASE}Signed-Minutes-27th-GST-Council-Meeting.pdf",
    "28th": f"{MINUTES_BASE}Signed-Minutes-28th-GST-Council-Meeting.pdf",
    "29th": f"{MINUTES_BASE}Signed-Minutes-29th-GST-Council-Meeting.pdf",
    "30th": f"{MINUTES_BASE}Signed-Minutes-30th-GST-Council-Meeting.pdf",
    "31st": f"{MINUTES_BASE}Signed-Minutes-31st-GST-Council-Meeting.pdf",
    "32nd": f"{MINUTES_BASE}Signed-Minutes-32nd-GST-Council-Meeting.pdf",
    "33rd": f"{MINUTES_BASE}Signed-Minutes-33rd-GST-Council-Meeting.pdf",
    "34th": f"{MINUTES_BASE}Signed_Minutes-34th_GST_Council_Meeting.pdf",
    "35th": f"{AGENDA_BASE}Signed-Minutes-35th-GST-Council-Meeting.pdf",
    "36th": f"{MINUTES_BASE}Signed-Minutes-36th-GST-Council-Meeting.pdf",
    "37th": f"{MINUTES_BASE}Signed-Minutes-37th-GST-Council-Meeting.pdf",
    "38th": f"{MINUTES_BASE}Signed_Minutes_38th_GST_Council_Meeting.pdf",
    "39th": f"{MINUTES_BASE}Signed-Minutes-39th-GSTCM.pdf",
    "40th": f"{MINUTES_BASE}Minutes-40th-GSTC-Meeting.pdf",
    "41st": f"{MINUTES_BASE}Minutes-%2041st-GSTC-Meeting.pdf",
    "42nd": f"{MINUTES_BASE}42nd-GSTC-Minutes-Signed.pdf",
    "43rd": f"{MINUTES_BASE}Minutes_of_43rd_GSTCM.pdf",
    "44th": f"{MINUTES_BASE}Minutes_of_44th_GSTCM.pdf",
    "45th": f"{MINUTES_BASE}45TH_MEETING.pdf",
    "46th": f"{MINUTES_BASE}46TH_MEETING_MINUTES.pdf",
    "47th": f"{MINUTES_BASE}47_MINUTES.pdf",
    "48th": f"{MINUTES_BASE}48THMINUTES.pdf",
    "49th": f"{MINUTES_BASE}49TH_MEETING_MINUTES.pdf",
    "50th": f"{MINUTES_BASE}Minutes_of_50th.pdf",
    "51st": f"{MINUTES_BASE}Minutes_of_51st.pdf",
}

# ─── Foundational / Archive docs ─────────────────────────────────────────────
ARCHIVE_DOCS = {
    "First_Discussion_Paper_on_GST.pdf":  "https://gstcouncil.gov.in/sites/default/files/2024-02/first_discussion_paper_on_gst.pdf",
    "Comments_DOR_1st_Discussion_Paper.pdf": "https://gstcouncil.gov.in/sites/default/files/2024-02/comments-dor-1st-discn-paper-01012010.pdf",
    "Constitution_Amendment_Act.pdf": "https://gstcouncil.gov.in/sites/default/files/2024-02/consti-amend-act.pdf",
    "CEA_Report_RNR.pdf": "https://gstcouncil.gov.in/sites/default/files/2024-02/cea-rpt-rnr.pdf",
    "Organizational_Chart.pdf": "https://gstcouncil.gov.in/sites/default/files/2024-04/organizational-chart.pdf",
}

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def get_session():
    s = requests.Session()
    s.verify = False
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    return s

def sanitize(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()[:200]

def download_file(session, url, out_path, retries=3):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return True
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=30, stream=True)
            if r.status_code == 200:
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, 'wb') as f:
                    for chunk in r.iter_content(1024 * 1024):
                        f.write(chunk)
                return True
            elif r.status_code == 404:
                return False
        except Exception:
            time.sleep(2)
    return False

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"completed_sections": [], "downloaded_files": 0}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

# ─── PAGINATED SECTION SCRAPER ───────────────────────────────────────────────
def scrape_paginated_section(session, section_name, url_path, max_pages, out_folder):
    """Scrape all PDF links from a paginated gstcouncil.gov.in section."""
    base_url = f"https://gstcouncil.gov.in/{url_path}"
    out_dir = os.path.join(BASE, out_folder)
    os.makedirs(out_dir, exist_ok=True)

    all_pdfs = []  # (url, filename)

    # Auto-detect max pages if not specified
    if max_pages is None:
        max_pages = 100  # safety cap

    print(f"\n{'='*60}")
    print(f"  {section_name}")
    print(f"  {base_url}")
    print(f"{'='*60}")

    for page_num in range(0, max_pages):
        url = f"{base_url}?page={page_num}" if page_num > 0 else base_url
        try:
            r = session.get(url, timeout=15)
            if r.status_code != 200:
                break
            soup = BeautifulSoup(r.text, 'html.parser')

            # Find all PDF links on this page
            pdf_links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.lower().endswith('.pdf'):
                    full_url = urljoin(base_url, href)
                    filename = sanitize(unquote(full_url.split('/')[-1]))
                    if not filename.endswith('.pdf'):
                        filename += '.pdf'
                    pdf_links.append((full_url, filename))

            if not pdf_links:
                # No PDFs found on this page — we've passed the last page
                break

            all_pdfs.extend(pdf_links)
            print(f"  Page {page_num}: {len(pdf_links)} PDFs found")

        except Exception as e:
            print(f"  Page {page_num}: ERROR - {e}")
            break

    # Deduplicate by URL
    seen = set()
    unique_pdfs = []
    for url, fname in all_pdfs:
        if url not in seen:
            seen.add(url)
            unique_pdfs.append((url, fname))

    print(f"  Total unique PDFs: {len(unique_pdfs)}")

    # Download with concurrency
    success = 0
    def dl(item):
        url, fname = item
        return download_file(session, url, os.path.join(out_dir, fname))

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(dl, item) for item in unique_pdfs]
        for future in tqdm(as_completed(futures), total=len(unique_pdfs), desc=f"  Downloading {section_name}", leave=True):
            if future.result():
                success += 1

    print(f"  Downloaded: {success}/{len(unique_pdfs)}")
    return success

# ─── GST ACTS from cbic-gst.gov.in ───────────────────────────────────────────
def scrape_gst_acts(session):
    print(f"\n{'='*60}")
    print(f"  GST Acts (cbic-gst.gov.in)")
    print(f"{'='*60}")
    out_dir = os.path.join(BASE, "Acts")
    os.makedirs(out_dir, exist_ok=True)

    url = "https://cbic-gst.gov.in/gst-acts.html"
    try:
        r = session.get(url, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        pdfs = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.lower().endswith('.pdf'):
                full_url = urljoin(url, href)
                fname = sanitize(unquote(full_url.split('/')[-1]))
                pdfs.append((full_url, fname))

        seen = set()
        unique = [(u, f) for u, f in pdfs if u not in seen and not seen.add(u)]
        print(f"  Found {len(unique)} Act PDFs")

        success = 0
        for pdf_url, fname in tqdm(unique, desc="  Downloading Acts"):
            if download_file(session, pdf_url, os.path.join(out_dir, fname)):
                success += 1
        print(f"  Downloaded: {success}/{len(unique)}")
    except Exception as e:
        print(f"  ERROR: {e}")

# ─── GST COUNCIL MEETING MINUTES ─────────────────────────────────────────────
def download_meeting_minutes(session):
    print(f"\n{'='*60}")
    print(f"  GST Council Meeting Minutes (1st–51st)")
    print(f"{'='*60}")
    out_dir = os.path.join(BASE, "Council_Meetings", "Minutes")
    os.makedirs(out_dir, exist_ok=True)

    success = 0
    for meeting, url in tqdm(MINUTES.items(), desc="  Downloading Minutes"):
        fname = f"Minutes_{meeting}_GSTCM.pdf"
        if download_file(session, url, os.path.join(out_dir, fname)):
            success += 1
    print(f"  Downloaded: {success}/{len(MINUTES)}")

# ─── GST COUNCIL MEETING AGENDA (scraped from meetings page) ─────────────────
def download_meeting_agendas(session):
    print(f"\n{'='*60}")
    print(f"  GST Council Meeting Agendas")
    print(f"{'='*60}")
    out_dir = os.path.join(BASE, "Council_Meetings", "Agendas")
    os.makedirs(out_dir, exist_ok=True)

    url = "https://gstcouncil.gov.in/gst-council-meetings"
    try:
        r = session.get(url, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        pdfs = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.lower().endswith('.pdf') and 'agenda' in href.lower():
                full_url = urljoin(url, href)
                fname = sanitize(unquote(full_url.split('/')[-1]))
                pdfs.append((full_url, fname))

        seen = set()
        unique = [(u, f) for u, f in pdfs if u not in seen and not seen.add(u)]
        print(f"  Found {len(unique)} Agenda PDFs")

        success = 0
        for pdf_url, fname in tqdm(unique, desc="  Downloading Agendas"):
            if download_file(session, pdf_url, os.path.join(out_dir, fname)):
                success += 1
        print(f"  Downloaded: {success}/{len(unique)}")
    except Exception as e:
        print(f"  ERROR: {e}")

# ─── ARCHIVE / FOUNDATIONAL DOCUMENTS ────────────────────────────────────────
def download_archive_docs(session):
    print(f"\n{'='*60}")
    print(f"  Archive / Foundational Documents")
    print(f"{'='*60}")
    out_dir = os.path.join(BASE, "Archive")
    os.makedirs(out_dir, exist_ok=True)

    success = 0
    for fname, url in ARCHIVE_DOCS.items():
        if download_file(session, url, os.path.join(out_dir, fname)):
            success += 1
            print(f"  OK   {fname}")
        else:
            print(f"  FAIL {fname}")
    print(f"  Downloaded: {success}/{len(ARCHIVE_DOCS)}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(BASE, exist_ok=True)
    state = load_state()
    session = get_session()
    total_downloaded = 0

    print("=" * 60)
    print("  GST COMPLETE DOCUMENT SCRAPER -- ArthLLM")
    print("  gstcouncil.gov.in + cbic-gst.gov.in")
    print("=" * 60)

    # 1. GST Acts
    if "Acts" not in state["completed_sections"]:
        scrape_gst_acts(session)
        state["completed_sections"].append("Acts")
        save_state(state)

    # 2. All paginated sections from gstcouncil.gov.in
    for section_name, (url_path, max_pages, subfolder) in SECTIONS.items():
        if section_name in state["completed_sections"]:
            print(f"\n  SKIP {section_name} (already done)")
            continue
        n = scrape_paginated_section(session, section_name, url_path, max_pages, subfolder)
        total_downloaded += n
        state["completed_sections"].append(section_name)
        save_state(state)

    # 3. Council Meeting Minutes
    if "Meeting_Minutes" not in state["completed_sections"]:
        download_meeting_minutes(session)
        state["completed_sections"].append("Meeting_Minutes")
        save_state(state)

    # 4. Council Meeting Agendas
    if "Meeting_Agendas" not in state["completed_sections"]:
        download_meeting_agendas(session)
        state["completed_sections"].append("Meeting_Agendas")
        save_state(state)

    # 5. Archive docs
    if "Archive" not in state["completed_sections"]:
        download_archive_docs(session)
        state["completed_sections"].append("Archive")
        save_state(state)

    print(f"\n{'='*60}")
    print(f"  ALL DONE! Files saved to: {BASE}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
