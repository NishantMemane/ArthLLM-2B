"""
Exhaustive Section 2 analysis — scan every single folder for real file counts,
sizes, year ranges, and content samples.
"""
import os, json, glob

BASE = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian"
EXTRACTED = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\extracted_text"

def scan_dir(path, label=""):
    """Recursively count files by extension and total size."""
    stats = {"pdf": 0, "txt": 0, "json": 0, "html": 0, "csv": 0, "other": 0}
    sizes = {"pdf": 0, "txt": 0, "json": 0, "html": 0, "csv": 0, "other": 0}
    total_files = 0
    years_found = set()
    
    if not os.path.exists(path):
        return None
    
    for root, dirs, files in os.walk(path):
        for f in files:
            fpath = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower().lstrip(".")
            fsize = os.path.getsize(fpath)
            total_files += 1
            
            # Try to extract year from path or filename
            parts = root.replace("\\", "/").split("/")
            for p in parts:
                if p.isdigit() and 1900 < int(p) < 2030:
                    years_found.add(int(p))
            
            if ext in stats:
                stats[ext] += 1
                sizes[ext] += fsize
            else:
                stats["other"] += 1
                sizes["other"] += fsize
    
    return {
        "total_files": total_files,
        "by_type": {k: v for k, v in stats.items() if v > 0},
        "sizes_mb": {k: round(v/(1024*1024), 1) for k, v in sizes.items() if v > 0},
        "total_size_mb": round(sum(sizes.values())/(1024*1024), 1),
        "years": sorted(years_found) if years_found else []
    }

def sample_text(path, max_chars=500):
    """Get a text sample from the first .txt file found."""
    for root, dirs, files in os.walk(path):
        for f in sorted(files):
            if f.endswith(".txt") and not f.startswith("_"):
                fpath = os.path.join(root, f)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                        text = fh.read(max_chars)
                    return f, text
                except:
                    pass
    return None, None

def list_subdirs(path):
    """List immediate subdirectories."""
    if not os.path.exists(path):
        return []
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

# ============================================================
# SCAN ALL RBI SOURCES
# ============================================================
print("=" * 80)
print("RBI SOURCES")
print("=" * 80)

rbi_sources = ["annual_reports", "bulletin", "circulars", "financial_stability_reports",
               "master_directions", "monetary_policy", "press_releases", "speeches", "working_papers"]

for src in rbi_sources:
    path = os.path.join(BASE, "rbi", src)
    print(f"\n--- rbi/{src} ---")
    subdirs = list_subdirs(path)
    print(f"  Subdirs: {subdirs[:10]}{'...' if len(subdirs)>10 else ''}")
    
    # Scan downloads
    dl_path = os.path.join(path, "downloads")
    if os.path.exists(dl_path):
        stats = scan_dir(dl_path)
        print(f"  Downloads: {stats}")
    else:
        print(f"  Downloads: NOT FOUND")
    
    # Scan for text extraction
    ext_path = os.path.join(EXTRACTED, "rbi", src)
    if os.path.exists(ext_path):
        ext_stats = scan_dir(ext_path)
        print(f"  Extracted Text: {ext_stats}")
    else:
        print(f"  Extracted Text: NOT FOUND")
    
    # Get sample
    fname, sample = sample_text(dl_path if os.path.exists(dl_path) else path)
    if sample:
        print(f"  Sample from '{fname}': {sample[:200]}...")

# ============================================================
# SCAN ALL SEBI SOURCES
# ============================================================
print("\n" + "=" * 80)
print("SEBI SOURCES")
print("=" * 80)

sebi_sources = ["annual_reports", "board_meetings", "board_meeting_decisions", "circulars",
                "consultation_papers", "enforcement_orders", "faqs", "orders", 
                "press_releases", "regulations"]

for src in sebi_sources:
    path = os.path.join(BASE, "sebi", src)
    print(f"\n--- sebi/{src} ---")
    if not os.path.exists(path):
        print(f"  PATH DOES NOT EXIST")
        continue
    subdirs = list_subdirs(path)
    print(f"  Subdirs: {subdirs[:10]}{'...' if len(subdirs)>10 else ''}")
    
    dl_path = os.path.join(path, "downloads")
    if os.path.exists(dl_path):
        stats = scan_dir(dl_path)
        print(f"  Downloads: {stats}")
    else:
        stats = scan_dir(path)
        print(f"  Direct scan: {stats}")
    
    ext_path = os.path.join(EXTRACTED, "sebi", src)
    if os.path.exists(ext_path):
        ext_stats = scan_dir(ext_path)
        print(f"  Extracted Text: {ext_stats}")
    
    fname, sample = sample_text(dl_path if os.path.exists(dl_path) else path)
    if sample:
        print(f"  Sample from '{fname}': {sample[:200]}...")

# ============================================================
# SCAN MCA SOURCES
# ============================================================
print("\n" + "=" * 80)
print("MCA SOURCES")
print("=" * 80)

