import os
import glob
import pypdf
import email
from email import policy
import ollama

# Internal Imports (Updated to absolute from src root)
from database.embeddings import OllamaEmbeddingFunction
from utils.simple_store import SimpleVectorStore

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(base_dir, 'data', 'Data')

def parse_eml(file_path):
    with open(file_path, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=policy.default)
    return f"Subject: {msg['subject']}\n\n{msg.get_content()}"

def ingest_data():
    db = SimpleVectorStore()
    db.reset()
    embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    print("Ingestion complete.")

if __name__ == "__main__":
    ingest_data()
