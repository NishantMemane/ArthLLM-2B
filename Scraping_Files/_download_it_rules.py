import requests
import os
import urllib3
urllib3.disable_warnings()

out_dir = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\IncomeTax\Income_Tax_Act"
os.makedirs(out_dir, exist_ok=True)

files = {
    "IT_Rules_1962_Part-A.pdf": "https://thc.nic.in/Central%20Governmental%20Rules/Income%20Tax%20Rules,1962(Part-A).pdf",
    "IT_Rules_1962_Part-B.pdf": "https://thc.nic.in/Central%20Governmental%20Rules/Income-Tax%20Rules,1962%20(Part-B).pdf",
    "IT_Rules_1962_Part-C_upto_16th_Amendment.pdf": "https://thc.nic.in/Central%20Governmental%20Rules/Income-Tax%20Rules,1962%20(Part-C)%20-Amendments%20upto%2016th%20Amendments.pdf",
    "IT_Rules_1962_Part-C_upto_19th_Amendment_07-07-2021.pdf": "https://thc.nic.in/Central%20Governmental%20Rules/Income-tax%20Rules,1962%20(Part-C)%20upto%2019th%20Amendment%20dt.07.07.2021.pdf",
    "IT_Rules_1962_Part-C_upto_31st_Amendment_01-10-2021.pdf": "https://thc.nic.in/Central%20Governmental%20Rules/Income-tax%20Rules,1962%20(Part-C)%20upto%2031st%20%20Amendment%20dt.01.10.2021.pdf",
    "IT_Rules_1962_Part-C_upto_33rd_Amendment_10-12-2021.pdf": "https://thc.nic.in/Central%20Governmental%20Rules/Income-Tax%20Rules,1962%20(Part-C)%20upto%2033rd%20%20%20Amendment%20dt.10.12.2021..pdf",
    "IT_Rules_1962_Part-C_upto_35th_Amendment_29-12-2021.pdf": "https://thc.nic.in/Central%20Governmental%20Rules/Income-Tax%20Rules,1962%20(Part-C)%20upto%2035th%20%20%20Amendment%20dt.29.12.2021..pdf",
    "IT_Rules_1962_All_Amendments_2022.pdf": "https://thc.nic.in/Central%20Governmental%20Rules/Income-Tax%20Rules,1962(%20All%20Amendments%20of%202022).pdf",
    "IT_Rules_1962_All_Amendments_2023.pdf": "https://thc.nic.in/Central%20Governmental%20Rules/Income-Tax%20Rules,1962(%20All%20Amendments%20of%202023).pdf",
    "IT_Rules_1962_All_Amendments_2024.pdf": "https://www.thc.nic.in/Central%20Governmental%20Rules/Income%20Tax%20Rules,1962(All%20Amendmnets%20of%202024).pdf",
    "IT_Rules_1962_All_Amendments_upto_2025.pdf": "https://thc.nic.in/Central%20Governmental%20Rules/Income%20Tax%20Rules,1962(All%20Amendmnets%20upto%202025).pdf",
}

s = requests.Session()
s.verify = False
s.headers.update({"User-Agent": "Mozilla/5.0"})

for filename, url in files.items():
    out_path = os.path.join(out_dir, filename)
    if os.path.exists(out_path):
        print(f"  SKIP {filename} (exists)")
        continue
    try:
        r = s.get(url, timeout=30, stream=True)
        if r.status_code == 200:
            size = 0
            with open(out_path, 'wb') as f:
                for chunk in r.iter_content(1024 * 1024):
                    f.write(chunk)
                    size += len(chunk)
            print(f"  OK   {filename} ({size/1024:.0f} KB)")
        else:
            print(f"  FAIL {filename} -> HTTP {r.status_code}")
    except Exception as e:
        print(f"  ERR  {filename} -> {e}")

print("\nDone!")
