"""Configuration for the application."""
import os
from pathlib import Path

class Config:
    # Database - SQLite by default
    DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite://slo_search.db')
    
    # Embedding model (Ollama)
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'nomic-embed-text')
    
    # Data directory
    DATA_DIR = Path(os.getenv('DATA_DIR', '../curriculum-fo/data'))
    
    # Ollama settings for LLM reranking
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')

config = Config()
