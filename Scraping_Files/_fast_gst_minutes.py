"""Fast 20-worker GST Council Meeting Minutes downloader. Resume-capable."""
import requests, os, concurrent.futures
from tqdm import tqdm
import urllib3
urllib3.disable_warnings()

out_dir = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\GST\Council_Meetings\Minutes"
os.makedirs(out_dir, exist_ok=True)

MB = "https://gstcouncil.gov.in/sites/default/files/Minutes/"
AB = "https://gstcouncil.gov.in/sites/default/files/Agenda/"

MINUTES = {
    "Minutes_01st_GSTCM.pdf": f"{MB}Signed-Minutes-1st-GST-Council-Meeting.pdf",
    "Minutes_02nd_GSTCM.pdf": f"{MB}Signed-Minutes-2nd-GST-Council-Meeting.pdf",
    "Minutes_03rd_GSTCM.pdf": f"{MB}Signed-Minutes-3rd-GST-Council-Meeting.pdf",
    "Minutes_04th_GSTCM.pdf": f"{MB}Signed-Minutes-4th-GST-Council-Meeting.pdf",
    "Minutes_05th_GSTCM.pdf": f"{MB}Signed-Minutes-5th-GST-Council-Meeting.pdf",
    "Minutes_06th_GSTCM.pdf": f"{MB}Signed-Minutes-6th-GST-Council-Meeting.pdf",
    "Minutes_07th_GSTCM.pdf": f"{MB}Signed-Minutes-7th-GST-Council-Meeting.pdf",
    "Minutes_08th_GSTCM.pdf": f"{MB}Signed-Minutes-8th-GST-Council-Meeting.pdf",
    "Minutes_09th_GSTCM.pdf": f"{MB}Signed-Minutes-9th-GST-Council-Meeting.pdf",
    "Minutes_10th_GSTCM.pdf": f"{MB}Signed-Minutes-10th-GST-Council-Meeting.pdf",
    "Minutes_11th_GSTCM.pdf": f"{MB}Signed-Minutes-11th-GST-Council-Meeting.pdf",
    "Minutes_12th_GSTCM.pdf": f"{MB}Signed-Minutes-12th-GST-Council-Meeting.pdf",
    "Minutes_13th_GSTCM.pdf": f"{MB}Signed-Minutes-13th-GST-Council-Meeting.pdf",
    "Minutes_14th_GSTCM.pdf": f"{MB}Signed-Minutes-14th-GST-Council-Meeting.pdf",
    "Minutes_15th_GSTCM.pdf": f"{MB}Signed-Minutes-15th-GST-Council-Meeting.pdf",
    "Minutes_16th_GSTCM.pdf": f"{MB}Signed-Minutes-16th-GST-Council-Meeting.pdf",
    "Minutes_17th_GSTCM.pdf": f"{MB}Signed-Minutes-17th-GST-Council-Meeting.pdf",
    "Minutes_18th_GSTCM.pdf": f"{MB}Signed-Minutes-18th-GST-Council-Meeting.pdf",
    "Minutes_19th_GSTCM.pdf": f"{MB}Signed_Minutes-19th_GST_Council_Meeting.pdf",
    "Minutes_20th_GSTCM.pdf": f"{MB}Signed-Minutes-20th-GST-Council-Meeting.pdf",
    "Minutes_21st_GSTCM.pdf": f"{MB}Signed-Minutes-21st-GST-Council-Meeting.pdf",
    "Minutes_22nd_GSTCM.pdf": f"{MB}Signed-Minutes-22nd-GST-Council-Meeting.pdf",
    "Minutes_23rd_GSTCM.pdf": f"{MB}Signed-Minutes-23rd-GST-Council-Meeting.pdf",
    "Minutes_24th_GSTCM.pdf": f"{MB}Signed-Minutes-24th-GST-Council-Meeting.pdf",
    "Minutes_25th_GSTCM.pdf": f"{MB}Signed-Minutes-25th-GST-Council-Meeting.pdf",
    "Minutes_26th_GSTCM.pdf": f"{MB}Signed-Minutes-26th-GST-Council-Meeting.pdf",
    "Minutes_27th_GSTCM.pdf": f"{MB}Signed-Minutes-27th-GST-Council-Meeting.pdf",
    "Minutes_28th_GSTCM.pdf": f"{MB}Signed-Minutes-28th-GST-Council-Meeting.pdf",
    "Minutes_29th_GSTCM.pdf": f"{MB}Signed-Minutes-29th-GST-Council-Meeting.pdf",
    "Minutes_30th_GSTCM.pdf": f"{MB}Signed-Minutes-30th-GST-Council-Meeting.pdf",
    "Minutes_31st_GSTCM.pdf": f"{MB}Signed-Minutes-31st-GST-Council-Meeting.pdf",
    "Minutes_32nd_GSTCM.pdf": f"{MB}Signed-Minutes-32nd-GST-Council-Meeting.pdf",
    "Minutes_33rd_GSTCM.pdf": f"{MB}Signed-Minutes-33rd-GST-Council-Meeting.pdf",
    "Minutes_34th_GSTCM.pdf": f"{MB}Signed_Minutes-34th_GST_Council_Meeting.pdf",
    "Minutes_35th_GSTCM.pdf": f"{AB}Signed-Minutes-35th-GST-Council-Meeting.pdf",
    "Minutes_36th_GSTCM.pdf": f"{MB}Signed-Minutes-36th-GST-Council-Meeting.pdf",
    "Minutes_37th_GSTCM.pdf": f"{MB}Signed-Minutes-37th-GST-Council-Meeting.pdf",
    "Minutes_38th_GSTCM.pdf": f"{MB}Signed_Minutes_38th_GST_Council_Meeting.pdf",
    "Minutes_39th_GSTCM.pdf": f"{MB}Signed-Minutes-39th-GSTCM.pdf",
    "Minutes_40th_GSTCM.pdf": f"{MB}Minutes-40th-GSTC-Meeting.pdf",
    "Minutes_41st_GSTCM.pdf": f"{MB}Minutes-%2041st-GSTC-Meeting.pdf",
    "Minutes_42nd_GSTCM.pdf": f"{MB}42nd-GSTC-Minutes-Signed.pdf",
    "Minutes_43rd_GSTCM.pdf": f"{MB}Minutes_of_43rd_GSTCM.pdf",
    "Minutes_44th_GSTCM.pdf": f"{MB}Minutes_of_44th_GSTCM.pdf",
    "Minutes_45th_GSTCM.pdf": f"{MB}45TH_MEETING.pdf",
    "Minutes_46th_GSTCM.pdf": f"{MB}46TH_MEETING_MINUTES.pdf",
    "Minutes_47th_GSTCM.pdf": f"{MB}47_MINUTES.pdf",
    "Minutes_48th_GSTCM.pdf": f"{MB}48THMINUTES.pdf",
    "Minutes_49th_GSTCM.pdf": f"{MB}49TH_MEETING_MINUTES.pdf",
    "Minutes_50th_GSTCM.pdf": f"{MB}Minutes_of_50th.pdf",
    "Minutes_51st_GSTCM.pdf": f"{MB}Minutes_of_51st.pdf",
}

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": "Mozilla/5.0"})

def dl(item):
    fname, url = item
    path = os.path.join(out_dir, fname)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return fname, "SKIP"
    try:
        r = s.get(url, timeout=30, stream=True)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in r.iter_content(1024*1024):
                    f.write(chunk)
            return fname, "OK"
        return fname, f"HTTP {r.status_code}"
    except Exception as e:
        return fname, str(e)

items = list(MINUTES.items())
skip = ok = fail = 0

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
    futures = [ex.submit(dl, item) for item in items]
    for f in tqdm(concurrent.futures.as_completed(futures), total=len(items), desc="Minutes"):
        fname, status = f.result()
        if status == "SKIP": skip += 1
        elif status == "OK": ok += 1
        else:
            fail += 1
            print(f"  FAIL {fname}: {status}")

print(f"\nDone! OK={ok} SKIP={skip} FAIL={fail}")
