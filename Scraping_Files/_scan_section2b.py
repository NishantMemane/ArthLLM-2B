"""Scan SEBI, MCA, MOF, Budget, Other Regulators — with UTF-8 output fix."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian"
EXTRACTED = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\extracted_text"

def scan_dir(path):
    stats = {"pdf": 0, "txt": 0, "json": 0, "html": 0, "csv": 0, "other": 0}
    sizes = {"pdf": 0, "txt": 0, "json": 0, "html": 0, "csv": 0, "other": 0}
    total_files = 0
    years_found = set()
    if not os.path.exists(path): return None
    for root, dirs, files in os.walk(path):
        for f in files:
            fpath = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower().lstrip(".")
            try: fsize = os.path.getsize(fpath)
            except: fsize = 0
            total_files += 1
            parts = root.replace("\\", "/").split("/")
            for p in parts:
                if p.isdigit() and 1900 < int(p) < 2030: years_found.add(int(p))
            if ext in stats: stats[ext] += 1; sizes[ext] += fsize
            else: stats["other"] += 1; sizes["other"] += fsize
    return {"total_files": total_files, "by_type": {k:v for k,v in stats.items() if v>0},
            "sizes_mb": {k:round(v/(1024*1024),1) for k,v in sizes.items() if v>0},
            "total_size_mb": round(sum(sizes.values())/(1024*1024),1),
            "years": sorted(years_found) if years_found else []}

def list_subdirs(path):
    if not os.path.exists(path): return []
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

# ============================================================
# SEBI
# ============================================================
print("=" * 80)
print("SEBI SOURCES")
print("=" * 80)
sebi_sources = ["annual_reports", "board_meetings", "board_meeting_decisions", "circulars",
                "consultation_papers", "enforcement_orders", "faqs", "orders",
                "press_releases", "regulations"]
for src in sebi_sources:
    path = os.path.join(BASE, "sebi", src)
    print(f"\n--- sebi/{src} ---")
    if not os.path.exists(path): print("  DOES NOT EXIST"); continue
    subdirs = list_subdirs(path)
    print(f"  Subdirs: {subdirs[:10]}")
    dl_path = os.path.join(path, "downloads")
    if os.path.exists(dl_path):
        stats = scan_dir(dl_path)
        print(f"  Downloads: {stats}")
    else:
        stats = scan_dir(path)
        print(f"  Direct: {stats}")
    ext_path = os.path.join(EXTRACTED, "sebi", src)
    if os.path.exists(ext_path):
        ext_stats = scan_dir(ext_path)
        print(f"  Extracted: {ext_stats}")

# ============================================================
# MCA
# ============================================================
print("\n" + "=" * 80)
print("MCA SOURCES")
print("=" * 80)
mca_path = os.path.join(BASE, "mca")
if os.path.exists(mca_path):
    subdirs = list_subdirs(mca_path)
    print(f"Top-level: {subdirs}")
    for src in subdirs:
        src_path = os.path.join(mca_path, src)
        print(f"\n--- mca/{src} ---")
        inner = list_subdirs(src_path)
        print(f"  Inner dirs: {inner[:15]}{'...' if len(inner)>15 else ''}")
        stats = scan_dir(src_path)
        print(f"  Stats: {stats}")

ext_mca = os.path.join(EXTRACTED, "mca")
if os.path.exists(ext_mca):
    print(f"\nMCA Extracted Text:")
    for sub in list_subdirs(ext_mca):
        stats = scan_dir(os.path.join(ext_mca, sub))
        print(f"  {sub}: {stats}")

# ============================================================
# MOF
# ============================================================
print("\n" + "=" * 80)
print("MOF SOURCES")
print("=" * 80)
mof_path = os.path.join(BASE, "mof")
if os.path.exists(mof_path):
    subdirs = list_subdirs(mof_path)
    print(f"Top-level: {subdirs}")
    for src in subdirs:
        src_path = os.path.join(mof_path, src)
        print(f"\n--- mof/{src} ---")
        dl_path = os.path.join(src_path, "downloads")
        if os.path.exists(dl_path):
            inner = list_subdirs(dl_path)
            print(f"  Year folders ({len(inner)}): {inner[:8]}...{inner[-3:] if len(inner)>8 else ''}")
            stats = scan_dir(dl_path)
            print(f"  Stats: {stats}")
        else:
            stats = scan_dir(src_path)
            print(f"  Direct: {stats}")

ext_mof = os.path.join(EXTRACTED, "mof")
if os.path.exists(ext_mof):
    print(f"\nMOF Extracted Text:")
    for sub in list_subdirs(ext_mof):
        stats = scan_dir(os.path.join(ext_mof, sub))
        print(f"  {sub}: {stats}")

# ============================================================
# BUDGET
# ============================================================
print("\n" + "=" * 80)
print("BUDGET SOURCES")
print("=" * 80)
for budget_try in [os.path.join(BASE, "budget"),
                   os.path.join(BASE, "..", "budget"),
                   os.path.join(BASE, "..", "..", "budget")]:
    if os.path.exists(budget_try):
        print(f"Found at: {os.path.abspath(budget_try)}")
        subdirs = list_subdirs(budget_try)
        print(f"Subdirs: {subdirs}")
        for src in subdirs:
            stats = scan_dir(os.path.join(budget_try, src))
            print(f"  {src}: {stats}")
        break
else:
    print("  NOT FOUND")

ext_budget = os.path.join(EXTRACTED, "budget")
if os.path.exists(ext_budget):
    print(f"\nBudget Extracted Text:")
    for sub in list_subdirs(ext_budget):
        stats = scan_dir(os.path.join(ext_budget, sub))
        print(f"  {sub}: {stats}")

# ============================================================
# OTHER REGULATORS
# ============================================================
print("\n" + "=" * 80)
print("OTHER REGULATORS")
print("=" * 80)
other_path = os.path.join(BASE, "other_regulators")
if os.path.exists(other_path):
    regs = list_subdirs(other_path)
    print(f"Regulators: {regs}")
    for reg in regs:
        stats = scan_dir(os.path.join(other_path, reg))
        print(f"  {reg}: {stats}")

ext_other = os.path.join(EXTRACTED, "other_regulators")
if os.path.exists(ext_other):
    print(f"\nOther Regulators Extracted Text:")
    for sub in list_subdirs(ext_other):
        stats = scan_dir(os.path.join(ext_other, sub))
        print(f"  {sub}: {stats}")

# ============================================================
# EXTRACTED TEXT TOP LEVEL
# ============================================================
print("\n" + "=" * 80)
print("EXTRACTED TEXT OVERVIEW")
print("=" * 80)
if os.path.exists(EXTRACTED):
    for cat in list_subdirs(EXTRACTED):
        stats = scan_dir(os.path.join(EXTRACTED, cat))
        print(f"  {cat}: {stats}")

print("\nDONE")
