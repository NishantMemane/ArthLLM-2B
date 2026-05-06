"""
Exhaustive analysis of all 7 datasets in section1/datasets
"""
import os, json, csv, sys

BASE = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section1\datasets"

# ============================================================
# 1. ChanceFocus / flare-finqa (Parquet)
# ============================================================
print("=" * 80)
print("DATASET 1: ChanceFocus / flare-finqa")
print("=" * 80)
try:
    import pandas as pd
    df = pd.read_parquet(os.path.join(BASE, "ChanceFocus", "flare-finqa", "data", "train-00000-of-00001-76a97cdb03ed8a9c.parquet"))
    print(f"Columns: {list(df.columns)}")
    print(f"Dtypes:\n{df.dtypes}")
    print(f"Shape: {df.shape}")
    print(f"\nFirst 2 rows:")
    for i in range(min(2, len(df))):
        print(f"\n--- Row {i} ---")
        for col in df.columns:
            val = str(df.iloc[i][col])
            print(f"  {col}: {val[:300]}{'...' if len(val)>300 else ''}")
    
    # Check test and valid sizes
    df_test = pd.read_parquet(os.path.join(BASE, "ChanceFocus", "flare-finqa", "data", "test-00000-of-00001-5ed0ee6b1f761c33.parquet"))
    df_val = pd.read_parquet(os.path.join(BASE, "ChanceFocus", "flare-finqa", "data", "valid-00000-of-00001-ebe922b746bd1328.parquet"))
    print(f"\nSplit sizes: train={len(df)}, test={len(df_test)}, valid={len(df_val)}")
    print(f"Total samples: {len(df) + len(df_test) + len(df_val)}")
except Exception as e:
    print(f"Error: {e}")

# ============================================================
# 2. FinGPT / fingpt-sentiment-train (Parquet)
# ============================================================
print("\n" + "=" * 80)
print("DATASET 2: FinGPT / fingpt-sentiment-train")
print("=" * 80)
try:
    df = pd.read_parquet(os.path.join(BASE, "FinGPT", "fingpt-sentiment-train", "data", "train-00000-of-00001-dabab110260ac909.parquet"))
    print(f"Columns: {list(df.columns)}")
    print(f"Dtypes:\n{df.dtypes}")
    print(f"Shape: {df.shape}")
    print(f"\nFirst 3 rows:")
    for i in range(min(3, len(df))):
        print(f"\n--- Row {i} ---")
        for col in df.columns:
            val = str(df.iloc[i][col])
            print(f"  {col}: {val[:300]}{'...' if len(val)>300 else ''}")
    
    # Label distribution
    if 'output' in df.columns:
        print(f"\nLabel distribution (output column):")
        print(df['output'].value_counts().to_string())
except Exception as e:
    print(f"Error: {e}")

# ============================================================
# 3. edgar-corpus (JSONL)
# ============================================================
print("\n" + "=" * 80)
print("DATASET 3: edgar-corpus")
print("=" * 80)
try:
    # Check a sample JSONL
    train_path = os.path.join(BASE, "edgar-corpus", "1993", "train.jsonl")
    with open(train_path, 'r', encoding='utf-8') as f:
        lines = [json.loads(f.readline()) for _ in range(3)]
    print(f"Keys in each entry: {list(lines[0].keys())}")
    for i, entry in enumerate(lines):
        print(f"\n--- Entry {i} ---")
        for k, v in entry.items():
            val = str(v)
            print(f"  {k}: {val[:300]}{'...' if len(val)>300 else ''}")
    
    # Count total entries across all years
    total = 0
    total_size = 0
    years_info = []
    for year_dir in sorted(os.listdir(os.path.join(BASE, "edgar-corpus"))):
        year_path = os.path.join(BASE, "edgar-corpus", year_dir)
        if os.path.isdir(year_path):
            for f in os.listdir(year_path):
                fpath = os.path.join(year_path, f)
                fsize = os.path.getsize(fpath)
                total_size += fsize
                with open(fpath, 'r', encoding='utf-8') as fh:
                    count = sum(1 for _ in fh)
                total += count
                years_info.append((year_dir, f, count, fsize))
    
    print(f"\nTotal entries across all years: {total}")
    print(f"Total size: {total_size / (1024*1024*1024):.2f} GB")
    print(f"\nPer-year breakdown (first 5 and last 5):")
    for info in years_info[:5]:
        print(f"  {info[0]}/{info[1]}: {info[2]} entries ({info[3]/(1024*1024):.1f} MB)")
    print("  ...")
    for info in years_info[-5:]:
        print(f"  {info[0]}/{info[1]}: {info[2]} entries ({info[3]/(1024*1024):.1f} MB)")
except Exception as e:
    print(f"Error: {e}")

