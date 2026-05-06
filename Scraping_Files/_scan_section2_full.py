import os

base = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian"

print("=" * 90)
print("SECTION 2 - FULL INVENTORY SCAN")
print("=" * 90)

for root, dirs, files in os.walk(base):
    rel = os.path.relpath(root, base)
    pdfs = [f for f in files if f.lower().endswith(".pdf")]
    jsons = [f for f in files if f.lower().endswith(".json")]
    txts = [f for f in files if f.lower().endswith(".txt")]
    htmls = [f for f in files if f.lower().endswith(".html")]
    total = len(pdfs) + len(jsons) + len(txts) + len(htmls)
    if total > 0:
        parts = []
        if pdfs:
            parts.append(str(len(pdfs)) + " pdf")
        if jsons:
            parts.append(str(len(jsons)) + " json")
        if txts:
            parts.append(str(len(txts)) + " txt")
        if htmls:
            parts.append(str(len(htmls)) + " html")
        print(rel.ljust(65) + " | " + "  ".join(parts))
