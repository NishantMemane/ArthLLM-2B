import requests
import re
import urllib3
urllib3.disable_warnings()
from bs4 import BeautifulSoup

s = requests.Session()
s.verify = False

# Search for FEMA
r = s.get("https://www.indiacode.nic.in/simple-search?query=Foreign+Exchange+Management+Act")
soup = BeautifulSoup(r.text, 'html.parser')
for a in soup.find_all('a', href=True):
    if '/handle/' in a['href'] and 'Foreign Exchange Management Act' in a.text:
        print(f"FEMA Handle: {a['href']}")
        
# Get the PDF for FEMA
r2 = s.get("https://www.indiacode.nic.in" + a['href'])
pdfs = re.findall(r'href="([^"]*bitstream[^"]*\.pdf)"', r2.text, re.I)
print(f"FEMA PDFs: {pdfs}")
