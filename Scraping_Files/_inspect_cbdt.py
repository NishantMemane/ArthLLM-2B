import requests, json
import urllib3
urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
base = "https://www.incometaxindia.gov.in"
gid = "20117"

voc_url = f"{base}/o/headless-admin-taxonomy/v1.0/sites/{gid}/taxonomy-vocabularies?pageSize=-1"
r2 = s.get(voc_url, timeout=10)
vocs = r2.json().get("items", [])

with open("cbdt_cats.txt", "w", encoding="utf-8") as f:
    for voc in vocs:
        vname = voc.get('name')
        f.write(f"\nVocab: {vname} (ID: {voc.get('id')})\n")
        cat_url = f"{base}/o/headless-admin-taxonomy/v1.0/taxonomy-vocabularies/{voc['id']}/taxonomy-categories?pageSize=-1"
        try:
            r3 = s.get(cat_url, timeout=10)
            cats = r3.json().get("items", [])
            for cat in cats:
                f.write(f"  - {cat.get('name')} (ID: {cat.get('id')})\n")
        except Exception as e:
            f.write(f"  ERROR: {e}\n")
