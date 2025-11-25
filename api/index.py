"""Vercel serverless entry point."""
from mangum import Mangum
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_fastapi import app

# Wrap FastAPI app for Vercel
handler = Mangum(app, lifespan="off")
