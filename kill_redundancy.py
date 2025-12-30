import os
import shutil

files_to_remove = [
    'ACCURACY_REPORT.md', 'ACCURACY_SUMMARY.md', 'EVENT_MONITOR.md', 
    'REACTIVE_INTELLIGENCE.md', 'TESTING_GUIDE.md', '.env', 
    'app.py', 'agent.py', 'event_monitor.py', 'reactive_intelligence.py', 
    'database.py', 'embeddings.py', 'ingest_docs.py', 'simple_store.py', 
    'cleanup.bat', 'reorganize.bat', 'cleanup_now.bat'
]

for f in files_to_remove:
    try:
        if os.path.exists(f):
            os.remove(f)
            print(f"Removed {f}")
    except Exception as e:
        print(f"Error removing {f}: {e}")

try:
    if os.path.exists('Data'):
        shutil.rmtree('Data')
        print("Removed Data directory")
except Exception as e:
    print(f"Error removing Data directory: {e}")
