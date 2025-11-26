"""MCP Server for SLO Curriculum Search - API Proxy Version.

Proxies requests to the FastAPI server instead of direct database access.
"""
from fastmcp import FastMCP
import requests
import json
import os

# Initialize MCP server
mcp = FastMCP("slo-curriculum-search")

# API base URL (configurable via environment)
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")


@mcp.tool()
def search(
    query: str,
    limit: int = 100,
    threshold: float = 0.4,
    weight: float = 0.7,
    rerank: bool = True
) -> str:
    """Search SLO curriculum (doelzinnen and uitwerkingen).
    
    Args:
        query: Search query
        limit: Max results (default: 100)
        threshold: Min similarity 0-1 (default: 0.4)
        weight: Doelzin weight 0-1 (default: 0.7)
        rerank: Use LLM re-ranking (default: True)
    
    Returns:
        JSON with search results
    """
    response = requests.get(f"{API_BASE}/search", params={
        "q": query,
        "limit": limit,
        "threshold": threshold,
        "weight": weight,
        "rerank": str(rerank).lower()
    }, timeout=120)
    response.raise_for_status()
    return json.dumps(response.json(), indent=2, ensure_ascii=False)


@mcp.tool()
def search_goals(
    query: str,
    limit: int = 10,
    threshold: float = 0.0
) -> str:
    """Search only in learning goals (doelzinnen).
    
    Args:
        query: Search query
        limit: Max results
        threshold: Min similarity
    
    Returns:
        JSON with results
    """
    response = requests.get(f"{API_BASE}/search/doelzinnen", params={
        "q": query,
        "limit": limit,
        "threshold": threshold
    }, timeout=60)
    response.raise_for_status()
    return json.dumps(response.json(), indent=2, ensure_ascii=False)


@mcp.tool()
def search_elaborations(
    query: str,
    limit: int = 10,
    threshold: float = 0.0
) -> str:
    """Search only in elaborations (uitwerkingen).
    
    Args:
        query: Search query
        limit: Max results
        threshold: Min similarity
    
    Returns:
        JSON with results
    """
    response = requests.get(f"{API_BASE}/search/uitwerkingen", params={
        "q": query,
        "limit": limit,
        "threshold": threshold
    }, timeout=60)
    response.raise_for_status()
    return json.dumps(response.json(), indent=2, ensure_ascii=False)


@mcp.tool()
def get_goal(doelzin_id: int) -> str:
    """Get a specific learning goal with all its elaborations.
    
    Args:
        doelzin_id: Learning goal ID
    
    Returns:
        JSON with goal and elaborations
    """
    response = requests.get(f"{API_BASE}/doelzin/{doelzin_id}", timeout=30)
    response.raise_for_status()
    return json.dumps(response.json(), indent=2, ensure_ascii=False)


@mcp.tool()
def stats() -> str:
    """Get database statistics.
    
    Returns:
        JSON with counts
    """
    response = requests.get(f"{API_BASE}/stats", timeout=10)
    response.raise_for_status()
    return json.dumps(response.json(), indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # Run the MCP server using stdio transport
    mcp.run()
