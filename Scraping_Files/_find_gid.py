import requests, re
r = requests.get('https://www.incometaxindia.gov.in/circulars', verify=False)
matches = re.findall(r'(getCompanyId|getScopeGroupId|getUserId|getLayoutId|getPlid|getPathMain|getCDNBaseURL|getDefaultLanguageId)\s*:\s*function\s*\(\)\s*\{\s*return\s+["\']([^"\']*)', r.text)
for name, val in matches:
    print(f'{name}: {val}')

# Try the API with the correct groupId
for gid in ['20099', '20101', '20120', '37910']:
    url = f"https://www.incometaxindia.gov.in/o/headless-delivery/v1.0/sites/{gid}/structured-contents?page=1&pageSize=2&flatten=true"
    r2 = requests.get(url, verify=False, headers={"Accept": "application/json"})
    print(f"GroupId {gid}: {r2.status_code}")
    if r2.status_code == 200:
        data = r2.json()
        print(f"  TotalCount: {data.get('totalCount')}")
        break

# Try search API
for gid in ['20099', '20101', '20120', '37910']:
    url = f"https://www.incometaxindia.gov.in/o/search/v1.0/search/scopes/{gid}?page=1&pageSize=2&nestedFields=embedded"
    r3 = requests.get(url, verify=False, headers={"Accept": "application/json"})
    print(f"Search GroupId {gid}: {r3.status_code}")
    if r3.status_code == 200:
        data = r3.json()
        print(f"  TotalCount: {data.get('totalCount')}")
        if data.get('items'):
            print(f"  First: {data['items'][0].get('title', '?')[:80]}")
        break
