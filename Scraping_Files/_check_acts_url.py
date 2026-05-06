import requests
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": "Mozilla/5.0"})

urls_to_try = [
    "https://www.incometaxindia.gov.in/acts",
    "https://www.incometaxindia.gov.in/income-tax-act",
    "https://www.incometaxindia.gov.in/rules",
]

for url in urls_to_try:
    r = s.get(url, timeout=10)
    print(f"{url} -> {r.status_code}")
