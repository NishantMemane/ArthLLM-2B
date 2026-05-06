import os

base_dir = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian"

print(f"{'Directory':<60} | {'PDF Count':>10}")
print("-" * 75)

for root, dirs, files in os.walk(base_dir):
    pdf_count = sum(1 for f in files if f.lower().endswith(".pdf"))
    if pdf_count > 0 or "other_regulators" in root or "sebi" in root or "cci" in root or "mof" in root or "rbi" in root:
        rel_path = os.path.relpath(root, base_dir)
        if rel_path == ".":
            rel_path = "indian (root)"
        if pdf_count > 0 or not dirs: # print if has pdfs or is a leaf dir
            print(f"{rel_path:<60} | {pdf_count:>10}")
