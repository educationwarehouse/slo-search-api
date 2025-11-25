# SLO Curriculum Search API

Semantic search API for Dutch curriculum data (Stichting Leerplan Ontwikkeling).

## Architecture

- **Database**: PostgreSQL + pgvector for vector similarity search
- **Embeddings**: `paraphrase-multilingual-MiniLM-L12-v2` (384-dim, Dutch optimized)
- **API**: py4web with pydal
- **Search**: Cosine similarity on title+description embeddings

## Deployment Options

Choose your deployment strategy:

### 1. Self-Hosted (Docker) — RECOMMENDED ✓

Full control, production-ready, ~€6/month.

```bash
# Quick start
cp .env.docker .env
bash generate_ssl.sh
docker-compose up -d
docker-compose exec api python ingest.py

# Production-ready with SSL, rate limiting, backups
```

**See:** [SELFHOST.md](SELFHOST.md) — Complete guide with monitoring, scaling, backups

### 2. Local Development (py4web)

For development and testing.

```bash
pip install -r requirements-dev.txt
createdb slo_search
python -c "from models import get_db; get_db()"
python ingest.py
py4web run . --port 8000
```

### 3. Vercel Serverless (FastAPI)

Serverless deployment with external database.

```bash
# Requires external PostgreSQL (Supabase/Neon)
export DATABASE_URI="postgres://..."
python ingest.py
vercel --prod
```

**See:** [VERCEL.md](VERCEL.md) — Serverless deployment guide

## Quick Comparison

| Feature | Self-Hosted | Vercel | Local |
|---------|-------------|--------|-------|
| **Control** | Full | Limited | Full |
| **Cost** | ~€6/mo | Free tier / $45+/mo | Free |
| **Scaling** | Manual | Auto | N/A |
| **Setup** | Docker | Git push | Manual |
| **Best for** | Production | MVP/Demo | Development |

## API Endpoints

### Combined Search (Recommended)
```bash
GET/POST /api/search?q=<query>&limit=10&weight=0.7
```
Searches both doelzinnen and uitwerkingen, weighted scoring.

### Doelzinnen Only
```bash
GET/POST /api/search/doelzinnen?q=<query>&limit=10&threshold=0.0
```

### Uitwerkingen Only
```bash
GET/POST /api/search/uitwerkingen?q=<query>&limit=10&threshold=0.0
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

## Usage Examples

```python
import requests

# Search for lesson match
response = requests.get(
    'http://localhost:8000/api/search',
    params={'q': 'leerlingen leren over fotosynthese', 'limit': 5}
)

results = response.json()['results']
for r in results:
    print(f"{r['title']} ({r['similarity']:.3f})")
    print(f"  {r['description']}")
```

```bash
# cURL
curl "http://localhost:8000/api/search?q=fotosynthese&limit=3"

# JSON POST
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "fotosynthese", "limit": 3}'
```

## Parameters

- `q`/`query`: Search text (required)
- `limit`: Max results (default: 10)
- `threshold`: Min similarity score 0-1 (default: 0.0)
- `weight`: Doelzin vs uitwerking weight 0-1 (default: 0.7)

## Response Format

```json
{
  "query": "fotosynthese",
  "count": 3,
  "results": [
    {
      "id": 123,
      "fo_id": "uuid",
      "title": "Eindterm X",
      "description": "...",
      "prefix": "A.1",
      "soort": "eindterm",
      "similarity": 0.856,
      "doelzin_similarity": 0.82,
      "uitwerking_similarity": 0.91
    }
  ]
}
```

## Tasks (via tasks.py)

```bash
python tasks.py db_create   # Create database
python tasks.py db_reset    # Drop and recreate
python tasks.py ingest      # Load data
python tasks.py dev         # Start dev server
python tasks.py test        # Run test queries
```

## Database Schema

**doelzin**: Learning goals (2642 records)
- fo_id, title, description, prefix, soort, ce, se, status, uitwerking_ids

**uitwerking**: Elaborations (10231 records)
- fo_id, title, description, prefix, niveau_ids, status

**doelzin_embedding**: Vector embeddings for doelzinnen
- embedding (vector(384)), embedding_model

**uitwerking_embedding**: Vector embeddings for uitwerkingen
- embedding (vector(384)), embedding_model

## Tuning

- **Model**: Change in `embeddings.py` (default: multilingual-MiniLM)
- **Vector index**: Adjust `lists` parameter in `models.py` (default: 100)
- **Scoring weight**: Adjust `doelzin_weight` in combined search (default: 0.7)
