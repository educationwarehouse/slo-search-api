"""Configuration for the application."""
import os
from pathlib import Path

class Config:
    # Database - SQLite by default
    DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite://slo_search.db')
    
    # OpenRouter settings
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
    OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
    
    # Embedding model (OpenRouter/OpenAI compatible)
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'openai/text-embedding-3-small')
    
    # LLM model for reranking
    LLM_MODEL = os.getenv('LLM_MODEL', 'openai/gpt-4o-mini')
    
    # Data directory
    DATA_DIR = Path(os.getenv('DATA_DIR', '../curriculum-fo/data'))

config = Config()
