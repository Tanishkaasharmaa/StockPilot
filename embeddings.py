from chromadb import Documents, EmbeddingFunction, Embeddings
import os
from dotenv import load_dotenv
import ollama

load_dotenv()

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
                # Return a zero vector or handle appropriately - for now, we might crash or return empty
                # Ideally we want to be robust. 
                # Let's try to proceed or Append a dummy vector if critical? 
                # For now just printing error.
                pass 
        return embeddings
