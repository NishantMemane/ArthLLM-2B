import os, json
BASE = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section1\datasets\edgar-corpus"

total = 0
total_size = 0
year_stats = {}
for year_dir in sorted(os.listdir(BASE)):
    year_path = os.path.join(BASE, year_dir)
    if not os.path.isdir(year_path): continue
    year_count = 0
    year_size = 0
    for f in os.listdir(year_path):
        fpath = os.path.join(year_path, f)
        fsize = os.path.getsize(fpath)
        year_size += fsize
        with open(fpath, "r", encoding="utf-8") as fh:
            count = sum(1 for _ in fh)
        year_count += count
    total += year_count
    total_size += year_size
    year_stats[year_dir] = (year_count, year_size)

print(f"Total entries: {total}")
print(f"Total size: {total_size / (1024**3):.2f} GB")
print(f"Years covered: {min(year_stats.keys())} to {max(year_stats.keys())}")
print()
for y, (c, s) in sorted(year_stats.items()):
    print(f"  {y}: {c:6d} entries  ({s/(1024**2):8.1f} MB)")

# Sample a single entry to check text length
with open(os.path.join(BASE, "2020", "train.jsonl"), "r", encoding="utf-8") as f:
    entry = json.loads(f.readline())
text_field = entry.get("text", "")
print(f"\nSample text length (chars): {len(text_field)}")
print(f"Sample text (first 500 chars): {text_field[:500]}")

# Check avg text length across 100 samples from 2020
lengths = []
with open(os.path.join(BASE, "2020", "train.jsonl"), "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if i >= 100: break
        e = json.loads(line)
        lengths.append(len(e.get("text", "")))

print(f"\nAvg text length (100 samples from 2020): {sum(lengths)/len(lengths):.0f} chars")
print(f"Min: {min(lengths)}, Max: {max(lengths)}")
