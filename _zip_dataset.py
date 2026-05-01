import os
import zipfile
from tqdm import tqdm

def zip_dataset():
    # Source and Destination paths
    source_dir = r"C:\Users\shree\Desktop\AA\ArthLLM-2B\data\raw\section2"
    zip_path = r"C:\Users\shree\Desktop\AA\ArthLLM_Indian_Data_Backup.zip"
    
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
        for file_path in tqdm(all_files, desc="Zipping Data", unit="file"):
            # We want the ZIP structure to start at "section2/" instead of "C:\Users\..."
            arcname = os.path.relpath(file_path, os.path.dirname(source_dir))
            try:
                zipf.write(file_path, arcname)
            except Exception as e:
                # Silently skip any locked/unreadable files
                pass

    print(f"\n✅ Zipping Complete!")
    print(f"Your compressed archive is ready at: {zip_path}")
    print(f"You can now upload this SINGLE file to Google Drive for maximum speed!")

if __name__ == "__main__":
    zip_dataset()
