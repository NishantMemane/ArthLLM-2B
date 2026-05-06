import requests
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

urls = [
    'https://www.indiacode.nic.in/bitstream/123456789/2435/1/a1961-43.pdf',
    'https://www.indiacode.nic.in/bitstream/123456789/2398/1/a1934-2.pdf',
    'https://www.indiacode.nic.in/bitstream/123456789/15689/5/a2017-12.pdf',
    'https://www.indiacode.nic.in/bitstream/123456789/2251/1/A201713.pdf',
    'https://www.indiacode.nic.in/bitstream/123456789/17290/1/A1999-42.pdf',
    'https://www.indiacode.nic.in/bitstream/123456789/1999/1/A1999-42.pdf',
]

for url in urls:
    try:
        r = s.get(url, timeout=5, allow_redirects=True, stream=True)
        pdf = r.raw.read(10)[:4] == b'%PDF'
        print(f'{r.status_code} | PDF: {pdf} | {url}')
    except Exception as e:
        print(f'Error: {e}')
