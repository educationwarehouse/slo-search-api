"""Embeddings using OpenRouter."""
import numpy as np
from openai import OpenAI
from config import config

class OpenRouterEmbeddings:
    """OpenRouter embeddings client."""
    
    def __init__(self, model: str = None):
        self.model = model or config.EMBEDDING_MODEL
        self.client = OpenAI(
            base_url=config.OPENROUTER_BASE_URL,
            api_key=config.OPENROUTER_API_KEY
        )
        
    def encode(self, text: str | list[str], convert_to_numpy: bool = True) -> np.ndarray:
        """Encode text to embeddings."""
        if isinstance(text, str):
            text = [text]
        
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        
        embeddings = [item.embedding for item in response.data]
        
        if convert_to_numpy:
            return np.array(embeddings[0] if len(embeddings) == 1 else embeddings)
        # Always return list for consistency when not converting to numpy
        return embeddings

_embedder = None

def get_embeddings(model: str = None) -> OpenRouterEmbeddings:
    """Get embeddings instance (singleton)."""
    global _embedder
    if _embedder is None:
        _embedder = OpenRouterEmbeddings(model)
    return _embedder

def combine_text_for_embedding(title: str, description: str) -> str:
    """Combine title and description for embedding."""
    return f"{title}\n{description}" if title else description

def create_embeddings_batch(texts: list[str], model_name: str = None, batch_size: int = 100) -> list:
    """Create embeddings for a batch of texts."""
    from tqdm import tqdm
    
    embedder = get_embeddings(model_name)
    embeddings = []
    
    # Process in batches for efficiency (100 texts per API call)
    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding batches"):
        batch = texts[i:i + batch_size]
        batch_embeddings = embedder.encode(batch, convert_to_numpy=False)
        embeddings.extend(batch_embeddings)
    
    return embeddings
