import json
import os

checkpoint_file = r'C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\rbi\press_releases\downloads\text\_gap_checkpoint.json'
out_dir = r'C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2\raw\indian\rbi\press_releases\downloads\text'

try:
    with open(checkpoint_file, 'r') as f:
        data = json.load(f)
        stats = data.get('stats', {})
        print(f'Progress from checkpoint:')
        print(f'  Success:   {stats.get("success", 0)}')
        print(f'  Not Found: {stats.get("not_found", 0)}')
        print(f'  Errors:    {stats.get("errors", 0)}')
        print(f'  MP Found:  {stats.get("mp_found", 0)}')
        print(f'  Total Processed: {stats.get("success", 0) + stats.get("not_found", 0) + stats.get("errors", 0)}')
except Exception as e:
    print(f'Error reading checkpoint: {e}')

files = len([f for f in os.listdir(out_dir) if f.endswith('.txt') and not f.startswith('_')])
print(f'\nTotal text files in folder: {files}')
