"""Probe the /api/corporates-pit endpoint — the real insider trading API."""
import requests
import json
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

s = requests.Session()
s.headers.update(HEADERS)

# warm up via the insider trading page
print("=== Warm up ===")
r = s.get("https://www.nseindia.com/companies-listing/corporate-filings-insider-trading", timeout=15)
print(f"  Status: {r.status_code}, Cookies: {len(s.cookies)}")
time.sleep(1)

# PIT endpoint
print("\n=== /api/corporates-pit (no date params) ===")
r1 = s.get("https://www.nseindia.com/api/corporates-pit", timeout=60)
print(f"  Status: {r1.status_code}")
data1 = r1.json()
print(f"  Type: {type(data1).__name__}, Keys: {list(data1.keys())}")
if "data" in data1:
    d = data1["data"]
    print(f"  data: type={type(d).__name__}")
    if isinstance(d, list):
        print(f"    length: {len(d)}")
        if d:
            print(f"    First keys: {list(d[0].keys())}")
            print(f"    First record:\n{json.dumps(d[0], indent=2, ensure_ascii=False)}")
            if len(d) > 1:
                print(f"\n    Second record:\n{json.dumps(d[1], indent=2, ensure_ascii=False)}")
    elif isinstance(d, dict):
        print(f"    keys: {list(d.keys())}")
        for k, v in d.items():
            if isinstance(v, list):
                print(f"      {k}: list[{len(v)}]")
                if v:
                    print(f"        Sample: {json.dumps(v[0], indent=2, ensure_ascii=False)[:500]}")
            else:
                print(f"      {k}: {str(v)[:300]}")

if "acqNameList" in data1:
    anl = data1["acqNameList"]
    print(f"\n  acqNameList: {len(anl)} names")
    print(f"    First 5: {anl[:5]}")

# Try with date params
time.sleep(1)
print("\n\n=== /api/corporates-pit with dates ===")
for params in [
    {"from_date": "01-04-2026", "to_date": "01-05-2026"},
    {"index": "equities", "from_date": "01-04-2026", "to_date": "01-05-2026"},
    {"from_date": "01-04-2026", "to_date": "01-05-2026", "symbol": ""},
]:
    print(f"\n  Params: {params}")
    r2 = s.get("https://www.nseindia.com/api/corporates-pit", params=params, timeout=60)
    print(f"  Status: {r2.status_code}")
    if r2.status_code == 200:
        try:
            d2 = r2.json()
            if isinstance(d2, dict):
                print(f"  Keys: {list(d2.keys())}")
                if "data" in d2:
                    dd = d2["data"]
                    if isinstance(dd, list):
                        print(f"  data: list[{len(dd)}]")
                        if dd:
                            print(f"  Keys: {list(dd[0].keys())}")
                            print(f"  Sample:\n{json.dumps(dd[0], indent=2, ensure_ascii=False)[:600]}")
                    elif isinstance(dd, dict):
                        print(f"  data keys: {list(dd.keys())}")
            elif isinstance(d2, list):
                print(f"  list[{len(d2)}]")
                if d2:
                    print(f"  Keys: {list(d2[0].keys())}")
        except:
            print(f"  Text: {r2.text[:300]}")
    time.sleep(0.5)

# Also try the SAST/Takeover specific variations
time.sleep(1)
print("\n\n=== Checking SAST / Takeover endpoints ===")
for ep in [
    "https://www.nseindia.com/api/corporates-pit?from_date=01-01-2025&to_date=31-03-2025",
]:
    r3 = s.get(ep, timeout=30)
    print(f"  {ep.split('?')[0].split('/')[-1]} → {r3.status_code}, len={len(r3.text)}")
    if r3.status_code == 200:
        try:
            d3 = r3.json()
            if isinstance(d3, dict) and "data" in d3:
                dd = d3["data"]
                if isinstance(dd, list):
                    print(f"    data: list[{len(dd)}]")
        except:
            pass

print("\nDone.")
