# Troubleshooting Guide

Common issues en oplossingen voor SLO Search API deployment.

## Docker Deployment Issues

### 1. Nginx Keeps Restarting

**Symptoom:**
```bash
docker compose ps
# slo-nginx: Restarting (1) X seconds ago
```

**Oorzaken & Oplossingen:**

#### A. SSL Certificates Missing

```bash
# Check logs
docker compose logs nginx | grep -i ssl

# Error: "cannot load certificate /etc/nginx/ssl/selfsigned.crt"
# Fix:
bash generate_ssl.sh
docker compose restart nginx
```

#### B. API Container Not Running

```bash
# Check if API is up
docker compose ps api

# If not running, check logs:
docker compose logs api

# Restart:
docker compose restart api
sleep 10
docker compose restart nginx
```

#### C. SSL Files Permission Issues

```bash
# SSL files created by root, nginx can't read
sudo chown -R $USER:$USER ssl/
chmod 600 ssl/selfsigned.key
chmod 644 ssl/selfsigned.crt
docker compose restart nginx
```

### 2. Data Ingestion Fails - File Not Found

**Symptoom:**
```bash
docker compose exec api python ingest.py
# FileNotFoundError: [Errno 2] No such file or directory: '../curriculum-fo/data/doelzinnen.json'
```

**Oorzaak:** Data directory niet gemount in container.

**Oplossing A: Run ingestion locally (recommended):**
```bash
# Activate venv
source venv/bin/activate

# Point to Docker database
export DATABASE_URI="postgres://slo_user:YOUR_PASSWORD@localhost:5432/slo_search"

# Run ingestion
python ingest.py
```

**Oplossing B: Mount data directory:**

Update `docker-compose.yml`:
```yaml
api:
  volumes:
    - ../curriculum-fo:/data:ro
    - ./models:/app/models
```

Update `.env`:
```bash
DATA_DIR=/data
```

Then:
```bash
docker compose up -d
docker compose exec api python ingest.py
```

### 3. Database Authentication Failed

**Symptoom:**
```bash
psycopg2.OperationalError: password authentication failed for user "slo_user"
```

**Oorzaak:** Password mismatch tussen .env en database.

**Oplossing:**
```bash
# Check current password in .env
grep POSTGRES_PASSWORD .env

# Reset database with correct password
docker compose down -v  # WARNING: deletes all data
echo "POSTGRES_PASSWORD=your_secure_password" > .env
docker compose up -d
```

### 4. Container Won't Start

**Symptoom:**
```bash
docker compose ps
# Container status: Exited (1)
```

**Debug:**
```bash
# Check logs
docker compose logs <service-name>

# Check last 50 lines
docker compose logs --tail 50 <service-name>

# Follow logs live
docker compose logs -f <service-name>
```

**Common fixes:**
```bash
# Rebuild image (if code changed)
docker compose build <service-name>
docker compose up -d <service-name>

# Reset everything
docker compose down -v
docker compose up -d --build
```

### 5. API Slow to Start

**Symptoom:** API container shows "health: starting" for minutes.

**Oorzaak:** PyTorch en sentence-transformers model loading (~3GB).

**Verwacht gedrag:**
- First start: 1-2 minutes (downloading model)
- Subsequent starts: 30-60 seconds (loading from cache)

**Oplossing:**
```bash
# Just wait longer
docker compose logs -f api

# Look for: "Application startup complete"
```

**Speed up:**
```yaml
# Mount model cache in docker-compose.yml
api:
  volumes:
    - ~/.cache/torch:/root/.cache/torch:ro
    - ./models:/app/models
```

## Local Development Issues

### 6. PostgreSQL Won't Start

**Symptoom:**
```bash
psql: error: connection refused
```

**Check if running:**
```bash
sudo systemctl status postgresql
pg_lsclusters
```

**Start:**
```bash
# System PostgreSQL
sudo systemctl start postgresql

# Or use Docker
docker compose up -d postgres
```

### 7. Python Virtual Environment Issues

**Symptoom:**
```bash
python: command not found
# or: ModuleNotFoundError
```

**Oplossing:**
```bash
# Create venv if missing
python3 -m venv venv

# Activate
source venv/bin/activate

# Verify
which python  # Should show: /path/to/venv/bin/python

# Install dependencies
pip install -r requirements-dev.txt
```

### 8. pgvector Extension Not Available

**Symptoom:**
```sql
ERROR: extension "vector" is not available
```

**Oplossing - Ubuntu/Debian:**
```bash
# PostgreSQL 15
sudo apt install postgresql-15-pgvector

# PostgreSQL 16
sudo apt install postgresql-16-pgvector

# Restart
sudo systemctl restart postgresql
```

