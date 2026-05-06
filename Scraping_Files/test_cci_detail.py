import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
html = requests.get('https://www.cci.gov.in/combination/order/details/summary/1742/0/orders-section31', verify=False).text
print("PDFs:")
pdfs = re.findall(r'[\'"]([^\'"]+\.pdf)[\'"]', html, re.I)
for p in pdfs:
    print(p)
