import requests
import re
import urllib3
urllib3.disable_warnings()
from concurrent.futures import ThreadPoolExecutor

s = requests.Session()
s.verify = False

def search_fema(i):
    url = f"https://www.indiacode.nic.in/handle/123456789/{i}"
    try:
        r = s.get(url, timeout=5)
        if "Foreign Exchange Management Act" in r.text:
            print(f"FOUND FEMA at handle {i}")
    except:
        pass

with ThreadPoolExecutor(max_workers=50) as ex:
    # Just check a range of typical IDs around the ones we found
    for i in range(1500, 3000):
        ex.submit(search_fema, i)
