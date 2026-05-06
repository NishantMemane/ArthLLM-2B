"""Fix: Test downloading RBI PDFs with proper Referer and session."""
import requests
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
})

# Test 1: Direct hit (fails — returns HTML)
url = "https://rbidocs.rbi.org.in/rdocs/notification/PDFs/AFEMA6R23022026D704451E2ED6439B8F8FAEEF5A4D0929.PDF"
print("=== Test 1: Direct (no session) ===")
r = requests.get(url, headers=s.headers, verify=False, timeout=30)
print(f"  Status: {r.status_code}, Type: {r.headers.get('Content-Type')}, Size: {len(r.content)}, PDF: {r.content[:4] == b'%PDF'}")

# Test 2: First visit the parent page, then download (session with cookies)
print("\n=== Test 2: Visit parent page first, then download ===")
parent = "https://www.rbi.org.in/Scripts/BS_FemaNotifications.aspx"
s.get(parent, timeout=30)
r2 = s.get(url, timeout=30, headers={"Referer": parent})
print(f"  Status: {r2.status_code}, Type: {r2.headers.get('Content-Type')}, Size: {len(r2.content)}, PDF: {r2.content[:4] == b'%PDF'}")

# Test 3: Visit the rbi.org.in homepage first to get cookies
print("\n=== Test 3: Visit rbi.org.in homepage first ===")
s2 = requests.Session()
s2.verify = False
s2.headers.update(s.headers)
s2.get("https://www.rbi.org.in", timeout=30)
r3 = s2.get(url, timeout=30)
print(f"  Status: {r3.status_code}, Type: {r3.headers.get('Content-Type')}, Size: {len(r3.content)}, PDF: {r3.content[:4] == b'%PDF'}")
print(f"  Cookies: {dict(s2.cookies)}")

# Test 4: Try with allow_redirects=False to see what's happening
print("\n=== Test 4: Check redirect chain ===")
r4 = requests.get(url, verify=False, headers=s.headers, allow_redirects=False, timeout=30)
print(f"  Status: {r4.status_code}, Location: {r4.headers.get('Location', 'none')}")

# Test 5: Try http:// instead of https://
print("\n=== Test 5: Try HTTP instead of HTTPS ===")
http_url = url.replace("https://", "http://")
r5 = requests.get(http_url, headers=s.headers, timeout=30, allow_redirects=True)
print(f"  Status: {r5.status_code}, Type: {r5.headers.get('Content-Type')}, Size: {len(r5.content)}, PDF: {r5.content[:4] == b'%PDF'}")
print(f"  Final URL: {r5.url[:100]}")

# Test 6: A known working FSR PDF from our earlier test
print("\n=== Test 6: The PDF that worked in the browser ===")
fsr_url = "https://rbidocs.rbi.org.in/rdocs//PublicationReport/Pdfs/0OVERVIEW0BD3010564F745549BF832CF2B7722F3.PDF"
r6 = s2.get(fsr_url, timeout=30)
print(f"  Status: {r6.status_code}, Type: {r6.headers.get('Content-Type')}, Size: {len(r6.content)}, PDF: {r6.content[:4] == b'%PDF'}")
