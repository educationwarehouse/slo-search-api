"""Embeddings using Ollama."""
import requests
import numpy as np
from config import config

class OllamaEmbeddings:
    """Ollama embeddings client."""
    
    def __init__(self, model: str = None, host: str = None):
        self.model = model or config.EMBEDDING_MODEL
        self.host = host or config.OLLAMA_HOST
        
    def encode(self, text: str | list[str], convert_to_numpy: bool = True) -> np.ndarray:
        """Encode text to embeddings."""
        if isinstance(text, str):
            text = [text]
        
        embeddings = []
        for t in text:
            response = requests.post(
                f"{self.host}/api/embeddings",
                json={"model": self.model, "prompt": t}
            )
            response.raise_for_status()
            emb = response.json()['embedding']
            embeddings.append(emb)
        
        if convert_to_numpy:
            return np.array(embeddings[0] if len(embeddings) == 1 else embeddings)
        return embeddings[0] if len(embeddings) == 1 else embeddings

_embedder = None

def get_embeddings(model: str = None) -> OllamaEmbeddings:
    """Get embeddings instance (singleton)."""
    global _embedder
    if _embedder is None:
        _embedder = OllamaEmbeddings(model)
    return _embedder

def combine_text_for_embedding(title: str, description: str) -> str:
    """Combine title and description for embedding."""
    return f"{title}\n{description}" if title else description

def create_embeddings_batch(texts: list[str], model_name: str = None) -> list:
    """Create embeddings for a batch of texts."""
    embedder = get_embeddings(model_name)
    embeddings = []
    for text in texts:
        emb = embedder.encode(text, convert_to_numpy=False)
        embeddings.append(emb)
    return embeddings
