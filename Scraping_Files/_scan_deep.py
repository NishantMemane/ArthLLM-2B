"""DEEP exhaustive scan — go into EVERY subfolder, show real structure."""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian"

def deep_scan(path, depth=0, max_depth=6):
    """Recursively list every directory with file counts and sizes."""
    if not os.path.exists(path) or depth > max_depth:
        return
    
    items = []
    try:
        items = os.listdir(path)
    except:
        return
    
    dirs = sorted([d for d in items if os.path.isdir(os.path.join(path, d))])
    files = [f for f in items if os.path.isfile(os.path.join(path, f))]
    
    # Count files by extension
    ext_counts = {}
    total_size = 0
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
        try:
            total_size += os.path.getsize(os.path.join(path, f))
        except:
            pass
    
    indent = "  " * depth
    dirname = os.path.basename(path)
    
    if files:
        ext_str = ", ".join(f"{v}x{k}" for k, v in sorted(ext_counts.items()))
        size_str = f"{total_size/(1024*1024):.1f}MB" if total_size > 1024*1024 else f"{total_size/1024:.0f}KB"
        print(f"{indent}[{dirname}] {len(files)} files ({ext_str}) = {size_str}")
    elif dirs:
        print(f"{indent}[{dirname}]")
    else:
        print(f"{indent}[{dirname}] EMPTY")
    
    for d in dirs:
        deep_scan(os.path.join(path, d), depth + 1, max_depth)

# ============================================================
# MOF — GO DEEP
# ============================================================
print("=" * 80)
print("MOF (Ministry of Finance) — DEEP SCAN")
print("=" * 80)
deep_scan(os.path.join(BASE, "mof"), max_depth=4)

# ============================================================
# BUDGET — GO DEEP
# ============================================================
print("\n" + "=" * 80)
print("BUDGET — DEEP SCAN")
print("=" * 80)
deep_scan(os.path.join(BASE, "budget"), max_depth=4)

# ============================================================
# RBI — SHOW WHAT'S INSIDE EACH
# ============================================================
print("\n" + "=" * 80)
print("RBI — DEEP SCAN (focus on empty/missing)")
print("=" * 80)
for src in ["financial_stability_reports", "monetary_policy"]:
    print(f"\n--- rbi/{src} ---")
    deep_scan(os.path.join(BASE, "rbi", src), max_depth=4)

# Also check what's actually inside circulars, press_releases structure
for src in ["circulars", "press_releases", "bulletin", "master_directions"]:
    path = os.path.join(BASE, "rbi", src, "downloads")
    if os.path.exists(path):
        subdirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        print(f"\n--- rbi/{src}/downloads ---")
        print(f"  Subdirs: {subdirs[:10]}")
        print(f"  Top-level files: {len(files)} files")
        for sd in subdirs[:5]:
            sdpath = os.path.join(path, sd)
            fcount = len(os.listdir(sdpath))
            print(f"    {sd}/: {fcount} items")

# ============================================================
# SEBI — GO DEEP on everything
# ============================================================
print("\n" + "=" * 80)
print("SEBI — DEEP SCAN")
print("=" * 80)
for src in os.listdir(os.path.join(BASE, "sebi")):
    srcpath = os.path.join(BASE, "sebi", src)
    if os.path.isdir(srcpath):
        print(f"\n--- sebi/{src} ---")
        deep_scan(srcpath, max_depth=3)

# ============================================================
# MCA — GO DEEP
# ============================================================
print("\n" + "=" * 80)
print("MCA — DEEP SCAN")
print("=" * 80)
deep_scan(os.path.join(BASE, "mca"), max_depth=4)

# ============================================================
# OTHER REGULATORS — CONFIRM EMPTY
# ============================================================
print("\n" + "=" * 80)
print("OTHER REGULATORS — DEEP SCAN")
print("=" * 80)
deep_scan(os.path.join(BASE, "other_regulators"), max_depth=3)

# ============================================================
# EXTRACTED TEXT — CONFIRM STATUS
# ============================================================
print("\n" + "=" * 80)
print("EXTRACTED TEXT PIPELINE — DEEP SCAN")
print("=" * 80)
ext_base = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\extracted_text"
deep_scan(ext_base, max_depth=3)

# ============================================================
# CLEANED + DEDUPED pipeline
# ============================================================
for stage in ["cleaned", "deduped"]:
    stage_path = os.path.join(r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2", stage)
    print(f"\n--- {stage}/ ---")
    if os.path.exists(stage_path):
        deep_scan(stage_path, max_depth=3)
    else:
        print(f"  DOES NOT EXIST")

print("\nDONE")
