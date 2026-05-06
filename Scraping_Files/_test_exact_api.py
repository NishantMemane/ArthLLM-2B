import requests
import json
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Content-Type": "application/json"
})

url = "https://www.incometaxindia.gov.in/o/search/v1.0/search?nestedFields=embedded&page=1&pageSize=10&restrictFields=embedded.actions%2Cembedded.creator"

print("Fetching Circulars...")
payload = {
    "attributes": {
        "search.empty.search": True,
        "search.experiences.blueprint.external.reference.code": "CIRCULAR_NOTIFICATION_BP_ERC",
        "search.experiences.structure_id": "36050",
        "search.experiences.structure_key": "CIRCULAR_KEY"
    }
}
r = s.post(url, json=payload, timeout=15)
if r.status_code == 200:
    data = r.json()
    items = data.get("items", [])
    print(f"Total Circulars: {data.get('totalCount')}") # wait, search api aggregations might not have totalCount, but let's check
    for item in items:
        # Extract title from contentFields
        title = ""
        url_val = ""
        fields = item.get("embedded", {}).get("contentFields", [])
        for f in fields:
            if f.get("name") == "circularNotificationNumber":
                title = f.get("contentFieldValue", {}).get("data", "")
            if f.get("name") == "documentFile":
                url_val = f.get("contentFieldValue", {}).get("document", {}).get("contentUrl", "")
        print(f"  {title} -> {url_val}")
else:
    print(f"Error: {r.status_code} - {r.text}")

print("\nFetching Notifications...")
payload_notif = {
    "attributes": {
        "search.empty.search": True,
        "search.experiences.blueprint.external.reference.code": "CIRCULAR_NOTIFICATION_BP_ERC",
        "search.experiences.structure_id": "36052", # Guessing ID? Wait, let's just use key
        "search.experiences.structure_key": "NOTIFICATION_KEY"
    }
}
r = s.post(url, json=payload_notif, timeout=15)
if r.status_code == 200:
    data = r.json()
    items = data.get("items", [])
    for item in items:
        title = ""
        url_val = ""
        fields = item.get("embedded", {}).get("contentFields", [])
        for f in fields:
            if f.get("name") == "circularNotificationNumber":
                title = f.get("contentFieldValue", {}).get("data", "")
            if f.get("name") == "documentFile":
                url_val = f.get("contentFieldValue", {}).get("document", {}).get("contentUrl", "")
        print(f"  {title} -> {url_val}")
else:
    print(f"Error: {r.status_code} - {r.text}")
