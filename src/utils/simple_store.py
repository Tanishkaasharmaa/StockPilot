import json
import os
import math

class SimpleVectorStore:
    def __init__(self, path=None):
        if path is None:
            # Default path relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.path = os.path.join(base_dir, 'data', 'simple_docs.json')
        else:
            self.path = path
            
        self.documents = [] # List of dicts: {'text': str, 'embedding': list, 'metadata': dict}
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                print(f"Loaded {len(self.documents)} docs from {self.path}")
            except Exception as e:
                print(f"Error loading store: {e}")
                self.documents = []
        else:
            print(f"No existing store found at {self.path}. Starting empty.")

    def save(self):
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f)
            print(f"Saved {len(self.documents)} docs to {self.path}")
        except Exception as e:
            print(f"Error saving store: {e}")

    def add(self, texts, embeddings, metadatas=None):
        if metadatas is None:
            metadatas = [{}] * len(texts)
            
        for i in range(len(texts)):
            doc = {
                'text': texts[i],
                'embedding': embeddings[i],
                'metadata': metadatas[i]
            }
            self.documents.append(doc)
        self.save()
        
    def reset(self):
        self.documents = []
        self.save()

    def cosine_similarity(self, vec1, vec2):
        dot_product = sum(a*b for a,b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a*a for a in vec1))
        magnitude2 = math.sqrt(sum(a*a for a in vec2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    def query(self, query_embedding, n_results=3):
        if not self.documents:
            return {'documents': [[]], 'metadatas': [[]]}
            
        # Calculate scores
        ranked = []
        for doc in self.documents:
            score = self.cosine_similarity(query_embedding, doc['embedding'])
            ranked.append((score, doc))
            
        # Sort desc
        ranked.sort(key=lambda x: x[0], reverse=True)
        
        # Take top N
        top_n = ranked[:n_results]
        
        # Format like Chroma response
        return {
            'documents': [[item[1]['text'] for item in top_n]],
            'metadatas': [[item[1]['metadata'] for item in top_n]]
        }
