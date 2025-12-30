from chromadb import Documents, EmbeddingFunction, Embeddings
import os
from dotenv import load_dotenv
import ollama

# Load .env from config directory
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', '.env')
load_dotenv(env_path)

class OllamaEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        # Default to nomic-embed-text if not specified
        self.model_name = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = []
        for text in input:
            try:
                response = ollama.embeddings(model=self.model_name, prompt=text)
                embeddings.append(response["embedding"])
            except Exception as e:
                print(f"Error generating embedding for text: {text[:30]}... Error: {e}")
                pass 
        return embeddings
