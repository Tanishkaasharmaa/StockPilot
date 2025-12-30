import sys
import os

# Add src to sys.path
base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, 'src')
sys.path.append(src_dir)

print(f"Base Directory: {base_dir}")
print(f"Source Directory: {src_dir}")
print(f"Python Path: {sys.path}")

try:
    print("Testing core.agent...")
    from core.agent import HugoAgent
    print("✅ core.agent imported successfully")
except Exception as e:
    print(f"❌ core.agent import failed: {e}")
    import traceback
    traceback.print_exc()

try:
    print("\nTesting core.reactive_intelligence...")
    from core.reactive_intelligence import ReactiveIntelligence
    print("✅ core.reactive_intelligence imported successfully")
except Exception as e:
    print(f"❌ core.reactive_intelligence import failed: {e}")

try:
    print("\nTesting core.event_monitor...")
    from core.event_monitor import EventMonitor
    print("✅ core.event_monitor imported successfully")
except Exception as e:
    print(f"❌ core.event_monitor import failed: {e}")

try:
    print("\nTesting database.database...")
    from database.database import get_db_connection
    print("✅ database.database imported successfully")
except Exception as e:
    print(f"❌ database.database import failed: {e}")

try:
    print("\nTesting database.embeddings...")
    from database.embeddings import OllamaEmbeddingFunction
    print("✅ database.embeddings imported successfully")
except Exception as e:
    print(f"❌ database.embeddings import failed: {e}")

try:
    print("\nTesting utils.simple_store...")
    from utils.simple_store import SimpleVectorStore
    print("✅ utils.simple_store imported successfully")
except Exception as e:
    print(f"❌ utils.simple_store import failed: {e}")
