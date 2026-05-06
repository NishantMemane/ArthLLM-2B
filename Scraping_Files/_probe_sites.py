"""Quick probe of all 5 target sites to understand their structure."""
import urllib.request
import re
import json

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def fetch(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30)
        return r.read().decode('utf-8', errors='replace')
    except Exception as e:
        return f"ERROR: {e}"

print("=" * 70)
print("PROBE 1: RBI FEMA Notifications")
print("=" * 70)
html = fetch("https://www.rbi.org.in/Scripts/BS_FemaNotifications.aspx")
# Check if it's a treeview/dropdown based page
tree_nodes = re.findall(r'TreeView.*?href="(.*?)"', html)
all_links = re.findall(r'href="([^"]*)"', html)
fema_links = [l for l in all_links if 'notification' in l.lower() or 'fema' in l.lower()]
print(f"  Total links: {len(all_links)}")
print(f"  FEMA/notification links: {len(fema_links)}")
print(f"  Tree nodes: {len(tree_nodes)}")
for l in fema_links[:10]:
    print(f"    {l}")

# Check if it uses postback (ASP.NET)
postbacks = re.findall(r"__doPostBack\('([^']*)'", html)
print(f"  PostBack targets: {len(postbacks)}")
for p in postbacks[:10]:
    print(f"    {p}")

print()
print("=" * 70)
print("PROBE 2: CBDT - incometaxindia.gov.in")
print("=" * 70)
html = fetch("https://incometaxindia.gov.in/Pages/communications/circulars.aspx")
if html.startswith("ERROR"):
    print(f"  {html}")
else:
    pdf_links = re.findall(r'href="([^"]*\.pdf)"', html, re.I)
    all_links = re.findall(r'href="([^"]*)"', html)
    print(f"  Total links: {len(all_links)}")
    print(f"  PDF links: {len(pdf_links)}")
    for l in pdf_links[:10]:
        print(f"    {l}")
    # Check for SharePoint REST API patterns
    sp_patterns = re.findall(r'_api/|_layouts|/_catalogs|ListData\.svc', html)
    print(f"  SharePoint API calls: {len(sp_patterns)}")
    # Check for iframe
    iframes = re.findall(r'<iframe[^>]*src="([^"]*)"', html, re.I)
    print(f"  Iframes: {iframes}")

print()
print("=" * 70)
print("PROBE 3: GST Council")
print("=" * 70)
for section in ["notifications", "circulars", "press-releases"]:
    url = f"https://gstcouncil.gov.in/{section}"
    html = fetch(url)
    if html.startswith("ERROR"):
        print(f"  {section}: {html}")
        continue
    pdf_links = re.findall(r'href="([^"]*\.pdf)"', html, re.I)
    print(f"  {section}: {len(pdf_links)} PDFs")
    # Check pagination
    pages = re.findall(r'page=(\d+)', html)
    print(f"    Pagination pages found: {sorted(set(pages)) if pages else 'none'}")

print()
print("=" * 70)
print("PROBE 4: RBI FSR - check known working IDs")
print("=" * 70)
# We know ID 1194 works. Check a few more.
for test_id in [1194, 1195, 1196, 1250, 1300]:
    url = f"https://www.rbi.org.in/Scripts/PublicationReportDetails.aspx?ID={test_id}"
    html = fetch(url)
    has_fsr = "financial stability" in html.lower()
    pdfs = re.findall(r'href=["\']([^"\']*\.pdf)["\']', html, re.I)
    rbi_pdfs = [p for p in pdfs if 'rbidocs' in p.lower()]
    print(f"  ID {test_id}: FSR={'YES' if has_fsr else 'no'}, rbidocs PDFs={len(rbi_pdfs)}")

print()
print("=" * 70)
print("PROBE 5: Income Tax Act direct PDF URLs")
print("=" * 70)
test_urls = [
    "https://incometaxindia.gov.in/Acts/Income-tax%20Act,%201961/2025/102120000000221498.htm",
    "https://incometaxindia.gov.in/Pages/acts/income-tax-act.aspx",
]
for u in test_urls:
    html = fetch(u)
    if html.startswith("ERROR"):
        print(f"  {u[:60]}... ERROR")
    else:
        pdf_links = re.findall(r'href="([^"]*\.pdf)"', html, re.I)
        htm_links = [l for l in re.findall(r'href="([^"]*)"', html) if 'Acts/' in l or 'act' in l.lower()]
        print(f"  {u[:60]}...")
        print(f"    PDFs: {len(pdf_links)}, Act-related links: {len(htm_links)}")
        for l in htm_links[:5]:
            print(f"      {l}")
