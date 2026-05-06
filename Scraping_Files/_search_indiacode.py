import requests
import re
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

def search_act(query):
    url = f"https://www.indiacode.nic.in/simple-search?query={query.replace(' ', '+')}"
    r = s.get(url)
    handles = re.findall(r'<a href="(/handle/123456789/\d+)">([^<]+)</a>', r.text)
    print(f"Query: {query}")
    for h, title in handles[:3]:
        print(f"  {h} -> {title.strip()}")
        # Get the actual PDF link
        r2 = s.get("https://www.indiacode.nic.in" + h)
        pdfs = re.findall(r'href="([^"]*bitstream[^"]*\.pdf)"', r2.text, re.I)
        print(f"    PDFs: {pdfs}")

search_act("Foreign Exchange Management Act")
search_act("Central Goods and Services Tax Act")
search_act("Reserve Bank of India Act")
search_act("Income-tax Act")
