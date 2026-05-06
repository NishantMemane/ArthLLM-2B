import requests
from bs4 import BeautifulSoup
import re
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False

def find_pdf_for_act(act_name, search_url=None):
    if not search_url:
        search_url = f"https://www.indiacode.nic.in/simple-search?query={act_name.replace(' ', '+')}"
    
    r = s.get(search_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    for a in soup.find_all('a', href=True):
        if '/handle/123456789/' in a['href'] and act_name.lower() in a.text.lower():
            handle_url = "https://www.indiacode.nic.in" + a['href']
            r2 = s.get(handle_url)
            pdfs = re.findall(r'href="([^"]*bitstream[^"]*\.pdf)"', r2.text, re.I)
            if pdfs:
                return "https://www.indiacode.nic.in" + pdfs[0]
    return None

print("Income Tax Act:", find_pdf_for_act("Income-tax Act, 1961"))
print("RBI Act:", find_pdf_for_act("Reserve Bank of India Act"))
print("CGST Act:", find_pdf_for_act("Central Goods and Services Tax Act"))
print("IGST Act:", find_pdf_for_act("Integrated Goods and Services Tax Act"))
print("FEMA:", find_pdf_for_act("Foreign Exchange Management Act"))

