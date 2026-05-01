import os
import zipfile
from tqdm import tqdm

def zip_section1():
    # Source and Destination paths
    source_dir = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section1"
    zip_path = r"C:\Users\shree\Desktop\AA\ArthLLM_Indian_Data_Section1.zip"
    
    print(f"Scanning directory: {source_dir}...")
    
    # 1. First, count all the files to set up the progress bar
    all_files = []
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            all_files.append(os.path.join(root, file))
            
    total_files = len(all_files)
    print(f"Found {total_files} total files. Preparing to compress...")
    
    # 2. Create the ZIP file with ZIP64 enabled (crucial for files > 4GB)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
        # Wrap the loop with tqdm for a beautiful progress bar
        for file_path in tqdm(all_files, desc="Zipping Section 1", unit="file"):
            # We want the ZIP structure to start at "section1/" instead of "C:\Users\..."
            arcname = os.path.relpath(file_path, os.path.dirname(source_dir))
            try:
                zipf.write(file_path, arcname)
            except Exception as e:
                # Silently skip any locked/unreadable files
                pass

    print(f"\n✅ Zipping Complete!")
    print(f"Your compressed archive for Section 1 is ready at: {zip_path}")
    print(f"You can now upload this file to Google Drive as well!")

if __name__ == "__main__":
    zip_section1()
