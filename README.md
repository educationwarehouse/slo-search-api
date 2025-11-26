# SLO Curriculum Search API

Semantic search API for Dutch curriculum data (Stichting Leerplan Ontwikkeling).

## Architecture

- **Database**: SQLite or PostgreSQL (configured via `DATABASE_URI`)
- **Embeddings**: Ollama `nomic-embed-text` (768-dim)
- **API**: FastAPI
- **Search**: Hybrid approach:
  - Numpy-based cosine similarity
  - Query-boosted cosine (lexical + semantic)
  - Optional LLM re-ranking (via Ollama)

## Prerequisites

- Docker & Docker Compose
- Ollama running locally with `nomic-embed-text` model
- Curriculum data in `../curriculum-fo/data/`

## Deployment Options

This project provides two interfaces:
- **FastAPI REST API** - HTTP endpoints for web integration
- **MCP Server** - Model Context Protocol for AI assistants (Claude, etc.)

See [MCP.md](MCP.md) for MCP server documentation.

## Quick Start

1. **Pull the embedding model:**
   ```bash
   ollama pull nomic-embed-text
   ```

2. **Start the API:**
   ```bash
   docker compose up -d
   ```

3. **Ingest data (first time only):**
   ```bash
   docker compose exec api python ingest.py
   # Takes ~5 minutes to generate 12,873 embeddings
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

**SQLite**: Persists at `./slo_search.db` (~205MB)
**PostgreSQL**: Configure connection in `.env`

## Development

Code is mounted, changes are live (no rebuild needed):

```bash
# Edit code locally
vim search.py

# Restart to reload Python modules
docker compose restart api
```

## Configuration

Edit `docker-compose.yml` or `.env`:
- `DATABASE_URI`: Database connection (SQLite: `sqlite:///app/slo_search.db` or Postgres: `postgres://user:pass@host:port/db`)
- `EMBEDDING_MODEL`: Ollama model name (default: `nomic-embed-text`)
- `OLLAMA_HOST`: Ollama API URL (default: `http://localhost:11434`)
- `OLLAMA_MODEL`: LLM model for re-ranking (default: `llama3.2:latest`)
- `DATA_DIR`: Path to curriculum data

## Backup

```bash
cp slo_search.db slo_search.db.backup
```

## Architecture Decisions

**Database: SQLite or PostgreSQL**
- SQLite: Simple deployment, no database server, ~205MB (data + embeddings)
- PostgreSQL: Better for concurrent writes, production deployments
- Both work equally well for read-heavy search (12k records)

**Why Ollama?**
- No heavy ML dependencies (torch, transformers)
- Easy model management
- Local inference
- Great multilingual embeddings

**Why host networking?**
- Container can access localhost Ollama
- No port forwarding complexity
- Direct communication with host services