**Or use Docker:** (has pgvector built-in)
```bash
docker compose up -d postgres
```

## API Issues

### 9. Search Returns No Results

**Debug:**
```bash
# Check data is loaded
curl "http://localhost:8000/api/stats"

# Should show non-zero counts
# If zero: run ingestion

# Try simple query
curl "http://localhost:8000/api/search/doelzinnen?q=test&limit=1"
```

**If still no results:**
```bash
# Check database directly
docker compose exec postgres psql -U slo_user -d slo_search

# In psql:
SELECT COUNT(*) FROM doelzin;
SELECT COUNT(*) FROM doelzin_embedding;

# Check embedding vectors exist
SELECT COUNT(*) FROM doelzin_embedding WHERE embedding IS NOT NULL;
```

### 10. LLM Re-ranking Fails

**Symptoom:**
```json
{"llm_score": 5, "llm_reasoning": "Error: ..."}
```

**Debug:**
```bash
# Check API key configured
grep OPENAI_API_KEY .env

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Check logs
docker compose logs api | grep -i error
```

**Common issues:**
- API key not set: Add to .env
- Invalid key: Generate new at platform.openai.com
- Rate limited: Wait or upgrade plan
- Network issues: Check firewall/proxy

### 11. Slow Query Performance

**Symptoom:** Queries take >5 seconds without LLM.

**Check:**
```bash
# Check database query time
docker compose exec postgres psql -U slo_user -d slo_search

# In psql:
\timing on
SELECT COUNT(*) FROM doelzin_embedding;
```

**Optimize:**
```sql
-- Rebuild vector index with more lists
DROP INDEX doelzin_embedding_idx;
CREATE INDEX doelzin_embedding_idx ON doelzin_embedding 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 200);

VACUUM ANALYZE doelzin_embedding;
```

## Network Issues

### 12. Can't Access API from Host

**Symptoom:**
```bash
curl http://localhost:8000
# Connection refused
```

**Check:**
```bash
# Container running?
docker compose ps api

# Ports mapped correctly?
docker compose ps | grep 8000

# Try container IP directly
docker inspect slo-api | grep IPAddress
curl http://172.x.x.x:8000/api/stats
```

**Fix:**
```bash
# Restart with correct ports
docker compose up -d api

# Check it's listening
docker compose exec api netstat -tlnp | grep 8000
```

### 13. Nginx "upstream not found"

**Symptoom:**
```bash
nginx: [emerg] host not found in upstream "api:8000"
```

**Oorzaak:** DNS resolution failure in Docker network.

**Oplossing:**
```bash
# Ensure API starts before nginx
docker compose up -d postgres
docker compose up -d api
sleep 10  # Wait for API to be ready
docker compose up -d nginx
```

Or add to `docker-compose.yml`:
```yaml
nginx:
  depends_on:
    api:
      condition: service_healthy
```

## Production Issues

### 14. Out of Memory

**Symptoom:**
```bash
docker compose logs api
# Killed (OOM)
```

**Oplossing:**
```bash
# Increase container memory in docker-compose.yml:
api:
  deploy:
    resources:
      limits:
        memory: 6G

# Or reduce workers in Dockerfile:
CMD ["uvicorn", "api_fastapi:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### 15. Database Connection Pool Exhausted

**Symptoom:**
```bash
FATAL: remaining connection slots are reserved
```

**Oplossing:**
```bash
# Increase PostgreSQL max_connections
docker compose exec postgres psql -U postgres -c \
  "ALTER SYSTEM SET max_connections = 200;"

docker compose restart postgres

# Or reduce pool_size in models.py:
db = DAL(db_uri, migrate=True, pool_size=5)
```

## Quick Diagnostics

```bash
# Full stack health check
docker compose ps
docker compose logs --tail 20

# Database
docker compose exec postgres psql -U slo_user -d slo_search -c "SELECT version();"

# API
curl http://localhost:8000/api/stats

# Embeddings
curl "http://localhost:8000/api/search/doelzinnen?q=test&limit=1"

# LLM (if configured)
curl "http://localhost:8000/api/search?q=test&limit=1&rerank=true"
```

## Common Command Reference

```bash
# Restart everything
docker compose restart

# Rebuild and restart
docker compose up -d --build

# Reset database (deletes data!)
docker compose down -v
docker compose up -d

# View logs
docker compose logs -f api
docker compose logs --tail 50 postgres

# Shell into container
docker compose exec api bash
docker compose exec postgres psql -U slo_user -d slo_search

# Stop everything
docker compose down

# Remove everything including images
docker compose down -v --rmi all
```
