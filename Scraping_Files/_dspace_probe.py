import requests
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False

def search(query):
    print(f"\n=== Search: {query} ===")
    url = f"https://www.indiacode.nic.in/rest/items/find-by-metadata-field"
    payload = {
        "key": "dc.title",
        "value": query,
        "language": ""
    }
    r = s.post(url, json=payload, headers={"Accept": "application/json"})
    if r.status_code == 200:
        items = r.json()
        for item in items[:3]:
            print(f"  ID: {item['id']}")
            print(f"  Name: {item['name']}")
            print(f"  Handle: {item['handle']}")
            
            # Now fetch the bitstreams for this item
            b_url = f"https://www.indiacode.nic.in/rest/items/{item['id']}/bitstreams"
            br = s.get(b_url, headers={"Accept": "application/json"})
            if br.status_code == 200:
                bitstreams = br.json()
                for b in bitstreams:
                    if b['format'] == 'Adobe PDF':
                        print(f"    PDF: https://www.indiacode.nic.in{b['retrieveLink']}")
            
    else:
        print(f"  Failed: {r.status_code} - {r.text[:100]}")

search("Foreign Exchange Management Act")
search("Central Goods and Services Tax Act")
search("Reserve Bank of India Act")
search("Income-tax Act")
search("Integrated Goods and Services Tax Act")
