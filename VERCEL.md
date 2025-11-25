# Vercel Deployment Guide

## Architecture

**Two-part system:**
1. **Local/CI**: Data ingestion + embedding generation → External PostgreSQL
2. **Vercel**: FastAPI serverless API → Read-only vector similarity queries

**Why this split?**
- Vercel has 50MB function limit (sentence-transformers is ~500MB)
- Embedding generation is compute-intensive (better suited for batch jobs)
- Vercel excels at serving fast API queries

## Prerequisites

1. **External PostgreSQL with pgvector** (choose one):
   - [Supabase](https://supabase.com) (recommended, free tier available)
   - [Railway](https://railway.app)
   - [Neon](https://neon.tech)
   - [Vercel Postgres](https://vercel.com/docs/storage/vercel-postgres)

2. **Vercel account** (free tier works)

## Setup Steps

### 1. Setup External Database

**Using Supabase (recommended):**

```bash
# 1. Create project at supabase.com
# 2. Enable pgvector in SQL Editor:
CREATE EXTENSION vector;

# 3. Get connection string from Settings → Database
# Format: postgres://postgres:[password]@db.[project].supabase.co:5432/postgres
```

### 2. Run Local Ingestion

```bash
# Install full dependencies (includes sentence-transformers)
pip install -r requirements-dev.txt

# Configure database
export DATABASE_URI="postgres://postgres:[password]@db.[project].supabase.co:5432/postgres"

# Run ingestion (generates embeddings and populates DB)
python ingest.py
```

This creates tables, loads curriculum data, and generates embeddings (~5-10 min).

### 3. Deploy to Vercel

**Via CLI:**

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Add environment variable
vercel env add DATABASE_URI

# Paste your connection string, select Production

# Deploy
vercel --prod
```

**Via Web UI:**

```bash
# 1. Push to GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/slo-search.git
git push -u origin main

# 2. Import project at vercel.com/new
# 3. Configure:
#    - Framework Preset: Other
#    - Build Command: (leave empty)
#    - Output Directory: (leave empty)
#    
# 4. Add Environment Variables:
#    DATABASE_URI = postgres://...
#
# 5. Deploy
```

### 4. Test Deployment

```bash
# Get your deployment URL from Vercel
curl "https://your-app.vercel.app/api/search?q=fotosynthese&limit=3"
```

## Configuration

### Required Environment Variables

Set in Vercel → Project → Settings → Environment Variables:

| Variable | Example | Required |
|----------|---------|----------|
| `DATABASE_URI` | `postgres://user:pass@host:5432/db` | Yes |
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | No* |

*Not used on Vercel (no embedding generation), but kept for consistency.

### Vercel Configuration

`vercel.json` settings:
- **Region**: `ams1` (Amsterdam, closest to Netherlands)
- **Runtime**: Python serverless functions
- **Routes**: All traffic → FastAPI handler

## Updating Data

To update curriculum data:

```bash
# Run locally with production DB
export DATABASE_URI="postgres://..."
python ingest.py

# No Vercel redeployment needed - changes are immediate
```

## Architecture Details

### What runs on Vercel:
- ✅ FastAPI API endpoints
- ✅ Vector similarity search (SQL queries)
- ✅ Database connection pooling
- ❌ No embedding generation
- ❌ No model downloads

### What runs locally:
- ✅ Data ingestion
- ✅ Embedding generation (sentence-transformers)
- ✅ Database schema creation
- ✅ Model downloads/caching

## Cost Estimates

**Free tier:**
- Vercel: 100GB bandwidth/month, 100 function invocations/day
- Supabase: 500MB database, 2GB bandwidth/month
- **Total**: $0/month for moderate use

**Paid:**
- Vercel Pro: $20/month (unlimited functions)
- Supabase Pro: $25/month (8GB database)

## Troubleshooting

### "Module not found" errors

Ensure `requirements-vercel.txt` is used (not `requirements.txt` or `requirements-dev.txt`):

```json
{
  "builds": [
    {
      "src": "api_fastapi.py",
      "use": "@vercel/python",
      "config": {
        "pythonRequirements": "requirements-vercel.txt"
      }
    }
  ]
}
```

### Cold start slowness

First request after inactivity takes longer (~2-5s). Solutions:
- Use Vercel Pro (reduced cold starts)
- Implement connection pooling (already in models.py)
- Add warming endpoint (periodic pings)

### Database connection limits

Free tier Supabase: 60 connections. If exceeded:
- Reduce `pool_size` in `models.py`
- Use connection pooler (pgBouncer)
- Upgrade Supabase tier

## Monitoring

```bash
# Vercel logs
vercel logs

# Database monitoring
# → Supabase dashboard → Database → Connection pooling
```

## Local Development

For local testing with production data:

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Use production DB
export DATABASE_URI="postgres://..."

# Run FastAPI locally
python api_fastapi.py

# Test
curl "http://localhost:8000/api/search?q=test"
```

## Alternatives to Vercel

This FastAPI app works on any serverless platform:
- **Railway**: Auto-deploy from Git, includes PostgreSQL
- **Render**: Free static sites + background workers
- **Fly.io**: Global edge deployment
- **Google Cloud Run**: Containerized deployment

Just ensure external PostgreSQL with pgvector is accessible.
