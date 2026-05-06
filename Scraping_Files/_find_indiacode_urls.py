import requests
import re
import urllib3
urllib3.disable_warnings()
from concurrent.futures import ThreadPoolExecutor

s = requests.Session()
s.verify = False
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
})

targets = {
    "fema": "Foreign Exchange Management",
    "cgst": "Central Goods and Services Tax",
    "igst": "Integrated Goods and Services Tax",
    "rbi": "Reserve Bank of India"
}

found = {}

def check(hid):
    url = f"https://www.indiacode.nic.in/handle/123456789/{hid}"
    try:
        r = s.get(url, timeout=5)
        if r.status_code == 200:
            for k, v in targets.items():
                if v.lower() in r.text.lower() and "act" in r.text.lower():
                    pdfs = re.findall(r'href="(/bitstream/[^"]*\.pdf)"', r.text, re.I)
                    if pdfs:
                        found[k] = "https://www.indiacode.nic.in" + pdfs[0]
                        print(f"FOUND {k}: {found[k]}")
    except:
        pass

# I already know roughly where they are from my previous brute force
# CGST is 15689
# IGST is 2251
# RBI is 2398
# Income Tax is 2435
# Let's verify them and find FEMA!

for i in [15689, 2251, 2398]:
    check(i)

# For FEMA, let's scan a wider range
print("Scanning for FEMA...")
with ThreadPoolExecutor(max_workers=50) as ex:
    for i in range(1600, 2600):
        if "fema" not in found:
            ex.submit(check, i)

    for i in range(15000, 16000):
        if "fema" not in found:
            ex.submit(check, i)
