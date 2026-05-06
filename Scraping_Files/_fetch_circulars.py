from curl_cffi import requests
import re

url = "https://www.incometaxindia.gov.in/circulars"
print(f"Fetching {url} with curl_cffi...")

r = requests.get(url, impersonate="chrome110")
print(f"Status: {r.status_code}")
print(f"Content Length: {len(r.text)}")

# Look for Circular No
circulars = re.findall(r'Circular No[^<]+', r.text)
print(f"Found 'Circular No' {len(circulars)} times in HTML.")
if circulars:
    for c in circulars[:10]:
        print(f"  {c.strip()}")

# Look for Liferay data objects
data = re.findall(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});', r.text)
if data:
    print(f"Found INITIAL_STATE of length {len(data[0])}")
else:
    print("No INITIAL_STATE found.")
    
# Save raw HTML
with open("raw_circulars.html", "w", encoding="utf-8") as f:
    f.write(r.text)
