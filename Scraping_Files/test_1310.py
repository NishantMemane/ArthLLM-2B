import urllib.request
import re

url = "https://www.rbi.org.in/Scripts/PublicationReportDetails.aspx?ID=1310"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36"}
req = urllib.request.Request(url, headers=headers)
html = urllib.request.urlopen(req).read().decode()

print(html[:500])
print("\nPDFs:")
pdfs = re.findall(r'href="(.*?\.pdf)"', html, re.I)
for p in pdfs:
    print(p)
    
if "financial stability" in html.lower():
    print("Has 'financial stability'")
else:
    print("NO 'financial stability'")
