import os
import shutil
import traceback

root = r"d:\Hugo"
data_dir = os.path.join(root, "data")
data_subdir = os.path.join(data_dir, "Data")
root_data_src = os.path.join(root, "Data")

logfile = os.path.join(root, "transfer_log.txt")

def log(msg):
    with open(logfile, "a") as f:
        f.write(msg + "\n")
    print(msg)

if os.path.exists(logfile):
    os.remove(logfile)

log("Starting transfer...")
if not os.path.exists(data_subdir):
    os.makedirs(data_subdir)
    log(f"Created {data_subdir}")

# 1. Transfer files from root Data/ to data/Data/
if os.path.exists(root_data_src):
    items = os.listdir(root_data_src)
    log(f"Found {len(items)} items in root Data folder")
    for item in items:
        src = os.path.join(root_data_src, item)
        dst = os.path.join(data_subdir, item)
        try:
            if os.path.exists(dst):
                if os.path.isdir(dst): shutil.rmtree(dst)
                else: os.remove(dst)
            shutil.copy2(src, dst) if os.path.isfile(src) else shutil.copytree(src, dst)
            log(f"COPIED: {item}")
        except Exception:
            log(f"FAILED COPY: {item}\n{traceback.format_exc()}")

# 2. Transfer loose files in data/ to data/Data/
log("Moving loose files in data/ to data/Data/")
targets = [f for f in os.listdir(data_dir) if f.endswith(".csv") or f in ["emails", "specs", "__MACOSX"]]
for item in targets:
    if item == "Data": continue
    src = os.path.join(data_dir, item)
    dst = os.path.join(data_subdir, item)
    try:
        if os.path.exists(dst):
            if os.path.isdir(dst): shutil.rmtree(dst)
            else: os.remove(dst)
        shutil.move(src, dst)
        log(f"MOVED LOOSE: {item}")
    except Exception:
        log(f"FAILED MOVE LOOSE: {item}\n{traceback.format_exc()}")

log("Transfer complete.")