# ============================================================
# 4. gbharti / finance-alpaca (JSON)
# ============================================================
print("\n" + "=" * 80)
print("DATASET 4: gbharti / finance-alpaca")
print("=" * 80)
try:
    json_path = os.path.join(BASE, "gbharti", "finance-alpaca", "Cleaned_date.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Type: {type(data)}")
    print(f"Total entries: {len(data)}")
    print(f"File size: {os.path.getsize(json_path)/(1024*1024):.1f} MB")
    print(f"Keys in first entry: {list(data[0].keys())}")
    
    for i in range(min(3, len(data))):
        print(f"\n--- Entry {i} ---")
        for k, v in data[i].items():
            val = str(v)
            print(f"  {k}: {val[:300]}{'...' if len(val)>300 else ''}")
    
    # Analyze text lengths
    lengths = [len(str(d.get('output', ''))) for d in data]
    print(f"\nOutput field lengths: min={min(lengths)}, max={max(lengths)}, avg={sum(lengths)/len(lengths):.0f}")
    
    # Check for instruction types
    instructions = [str(d.get('instruction', ''))[:50] for d in data[:20]]
    print(f"\nSample instructions (first 20):")
    for inst in instructions:
        print(f"  - {inst}")
except Exception as e:
    print(f"Error: {e}")

# ============================================================
# 5. nickmuchi / financial-classification (Parquet)
# ============================================================
print("\n" + "=" * 80)
print("DATASET 5: nickmuchi / financial-classification")
print("=" * 80)
try:
    df_train = pd.read_parquet(os.path.join(BASE, "nickmuchi", "financial-classification", "data", "train-00000-of-00001.parquet"))
    df_test = pd.read_parquet(os.path.join(BASE, "nickmuchi", "financial-classification", "data", "test-00000-of-00001.parquet"))
    print(f"Columns: {list(df_train.columns)}")
    print(f"Dtypes:\n{df_train.dtypes}")
    print(f"Train shape: {df_train.shape}, Test shape: {df_test.shape}")
    print(f"Total: {len(df_train) + len(df_test)}")
    
    for i in range(min(3, len(df_train))):
        print(f"\n--- Row {i} ---")
        for col in df_train.columns:
            val = str(df_train.iloc[i][col])
            print(f"  {col}: {val[:300]}{'...' if len(val)>300 else ''}")
    
    if 'label' in df_train.columns:
        print(f"\nLabel distribution (train):")
        print(df_train['label'].value_counts().to_string())
except Exception as e:
    print(f"Error: {e}")

# ============================================================
# 6. sujet-ai / Sujet-Finance-Instruct-177k (CSV)
# ============================================================
print("\n" + "=" * 80)
print("DATASET 6: sujet-ai / Sujet-Finance-Instruct-177k")
print("=" * 80)
try:
    csv_path = os.path.join(BASE, "sujet-ai", "Sujet-Finance-Instruct-177k", "sujet-ai", "Sujet-Finance-Instruct-177k.csv")
    df = pd.read_csv(csv_path, nrows=5)
    print(f"Columns: {list(df.columns)}")
    print(f"Dtypes:\n{df.dtypes}")
    
    # Count total rows efficiently
    total_rows = sum(1 for _ in open(csv_path, 'r', encoding='utf-8')) - 1
    print(f"Total rows: {total_rows}")
    print(f"File size: {os.path.getsize(csv_path)/(1024*1024):.1f} MB")
    
    for i in range(min(3, len(df))):
        print(f"\n--- Row {i} ---")
        for col in df.columns:
            val = str(df.iloc[i][col])
            print(f"  {col}: {val[:300]}{'...' if len(val)>300 else ''}")
    
    # Check output categories if any
    df_sample = pd.read_csv(csv_path, nrows=1000)
    if 'answer_type' in df_sample.columns:
        print(f"\nAnswer type distribution (first 1000):")
        print(df_sample['answer_type'].value_counts().to_string())
    if 'data_source' in df_sample.columns:
        print(f"\nData source distribution (first 1000):")
        print(df_sample['data_source'].value_counts().to_string())
except Exception as e:
    print(f"Error: {e}")

# ============================================================
# 7. zeroshot / twitter-financial-news (CSV)
# ============================================================
print("\n" + "=" * 80)
print("DATASET 7: zeroshot / twitter-financial-news")
print("=" * 80)
try:
    for fname in ['sent_train.csv', 'sent_valid.csv']:
        fpath = os.path.join(BASE, "zeroshot", "twitter-financial-news", fname)
        df = pd.read_csv(fpath)
        print(f"\n{fname}:")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Dtypes:\n{df.dtypes}")
        print(f"  Shape: {df.shape}")
        
        if fname == 'sent_train.csv':
            for i in range(min(3, len(df))):
                print(f"\n  --- Row {i} ---")
                for col in df.columns:
                    val = str(df.iloc[i][col])
                    print(f"    {col}: {val[:300]}{'...' if len(val)>300 else ''}")
            
            if 'label' in df.columns:
                print(f"\n  Label distribution:")
                print(df['label'].value_counts().to_string())
            
            # Text length stats
            if 'text' in df.columns:
                lengths = df['text'].str.len()
                print(f"\n  Text length: min={lengths.min()}, max={lengths.max()}, avg={lengths.mean():.0f}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
