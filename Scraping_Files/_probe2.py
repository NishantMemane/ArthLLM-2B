"""Probe 2: dig deeper into FEMA and GST."""
import urllib.request, re, ssl

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def fetch(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30, context=ctx)
        return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        return f"ERROR: {e}"

# 1. FEMA — dig into the notification listing links
print("=== FEMA: Follow the listing links ===")
html = fetch("https://www.rbi.org.in/Scripts/BS_FemaNotifications.aspx")
# Find all PDF links directly on the page
pdfs = re.findall(r'href="([^"]*\.pdf)"', html, re.I)
print(f"Direct PDFs on FEMA main page: {len(pdfs)}")
for p in pdfs[:10]:
    print(f"  {p}")

# Find year links or notification detail links
detail_links = re.findall(r'href="((?:NotificationUser|Fema|BS_viewfema)[^"]*)"', html)
print(f"\nDetail/sub-page links: {len(detail_links)}")
for l in detail_links[:10]:
    print(f"  {l}")

# Try a Fema.aspx link
print("\n=== FEMA: Try Fema.aspx sub-page ===")
fema_sub = fetch("https://www.rbi.org.in/Scripts/Fema.aspx")
if not fema_sub.startswith("ERROR"):
    sub_pdfs = re.findall(r'href="([^"]*\.pdf)"', fema_sub, re.I)
    sub_notifs = re.findall(r'href="(NotificationUser[^"]*)"', fema_sub)
    print(f"  PDFs: {len(sub_pdfs)}, Notification links: {len(sub_notifs)}")
    for p in sub_pdfs[:5]:
        print(f"    {p}")
else:
    print(f"  {fema_sub}")

# 2. GST Council — try with SSL bypass and correct URLs
print("\n=== GST Council: Try with SSL bypass ===")
for path in ["press-releases", "notifications", "circulars",
             "gst-council-meeting-agenda-and-minutes", "gst-act-rules-and-rates"]:
    url = f"https://gstcouncil.gov.in/{path}"
    html = fetch(url)
    if html.startswith("ERROR"):
        print(f"  {path}: {html[:80]}")
    else:
        pdf_links = re.findall(r'href="([^"]*\.pdf)"', html, re.I)
        pages = sorted(set(re.findall(r'page=(\d+)', html)))
        print(f"  {path}: {len(pdf_links)} PDFs, pages: {pages}")
        for p in pdf_links[:3]:
            print(f"    {p}")

# 3. CBDT — try with SSL bypass
print("\n=== CBDT: Try with SSL bypass ===")
for path in ["Pages/communications/circulars.aspx",
             "Pages/communications/notifications.aspx",
             "Pages/acts/income-tax-act.aspx"]:
    url = f"https://incometaxindia.gov.in/{path}"
    html = fetch(url)
    if html.startswith("ERROR"):
        print(f"  {path}: {html[:80]}")
    else:
        pdf_links = re.findall(r'href="([^"]*\.pdf)"', html, re.I)
        print(f"  {path}: {len(pdf_links)} PDFs, page size: {len(html)} chars")
