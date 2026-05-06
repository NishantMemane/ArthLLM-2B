import requests
import re
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_api(page_url, api_url):
    session = requests.Session()
    session.verify = False
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    
    resp1 = session.get(page_url)
    m = re.search(r'name="csrf-token" content="(.*?)"', resp1.text)
    if not m:
        m = re.search(r'name:"_token", value:"(.*?)"', resp1.text)
    token = m.group(1)
    
    print("Token:", token)
    
    headers = {
        'X-CSRF-TOKEN': token,
        'X-Requested-With': 'XMLHttpRequest'
    }
    data = {
        'draw': 1,
        'start': 0,
        'length': 10,
        '_token': token
    }
    
    resp2 = session.post(api_url, data=data, headers=headers)
    print("Status:", resp2.status_code)
    try:
        import json
        import html
        j = resp2.json()
        item = j['data'][0]
        raw_files = item['file_content']
        decoded = html.unescape(raw_files)
        files = json.loads(decoded)
        print("First item files:", files)
    except Exception as e:
        print("Error parsing json:", e)

test_api('https://www.cci.gov.in/combination/orders-section31', 'https://www.cci.gov.in/combination/orders-section31/list')
