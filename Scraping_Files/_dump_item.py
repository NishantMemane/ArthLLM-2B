import requests
import json
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False

url = "https://www.incometaxindia.gov.in/o/search/v1.0/search?nestedFields=embedded&page=1&pageSize=1&restrictFields=embedded.actions%2Cembedded.creator"
payload = {
    "attributes": {
        "search.empty.search": True,
        "search.experiences.blueprint.external.reference.code": "CIRCULAR_NOTIFICATION_BP_ERC",
        "search.experiences.structure_id": "36050",
        "search.experiences.structure_key": "CIRCULAR_KEY"
    }
}
r = s.post(url, json=payload, headers={"Content-Type": "application/json"})
with open("cbdt_item_dump.json", "w") as f:
    json.dump(r.json(), f, indent=2)
print("Dumped 1 item to cbdt_item_dump.json")
