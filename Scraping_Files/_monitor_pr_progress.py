import os
import sys
import json
import time

CHECKPOINT_FILE = r'C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\rbi\press_releases\downloads\text\_gap_checkpoint.json'
START_PRID = 44520
END_PRID = 62579
TOTAL_PRIDS = END_PRID - START_PRID + 1

def read_checkpoint():
    try:
        if not os.path.exists(CHECKPOINT_FILE):
            return None
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return None

def main():
    print("=" * 70)
    print("RBI Press Release Downloader — Live Progress Monitor")
    print("=" * 70)
    
    while not os.path.exists(CHECKPOINT_FILE):
        print("Waiting for downloader to start...", end="\r")
        time.sleep(1)
        
    target_downloads = TOTAL_PRIDS
    print(f"Targeting ~{target_downloads} missing press releases...")
    print("-" * 70)
    
    while True:
        data = read_checkpoint()
        if not data:
            time.sleep(1)
            continue
            
        stats = data.get("stats", {})
        success = stats.get("success", 0)
        errors = stats.get("errors", 0)
        not_found = stats.get("not_found", 0)
        mp_found = stats.get("mp_found", 0)
        
        current_processed = success + not_found + errors
        pct = (current_processed / target_downloads) * 100 if target_downloads > 0 else 0
        
        # Clear line and print live stats
        sys.stdout.write(f"\r[LIVE] Processed: {current_processed}/{target_downloads} ({pct:.1f}%) | Success: {success} | MP Docs Found: {mp_found} | 404/Errors: {not_found + errors}   ")
        sys.stdout.flush()
        
        if current_processed >= target_downloads:
            break
            
        time.sleep(1)

    print("\n\nDownload process appears to be complete!")
    print(f"Final Stats: Success={stats.get('success', 0)}, MP Found={stats.get('mp_found', 0)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
