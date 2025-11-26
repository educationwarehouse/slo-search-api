"""FastAPI version for Vercel deployment."""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os

from models import get_db
from search import (
    search_doelzinnen,
    search_uitwerkingen, 
    search_combined,
    get_doelzin_with_uitwerkingen
)
from rerank import rerank_results
from qb_cosine import enhance_with_qb_cosine
from config import config

app = FastAPI(
    title="SLO Curriculum Search API",
    version="0.1.0",
    description="Semantic search over Dutch curriculum data"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB once at startup
db = None

def init_db():
    """Initialize database schema once."""
    global db
    db = get_db()

def get_database():
    """Get database connection - assumes db already initialized."""
    if db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return db

# Startup: initialize database
init_db()


class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 100  # High enough to capture all relevant results
    threshold: Optional[float] = 0.6  # Filter to fair+ quality
    weight: Optional[float] = 0.7


@app.get("/")
def root():
    """API documentation."""
    return {
        "service": "SLO Curriculum Search API",
        "version": "0.1.0",
        "endpoints": {
            "/api/search": "Combined search (GET/POST)",
            "/api/search/doelzinnen": "Search doelzinnen only",
            "/api/search/uitwerkingen": "Search uitwerkingen only",
            "/api/doelzin/{id}": "Get full doelzin",
            "/api/stats": "Database statistics"
        },
        "docs": "/docs"
    }


@app.get("/api/search")
@app.post("/api/search")
def api_search(
    q: Optional[str] = Query(None),
    query: Optional[str] = None,
    limit: int = Query(100),
    threshold: float = Query(0.6),
    weight: float = Query(0.7),
    rerank: bool = Query(True, description="Use LLM re-ranking for better results"),
    body: Optional[SearchRequest] = None
):
    """Combined search across doelzinnen and uitwerkingen."""
    db = get_database()
    
    # Handle both query params and JSON body
    search_query = q or (body.query if body else None) or query
    if not search_query:
        raise HTTPException(400, "Missing query parameter")
    
    search_limit = body.limit if body else limit
    search_threshold = body.threshold if body else threshold
    search_weight = body.weight if body else weight
    
    results = search_combined(
        db, 
        search_query, 
        limit=search_limit,
        threshold=search_threshold,
        doelzin_weight=search_weight
    )
    
    # Optional LLM re-ranking
    if rerank:
        results = rerank_results(search_query, results, limit=search_limit)
    
    # Apply query-boosted cosine for hybrid semantic + lexical search
    results = enhance_with_qb_cosine(search_query, results)
    
    # Apply threshold filtering after all enhancements
    results = [r for r in results if r['similarity'] >= search_threshold]
    
    # Limit results
    results = results[:search_limit]
    
    return {
        "query": search_query,
        "count": len(results),
        "results": results,
        "reranked": rerank,
        "enhanced": True
    }


@app.get("/api/search/doelzinnen")
@app.post("/api/search/doelzinnen")
def api_search_doelzinnen(
    q: Optional[str] = Query(None),
    query: Optional[str] = None,
    limit: int = Query(10),
    threshold: float = Query(0.0),
    body: Optional[SearchRequest] = None
):
    """Search doelzinnen by lesson description."""
    db = get_database()
    
    search_query = q or (body.query if body else None) or query
    if not search_query:
        raise HTTPException(400, "Missing query parameter")
    
    search_limit = body.limit if body else limit
    search_threshold = body.threshold if body else threshold
    
    results = search_doelzinnen(
        db,
        search_query,
        limit=search_limit,
        threshold=search_threshold
    )
    
    return {
        "query": search_query,
        "count": len(results),
        "results": results
    }


@app.get("/api/search/uitwerkingen")
def api_search_uitwerkingen(
    q: str = Query(...),
    limit: int = Query(10),
    threshold: float = Query(0.0)
):
    """Search uitwerkingen by description."""
    db = get_database()
    
    results = search_uitwerkingen(
        db,
        q,
        limit=limit,
        threshold=threshold
    )
    
    return {
        "query": q,
        "count": len(results),
        "results": results
    }


@app.get("/api/doelzin/{doelzin_id}")
def api_get_doelzin(doelzin_id: int):
    """Get full doelzin with linked uitwerkingen."""
    db = get_database()
    
    result = get_doelzin_with_uitwerkingen(db, doelzin_id)
    if not result:
        raise HTTPException(404, "Doelzin not found")
    
    return result


@app.get("/api/stats")
def api_stats():
    """Get database statistics."""
    db = get_database()
    
    doelzin_count = db(db.doelzin).count()
    uitwerking_count = db(db.uitwerking).count()
    doelzin_embedded = db(db.doelzin_embedding).count()
    uitwerking_embedded = db(db.uitwerking_embedding).count()
    
    return {
        "doelzinnen": {
            "total": doelzin_count,
            "embedded": doelzin_embedded
        },
        "uitwerkingen": {
            "total": uitwerking_count,
            "embedded": uitwerking_embedded
        }
    }


# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
