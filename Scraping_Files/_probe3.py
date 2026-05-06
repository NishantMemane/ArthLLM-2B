"""Probe 3: Find correct GST Council and CBDT URLs."""
import requests
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
s.verify = False

print("=== GST Council: Find correct URLs ===")
# Try the root
for url in [
    "https://gstcouncil.gov.in",
    "https://www.gstcouncil.gov.in",
    "https://gstcouncil.gov.in/press-releases",
    "https://gstcouncil.gov.in/press-release",
    "https://gstcouncil.gov.in/node",
]:
    try:
        r = s.get(url, timeout=15, allow_redirects=True)
        print(f"  {url} -> {r.status_code} (final: {r.url[:80]})")
    except Exception as e:
        print(f"  {url} -> ERROR: {e}")

print()
print("=== CBDT: Find correct URLs ===")
for url in [
    "https://incometaxindia.gov.in",
    "https://www.incometaxindia.gov.in",
    "https://incometaxindia.gov.in/pages/communications/circulars.aspx",
    "https://incometaxindia.gov.in/Pages/I-Am/individual.aspx",
]:
    try:
        r = s.get(url, timeout=15, allow_redirects=True)
        print(f"  {url} -> {r.status_code} (size: {len(r.text)}, final: {r.url[:80]})")
    except Exception as e:
        print(f"  {url} -> ERROR: {e}")

print()
print("=== RBI FEMA: Count all PDFs by scanning subpages ===")
import re
# The main page has 24 PDFs. Let's also check BS_viewfemanewnotification.aspx
for url in [
    "https://www.rbi.org.in/Scripts/BS_viewfemanewnotification.aspx",
    "https://www.rbi.org.in/Scripts/BS_FemaNotifications.aspx",
]:
    try:
        r = s.get(url, timeout=20)
        pdfs = re.findall(r'href="([^"]*\.pdf)"', r.text, re.I)
        rbi_pdfs = [p for p in pdfs if 'rbidocs' in p]
        print(f"  {url.split('/')[-1]}: {len(rbi_pdfs)} rbidocs PDFs")
    except Exception as e:
        print(f"  ERROR: {e}")
