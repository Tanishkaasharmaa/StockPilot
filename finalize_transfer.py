import os
import shutil

root = r"d:\Hugo"
data_dir = os.path.join(root, "data")
data_subdir = os.path.join(data_dir, "Data")

# Ensure target directories exist
os.makedirs(data_subdir, exist_ok=True)

# 1. Move root Data/ contents to data/Data/
root_data_src = os.path.join(root, "Data")
if os.path.exists(root_data_src):
    for item in os.listdir(root_data_src):
        src_path = os.path.join(root_data_src, item)
        dst_path = os.path.join(data_subdir, item)
        try:
            if os.path.isdir(src_path):
                if os.path.exists(dst_path):
                    shutil.rmtree(dst_path)
                shutil.move(src_path, dst_path)
            else:
                shutil.move(src_path, dst_path)
            print(f"Moved {src_path} -> {dst_path}")
        except Exception as e:
            print(f"Failed to move {item}: {e}")

# 2. Move loose CSVs from root data/ to data/Data/
for item in os.listdir(data_dir):
    if item.endswith(".csv"):
        src_path = os.path.join(data_dir, item)
        dst_path = os.path.join(data_subdir, item)
        try:
            shutil.move(src_path, dst_path)
            print(f"Moved {src_path} -> {dst_path}")
        except Exception as e:
             print(f"Failed to move {item}: {e}")

# Also move these subdirs if they exist loose in data/
for d in ["emails", "specs", "__MACOSX"]:
    src_path = os.path.join(data_dir, d)
    if os.path.exists(src_path) and os.path.isdir(src_path):
        dst_path = os.path.join(data_subdir, d)
        try:
            if os.path.exists(dst_path):
                shutil.rmtree(dst_path)
            shutil.move(src_path, dst_path)
            print(f"Moved {src_path} -> {dst_path}")
        except Exception as e:
            print(f"Failed to move {d}: {e}")

# 3. Clean up root redundant files
redundant_files = [
    "ACCURACY_REPORT.md", "ACCURACY_SUMMARY.md", "EVENT_MONITOR.md", 
    "REACTIVE_INTELLIGENCE.md", "TESTING_GUIDE.md", ".env",
    "agent.py", "database.py", "embeddings.py", "event_monitor.py", 
    "ingest_docs.py", "reactive_intelligence.py", "simple_store.py",
    "cleanup.bat", "cleanup_now.bat", "reorganize.bat", "kill_redundancy.py",
    "REORG_SUCCESS.txt", "verify_imports.py", "simple_docs.json"
]

for f in redundant_files:
    f_path = os.path.join(root, f)
    if os.path.exists(f_path):
        try:
            if os.path.isdir(f_path):
                shutil.rmtree(f_path)
            else:
                os.remove(f_path)
            print(f"Removed redundant root file: {f}")
        except Exception as e:
            print(f"Could not remove {f}: {e}")

if os.path.exists(root_data_src):
    try:
        shutil.rmtree(root_data_src)
        print("Removed root Data/ folder")
    except Exception as e:
        print(f"Failed to remove root Data folder: {e}")
