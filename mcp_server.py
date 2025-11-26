"""MCP Server for SLO Curriculum Search.

Exposes search functionality via Model Context Protocol.
"""
from fastmcp import FastMCP
from typing import Optional
import json

from models import get_db
from search import (
    search_doelzinnen,
    search_uitwerkingen,
    search_combined,
    get_doelzin_with_uitwerkingen
)
from rerank import rerank_results
from qb_cosine import enhance_with_qb_cosine

# Initialize MCP server
mcp = FastMCP("slo-curriculum-search")

# Initialize database once at startup
db = get_db()


@mcp.tool()
def search(
    query: str,
    limit: int = 100,
    threshold: float = 0.5,  # Lower default - real scores are 0.54-0.75
    weight: float = 0.7,
    rerank: bool = None  # Auto: True for complex queries (5+ words)
) -> str:
    """Zoek in het SLO curriculum (doelzinnen en uitwerkingen).
    
    Gebruikt hybride semantic + lexical search met optionele LLM re-ranking.
    
    Args:
        query: Zoekterm (bijv. "fotosynthese", "wiskunde")
        limit: Max aantal resultaten (default: 100)
        threshold: Min similarity 0-1 (default: 0.5)
        weight: Doelzin weight 0-1 (default: 0.7, hogere waarde = meer focus op doelzinnen)
        rerank: Gebruik LLM re-ranking (default: auto - True for 5+ words)
    
    Returns:
        JSON met zoekresultaten en metadata
    """
    # Auto-enable reranking for complex queries (5+ words)
    if rerank is None:
        word_count = len(query.split())
        rerank = word_count >= 5
    
    # Get initial results with low threshold to catch potential matches
    results = search_combined(
        db,
        query,
        limit=limit * 3,  # Get more for reranking/filtering
        threshold=0.2,  # Low threshold - filter noise but catch potential
        doelzin_weight=weight
    )
    
    if rerank:
        results = rerank_results(query, results, limit=limit * 2)
    
    results = enhance_with_qb_cosine(query, results)
    
    # Apply final threshold ONCE after all enhancements
    results = [r for r in results if r['similarity'] >= threshold]
    results = results[:limit]
    
    return json.dumps({
        "query": query,
        "count": len(results),
        "results": results,
        "reranked": rerank,
        "enhanced": True
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def search_goals(
    query: str,
    limit: int = 10,
    threshold: float = 0.0
) -> str:
    """Zoek alleen in doelzinnen (leerdoelen).
    
    Args:
        query: Zoekterm
        limit: Max aantal resultaten (default: 10)
        threshold: Min similarity 0-1 (default: 0.0)
    
    Returns:
        JSON met doelzin zoekresultaten
    """
    results = search_doelzinnen(db, query, limit=limit, threshold=threshold)
    
    return json.dumps({
        "query": query,
        "count": len(results),
        "results": results
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def search_elaborations(
    query: str,
    limit: int = 10,
    threshold: float = 0.0
) -> str:
    """Zoek alleen in uitwerkingen (uitgebreide beschrijvingen).
    
    Args:
        query: Zoekterm
        limit: Max aantal resultaten (default: 10)
        threshold: Min similarity 0-1 (default: 0.0)
    
    Returns:
        JSON met uitwerking zoekresultaten
    """
    results = search_uitwerkingen(db, query, limit=limit, threshold=threshold)
    
    return json.dumps({
        "query": query,
        "count": len(results),
        "results": results
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_goal(doelzin_id: int) -> str:
    """Haal een specifieke doelzin op met alle gekoppelde uitwerkingen.
    
    Args:
        doelzin_id: Database ID van de doelzin
    
    Returns:
        JSON met complete doelzin data en uitwerkingen
    """
    result = get_doelzin_with_uitwerkingen(db, doelzin_id)
    
    if not result:
        return json.dumps({"error": "Doelzin niet gevonden"}, ensure_ascii=False)
    
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def stats() -> str:
    """Toon database statistieken.
    
    Returns:
        JSON met aantallen doelzinnen en uitwerkingen
    """
    doelzin_count = db(db.doelzin).count()
    uitwerking_count = db(db.uitwerking).count()
    doelzin_embedded = db(db.doelzin_embedding).count()
    uitwerking_embedded = db(db.uitwerking_embedding).count()
    
    return json.dumps({
        "doelzinnen": {
            "total": doelzin_count,
            "embedded": doelzin_embedded
        },
        "uitwerkingen": {
            "total": uitwerking_count,
            "embedded": uitwerking_embedded
        }
    }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run()
