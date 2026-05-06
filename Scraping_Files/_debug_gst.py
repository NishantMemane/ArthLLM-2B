import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": "Mozilla/5.0"})

urls = [
    "https://gstcouncil.gov.in/cgst-tax-rate-notification",
    "https://gstcouncil.gov.in/igst-tax-notification",
    "https://gstcouncil.gov.in/utgst-tax-notification",
    "https://gstcouncil.gov.in/compensation-cess-notification",
]

for url in urls:
    print(f"\n{'='*60}")
    print(f"URL: {url}")
    r = s.get(url, timeout=15)
    print(f"Status: {r.status_code}")
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Find all links
    all_links = soup.find_all('a', href=True)
    pdf_links = [a for a in all_links if '.pdf' in a['href'].lower()]
    print(f"Total <a> tags: {len(all_links)}")
    print(f"PDF links: {len(pdf_links)}")
    
    # Show first 5 links with href to understand structure
    print("Sample links:")
    for a in all_links[:20]:
        href = a['href']
        text = a.get_text(strip=True)[:60]
        if text and '/sites/' in href or 'notification' in href.lower() or 'circular' in href.lower():
            print(f"  [{text}] -> {href}")
    
    # Check for any tables or views
    views = soup.find_all('div', class_=lambda c: c and 'view' in c.lower()) if True else []
    print(f"View divs: {len(views)}")
    
    # Save first page HTML for analysis
    slug = url.split('/')[-1]
    with open(f"gst_debug_{slug}.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    print(f"Saved HTML to gst_debug_{slug}.html")
