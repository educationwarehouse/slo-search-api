# SLO Curriculum Search API

Semantic search API for Dutch curriculum data (Stichting Leerplan Ontwikkeling).

## Architecture

- **Database**: PostgreSQL with pgvector extension
- **Embeddings**: OpenRouter API (OpenAI-compatible models)
- **API**: FastAPI
- **Search**: Hybrid approach:
  - Numpy-based cosine similarity
  - Query-boosted cosine (lexical + semantic)
  - Optional LLM re-ranking (via OpenRouter)

## Prerequisites

- Docker & Docker Compose
- OpenRouter API key
- Traefik reverse proxy with broker network (optional, for production)

Clone the curriculum data repository as sibling directory:
git clone https://github.com/slonl/curriculum-fo.git ../curriculum-fo

## Deployment Options

This project provides two interfaces:
- **FastAPI REST API** - HTTP endpoints for web integration
- **MCP Server** - Model Context Protocol for AI assistants (Claude, etc.)

See [MCP.md](MCP.md) for MCP server documentation.

## URLs & Domains

When deployed with Traefik, services are available at:

**Current domains:**
- REST API: `{PROJECT}-rest-api.{HOSTINGDOMAIN}`
- MCP Server: `{PROJECT}-mcp-api.{HOSTINGDOMAIN}`

**Legacy domains (backward compatibility):**
- REST API: `slo-search-api.{HOSTINGDOMAIN}`
- MCP Server: `slo-search-mcp.{HOSTINGDOMAIN}`

Example with `PROJECT=slo-search` and `HOSTINGDOMAIN=example.com`:
- REST API: `https://slo-search-rest-api.example.com` (or `https://slo-search-api.example.com`)
- MCP Server: `https://slo-search-mcp-api.example.com` (or `https://slo-search-mcp.example.com`)

Both domain patterns are supported simultaneously for backward compatibility.

## Quick Start

1. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENROUTER_API_KEY
   ```

2. **Start the API:**
   ```bash
   docker compose up -d
   ```

3. **Ingest data (first time only):**
   ```bash
   docker compose exec rest-api python ingest.py
   # Generates 12,873 embeddings via OpenRouter API
   ```

4. **Test the API:**
   ```bash
   # Simple search
   curl "http://localhost:8000/api/search?q=fotosynthese&limit=5"
   
   # With custom parameters
   curl "http://localhost:8000/api/search?q=fotosynthese&limit=10&threshold=0.7&rerank=false"
   ```

## API Endpoints

### Combined Search (Recommended)
```bash
GET/POST /api/search?q=<query>&limit=100&threshold=0.6&weight=0.7&rerank=true
```
Searches both doelzinnen and uitwerkingen with weighted scoring, LLM re-ranking, and query-boosted cosine enhancement.

### Doelzinnen Only
```bash
GET/POST /api/search/doelzinnen?q=<query>&limit=10
```

### Uitwerkingen Only
```bash
GET/POST /api/search/uitwerkingen?q=<query>&limit=10
```

### Get Full Doelzin
```bash
GET /api/doelzin/<id>
```
Returns doelzin with all linked uitwerkingen.

### Stats
```bash
GET /api/stats
```

## Response Format

```json
{
  "query": "fotosynthese",
  "count": 3,
  "results": [
    {
      "id": 1600,
      "fo_id": "87f8e2b1-f4ec-4062-b514-281c3198bfc3",
      "title": "Eindterm 15",
      "description": "De leerling gebruikt concepten over ecosystemen...",
      "prefix": "15",
      "soort": "eindterm",
      "similarity": 0.547,
      "doelzin_similarity": 0.472,
      "uitwerking_similarity": 0.722
    }
  ],
  "reranked": true,
  "enhanced": true
}
```

## Parameters

- `q`/`query`: Search text (required)
- `limit`: Max results (default: 100)
- `threshold`: Min similarity 0-1 (default: 0.6)
- `weight`: Doelzin weight 0-1 (default: 0.7)
- `rerank`: Use LLM re-ranking (default: true)

## Database

The database contains:
- **2,642 doelzinnen** (learning goals)
- **10,231 uitwerkingen** (elaborations)
- **Embeddings** stored as JSON arrays (or binary for PostgreSQL)

Configure PostgreSQL connection in `.env` or use default settings from `docker-compose.yml`.

## Development

Code is mounted, changes are live (no rebuild needed):

```bash
# Edit code locally
vim search.py

# Restart to reload Python modules
docker compose restart api
```

## Configuration

Edit `.env` or `docker-compose.yml`:
- `OPENROUTER_API_KEY`: Your OpenRouter API key (required)
- `DATABASE_URI`: PostgreSQL connection string (e.g., `postgres://user:pass@host:port/db`)
- `EMBEDDING_MODEL`: OpenRouter embedding model (default: `openai/text-embedding-3-small`)
- `LLM_MODEL`: LLM model for re-ranking (default: `openai/gpt-4o-mini`)
- `DATA_DIR`: Path to curriculum data

## Backup

Use standard PostgreSQL backup tools:
```bash
docker compose exec postgres pg_dump -U slo slo_search > backup.sql
```

## Architecture Decisions

**Database: PostgreSQL with pgvector**
- Production-ready with concurrent access support
- Efficient vector operations via pgvector extension
- Scalable for growing datasets beyond 12k records

**Why OpenRouter?**
- No local model management required
- Access to best-in-class embedding models (OpenAI, etc.)
- Flexible LLM selection for re-ranking
- OpenAI-compatible API (easy migration path)
- Pay-per-use pricing (no infrastructure overhead)