mca_path = os.path.join(BASE, "mca")
if os.path.exists(mca_path):
    subdirs = list_subdirs(mca_path)
    print(f"Top-level subdirs: {subdirs}")
    
    for src in subdirs:
        src_path = os.path.join(mca_path, src)
        print(f"\n--- mca/{src} ---")
        inner_dirs = list_subdirs(src_path)
        print(f"  Subdirs: {inner_dirs[:15]}{'...' if len(inner_dirs)>15 else ''}")
        stats = scan_dir(src_path)
        print(f"  Stats: {stats}")

# MCA extracted text
ext_mca = os.path.join(EXTRACTED, "mca")
if os.path.exists(ext_mca):
    print(f"\nMCA Extracted Text:")
    stats = scan_dir(ext_mca)
    print(f"  {stats}")

# ============================================================
# SCAN MOF SOURCES
# ============================================================
print("\n" + "=" * 80)
print("MOF SOURCES")
print("=" * 80)

mof_path = os.path.join(BASE, "mof")
if os.path.exists(mof_path):
    subdirs = list_subdirs(mof_path)
    print(f"Top-level subdirs: {subdirs}")
    
    for src in subdirs:
        src_path = os.path.join(mof_path, src)
        print(f"\n--- mof/{src} ---")
        dl_path = os.path.join(src_path, "downloads")
        if os.path.exists(dl_path):
            inner = list_subdirs(dl_path)
            print(f"  Year folders: {inner[:10]}{'...' if len(inner)>10 else ''} (total: {len(inner)})")
            stats = scan_dir(dl_path)
            print(f"  Stats: {stats}")
        else:
            stats = scan_dir(src_path)
            print(f"  Direct: {stats}")

# MOF extracted text
ext_mof = os.path.join(EXTRACTED, "mof")
if os.path.exists(ext_mof):
    print(f"\nMOF Extracted Text:")
    stats = scan_dir(ext_mof)
    print(f"  {stats}")

# ============================================================
# SCAN BUDGET SOURCES
# ============================================================
print("\n" + "=" * 80)
print("BUDGET SOURCES")
print("=" * 80)

budget_path = os.path.join(BASE, "budget")
if os.path.exists(budget_path):
    subdirs = list_subdirs(budget_path)
    print(f"Top-level subdirs: {subdirs}")
    for src in subdirs:
        src_path = os.path.join(budget_path, src)
        print(f"\n--- budget/{src} ---")
        stats = scan_dir(src_path)
        print(f"  Stats: {stats}")
else:
    # Check alternate location
    for alt in [os.path.join(BASE, "..", "budget"), os.path.join(BASE, "..", "..", "budget")]:
        if os.path.exists(alt):
            print(f"Found at: {os.path.abspath(alt)}")
            subdirs = list_subdirs(alt)
            print(f"Subdirs: {subdirs}")
            for src in subdirs:
                stats = scan_dir(os.path.join(alt, src))
                print(f"  {src}: {stats}")
            break
    else:
        print("  BUDGET FOLDER NOT FOUND in expected locations")

# Budget extracted text
ext_budget = os.path.join(EXTRACTED, "budget")
if os.path.exists(ext_budget):
    print(f"\nBudget Extracted Text:")
    stats = scan_dir(ext_budget)
    print(f"  {stats}")

# ============================================================
# SCAN OTHER REGULATORS
# ============================================================
print("\n" + "=" * 80)
print("OTHER REGULATORS")
print("=" * 80)

other_path = os.path.join(BASE, "other_regulators")
if os.path.exists(other_path):
    subdirs = list_subdirs(other_path)
    print(f"Regulators: {subdirs}")
    for reg in subdirs:
        reg_path = os.path.join(other_path, reg)
        stats = scan_dir(reg_path)
        print(f"  {reg}: {stats}")
else:
    print("  OTHER_REGULATORS FOLDER NOT FOUND")

# Other regulators extracted text
ext_other = os.path.join(EXTRACTED, "other_regulators")
if os.path.exists(ext_other):
    print(f"\nOther Regulators Extracted Text:")
    stats = scan_dir(ext_other)
    print(f"  {stats}")

# ============================================================
# SCAN EXTRACTED TEXT FOLDER TOP LEVEL
# ============================================================
print("\n" + "=" * 80)
print("EXTRACTED TEXT — TOP LEVEL OVERVIEW")
print("=" * 80)

if os.path.exists(EXTRACTED):
    subdirs = list_subdirs(EXTRACTED)
    print(f"Extracted text categories: {subdirs}")
    for cat in subdirs:
        cat_path = os.path.join(EXTRACTED, cat)
        stats = scan_dir(cat_path)
        print(f"  {cat}: {stats}")
else:
    print("  EXTRACTED TEXT FOLDER NOT FOUND")

print("\n" + "=" * 80)
print("SCAN COMPLETE")
print("=" * 80)
