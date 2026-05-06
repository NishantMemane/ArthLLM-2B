import urllib.request
import urllib.parse
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_api(page_url, api_url):
    req = urllib.request.Request(page_url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req, context=ctx).read().decode()
    m = re.search(r'name="csrf-token" content="(.*?)"', html)
    if not m:
        m = re.search(r'name:"_token", value:"(.*?)"', html)
    token = m.group(1)
    
    data = urllib.parse.urlencode({'draw': 1, 'start': 0, 'length': 10, '_token': token}).encode()
    req2 = urllib.request.Request(api_url, data=data, headers={
        'User-Agent': 'Mozilla/5.0',
        'X-CSRF-TOKEN': token,
        'X-Requested-With': 'XMLHttpRequest'
    })
    
    resp = urllib.request.urlopen(req2, context=ctx).read().decode()
    print(resp[:500])

test_api('https://www.cci.gov.in/antitrust/orders', 'https://www.cci.gov.in/antitrust/orders/list')
