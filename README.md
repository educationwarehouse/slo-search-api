# SLO Curriculum Search API

Semantic search API for Dutch curriculum data (Stichting Leerplan Ontwikkeling).

## Architecture

- **Database**: SQLite (205MB, file-based)
- **Embeddings**: Ollama `nomic-embed-text` (768-dim)
- **API**: FastAPI
- **Search**: Numpy-based cosine similarity

## Prerequisites

- Docker & Docker Compose
- Ollama running locally with `nomic-embed-text` model
- Curriculum data in `../curriculum-fo/data/`

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
   curl "http://localhost:8000/api/search?q=fotosynthese&limit=3"
   ```

## API Endpoints

### Combined Search (Recommended)
```bash
GET/POST /api/search?q=<query>&limit=10&weight=0.7
```
Searches both doelzinnen and uitwerkingen with weighted scoring.

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
  ]
}
```

## Parameters

- `q`/`query`: Search text (required)
- `limit`: Max results (default: 10)
- `threshold`: Min similarity 0-1 (default: 0.0)
- `weight`: Doelzin weight 0-1 (default: 0.7)

## Database

The SQLite database (`slo_search.db`) contains:
- **2,642 doelzinnen** (learning goals)
- **10,231 uitwerkingen** (elaborations)
- **Embeddings** stored as JSON arrays

Database persists on host at `./slo_search.db` (205MB).

## Development

Code is mounted, changes are live (no rebuild needed):

```bash
# Edit code locally
vim search.py

# Restart to reload Python modules
docker compose restart api
```

## Configuration

Edit `docker-compose.yml`:
- `EMBEDDING_MODEL`: Ollama model name
- `DATABASE_URI`: Database path
- `OLLAMA_HOST`: Ollama API URL

## Backup

```bash
cp slo_search.db slo_search.db.backup
```

## Architecture Decisions

**Why SQLite?**
- Simple deployment (no database server)
- Fast for read-heavy workloads
- 205MB total size (data + embeddings)
- Perfect for this use case (12k records)

**Why Ollama?**
- No heavy ML dependencies (torch, transformers)
- Easy model management
- Local inference
- Great multilingual embeddings

**Why host networking?**
- Container can access localhost Ollama
- No port forwarding complexity
- Direct communication with host services
