"""Final deep data collection for Section 2 analysis."""
import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian"

def count_files(path):
    if not os.path.exists(path): return 0
    return len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])

def dir_exists(path):
    return os.path.exists(path) and os.path.isdir(path)

# 1. SEBI circulars per-year text counts
print("=== SEBI CIRCULARS TEXT PER YEAR ===")
sebi_txt = os.path.join(BASE, "sebi", "circulars", "downloads", "text")
for y in sorted(os.listdir(sebi_txt)):
    yp = os.path.join(sebi_txt, y)
    if os.path.isdir(yp):
        fc = count_files(yp)
        print(f"  {y}: {fc} texts")

# 2. SEBI circulars per-year PDF counts
print("\n=== SEBI CIRCULARS PDF PER YEAR ===")
sebi_pdf = os.path.join(BASE, "sebi", "circulars", "downloads", "pdfs")
for y in sorted(os.listdir(sebi_pdf)):
    yp = os.path.join(sebi_pdf, y)
    if os.path.isdir(yp):
        fc = count_files(yp)
        print(f"  {y}: {fc} pdfs")

# 3. RBI bulletin text per year — check for empty months
print("\n=== RBI BULLETIN TEXT — PER YEAR/MONTH ===")
bul_txt = os.path.join(BASE, "rbi", "bulletin", "downloads", "text")
for y in sorted(os.listdir(bul_txt)):
    yp = os.path.join(bul_txt, y)
    if os.path.isdir(yp):
        months = sorted(os.listdir(yp))
        month_counts = []
        for m in months:
            mp = os.path.join(yp, m)
            if os.path.isdir(mp):
                fc = count_files(mp)
                month_counts.append(f"{m}({fc})")
        print(f"  {y}: {len(months)} months -> {', '.join(month_counts[:3])}...{', '.join(month_counts[-2:]) if len(month_counts)>3 else ''}")

# 4. RBI bulletin PDFs per year — check empty
print("\n=== RBI BULLETIN PDF — PER YEAR ===")
bul_pdf = os.path.join(BASE, "rbi", "bulletin", "downloads", "pdfs")
for y in sorted(os.listdir(bul_pdf)):
    yp = os.path.join(bul_pdf, y)
    if os.path.isdir(yp):
        months = sorted(os.listdir(yp))
        total = 0
        empty_months = []
        for m in months:
            mp = os.path.join(yp, m)
            if os.path.isdir(mp):
                fc = count_files(mp)
                total += fc
                if fc == 0: empty_months.append(m)
        print(f"  {y}: {len(months)} months, {total} pdfs total" + (f" EMPTY: {empty_months}" if empty_months else ""))

# 5. RBI speeches per year
print("\n=== RBI SPEECHES PER YEAR ===")
sp_txt = os.path.join(BASE, "rbi", "speeches", "downloads", "text")
for y in sorted(os.listdir(sp_txt)):
    yp = os.path.join(sp_txt, y)
    if os.path.isdir(yp):
        fc = count_files(yp)
        print(f"  {y}: {fc} speeches")

# 6. RBI annual reports per year
print("\n=== RBI ANNUAL REPORTS PER YEAR ===")
ar_txt = os.path.join(BASE, "rbi", "annual_reports", "downloads", "text")
for y in sorted(os.listdir(ar_txt)):
    yp = os.path.join(ar_txt, y)
    if os.path.isdir(yp):
        fc = count_files(yp)
        print(f"  {y}: {fc} chapters")

# 7. Duplicate folder checks
print("\n=== DUPLICATE FOLDER CHECKS ===")
checks = [
    ("mca/downloads/ibbi_orders/hc", "mca/downloads/ibbi_orders/high_court"),
    ("mca/downloads/ibbi_orders/sc", "mca/downloads/ibbi_orders/supreme_court"),
    ("mca/downloads/nclat_orders", "mca/downloads/ibbi_orders/nclat"),
    ("mca/downloads/nclt_orders", "mca/downloads/ibbi_orders/nclt"),
]
for a, b in checks:
    pa, pb = os.path.join(BASE, a), os.path.join(BASE, b)
    ea = dir_exists(pa)
    eb = dir_exists(pb)
    ca = count_files(pa) if ea else -1
    cb = count_files(pb) if eb else -1
    print(f"  {a}: exists={ea}, files={ca}")
    print(f"  {b}: exists={eb}, files={cb}")

# 8. Check for nclat_orders and nclt_orders at mca level
print("\n=== MCA TOP-LEVEL STRUCTURE ===")
mca_dl = os.path.join(BASE, "mca", "downloads")
for sub in sorted(os.listdir(mca_dl)):
    sp = os.path.join(mca_dl, sub)
    if os.path.isdir(sp):
        inner = os.listdir(sp)
        dirs = [d for d in inner if os.path.isdir(os.path.join(sp, d))]
        files = [f for f in inner if os.path.isfile(os.path.join(sp, f))]
        print(f"  {sub}/: {len(files)} files, {len(dirs)} subdirs -> {dirs[:10]}")

# 9. Sample text from key datasets
print("\n=== SAMPLE TEXTS ===")
samples = [
    ("RBI Circular", os.path.join(BASE, "rbi", "circulars", "downloads", "text")),
    ("RBI Press Release", os.path.join(BASE, "rbi", "press_releases", "downloads", "text")),
    ("RBI Master Direction", os.path.join(BASE, "rbi", "master_directions", "downloads", "text")),
    ("SEBI Order", os.path.join(BASE, "sebi", "orders", "downloads", "text")),
    ("SEBI Circular", os.path.join(BASE, "sebi", "circulars", "downloads", "text", "2024")),
    ("SEBI Regulation", os.path.join(BASE, "sebi", "regulations", "downloads", "text")),
]
for name, path in samples:
    if os.path.exists(path):
        txts = [f for f in os.listdir(path) if f.endswith(".txt")]
        if txts:
            fp = os.path.join(path, txts[0])
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(600)
            print(f"\n--- {name} ({txts[0]}) ---")
            print(content[:500])

# 10. Text file average lengths
print("\n=== AVERAGE TEXT LENGTHS ===")
for name, path in [
    ("RBI Circulars text", os.path.join(BASE, "rbi", "circulars", "downloads", "text")),
    ("RBI Press Releases text", os.path.join(BASE, "rbi", "press_releases", "downloads", "text")),
    ("SEBI Orders text", os.path.join(BASE, "sebi", "orders", "downloads", "text")),
]:
    if os.path.exists(path):
        sizes = []
        txts = [f for f in os.listdir(path) if f.endswith(".txt")][:200]
        for t in txts:
            sizes.append(os.path.getsize(os.path.join(path, t)))
        if sizes:
            print(f"  {name}: avg={sum(sizes)/len(sizes)/1024:.1f}KB, min={min(sizes)/1024:.1f}KB, max={max(sizes)/1024:.1f}KB (sampled {len(sizes)})")

print("\nDONE")
