import urllib.request
import re

def test_id(i):
    url = f"https://www.rbi.org.in/Scripts/PublicationReportDetails.aspx?ID={i}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36"}
    req = urllib.request.Request(url, headers=headers)
    try:
        html = urllib.request.urlopen(req).read().decode()
    except Exception as e:
        return f"{i}: Error {e}"
        
    pdfs = re.findall(r'href="(https?://rbidocs\.rbi\.org\.in/rdocs//?PublicationReport/Pdfs/[^"]+\.(?:PDF|pdf))"', html, re.I)
    has_fsr = "financial stability" in html.lower()
    return f"{i}: FSR={has_fsr}, PDFs={len(pdfs)}"

for i in [750, 800, 850, 900, 1000, 1100, 1200, 1250, 1300]:
    print(test_id(i))
