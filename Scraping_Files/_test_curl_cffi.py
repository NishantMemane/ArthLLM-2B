from curl_cffi import requests

print("Testing curl_cffi to bypass Akamai WAF...")
url = "https://www.indiacode.nic.in/bitstream/123456789/2435/1/a1961-43.pdf"

try:
    r = requests.get(url, impersonate="chrome110", timeout=15)
    print(f"Status: {r.status_code}")
    print(f"Headers: {dict(r.headers)[:100]}")
    is_pdf = r.content[:4] == b"%PDF"
    print(f"Is PDF: {is_pdf}")
    print(f"Size: {len(r.content)}")
except Exception as e:
    print(f"Error: {e}")
