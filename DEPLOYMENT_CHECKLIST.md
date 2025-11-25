# Deployment Checklist

Pre-flight checklists voor elk deployment scenario.

## 🏠 Local Development

**Prerequisites:**
- [ ] Python 3.9+
- [ ] PostgreSQL 14+ OR Docker
- [ ] `git clone https://github.com/slonl/curriculum-fo ../curriculum-fo`

**Setup:**
```bash
- [ ] python3 -m venv venv && source venv/bin/activate
- [ ] pip install -r requirements-dev.txt
- [ ] cp .env.example .env && nano .env
```

**Database:**
```bash
- [ ] createdb slo_search (or: docker compose up -d postgres)
- [ ] python -c "from models import get_db; get_db()"
```

**Data:**
```bash
- [ ] python ingest.py  # ~5-10 min
- [ ] Verify: curl http://localhost:8000/api/stats
```

**Run:**
```bash
- [ ] python api_fastapi.py &
- [ ] Test: curl "http://localhost:8000/api/search?q=test"
```

---

## 🐳 Self-Hosted Docker

**Prerequisites:**
- [ ] Docker + Compose
- [ ] Domain (optional)
- [ ] Ports 80/443 open
- [ ] Data: `git clone https://github.com/slonl/curriculum-fo ../curriculum-fo`

**Setup:**
```bash
- [ ] cp .env.example .env
- [ ] nano .env  # Set POSTGRES_PASSWORD
- [ ] bash generate_ssl.sh  # Dev SSL
```

**Deploy:**
```bash
- [ ] docker compose build
- [ ] docker compose up -d
- [ ] docker compose ps  # All healthy?
```

**Data (choose one):**
```bash
Option A - Local to Docker DB:
- [ ] source venv/bin/activate
- [ ] export DATABASE_URI="postgres://slo_user:PASS@localhost:5432/slo_search"
- [ ] python ingest.py

Option B - In container:
- [ ] Mount data: ../curriculum-fo:/data:ro in docker-compose.yml
- [ ] docker compose exec api python ingest.py
```

**Verify:**
```bash
- [ ] curl http://localhost:8000/api/stats  # 2642 doelzinnen?
- [ ] curl "http://localhost:8000/api/search?q=test"
```

**Production:**
- [ ] Rotate POSTGRES_PASSWORD
- [ ] Setup Let's Encrypt SSL
- [ ] Firewall: sudo ufw allow 80,443/tcp
- [ ] Backups: crontab backup.sh
- [ ] Monitor: docker compose logs -f

---

## ☁️ Vercel Serverless

**Setup External DB:**
- [ ] Create Supabase/Neon project
- [ ] Enable pgvector: `CREATE EXTENSION vector;`
- [ ] Copy connection string

**Load Data:**
```bash
- [ ] pip install -r requirements-dev.txt
- [ ] export DATABASE_URI="postgres://..."
- [ ] python ingest.py
```

**Deploy:**
```bash
Via CLI:
- [ ] npm i -g vercel && vercel login
- [ ] vercel env add DATABASE_URI
- [ ] vercel env add OPENAI_API_KEY (optional)
- [ ] vercel --prod

Via Web:
- [ ] Push to GitHub
- [ ] Import at vercel.com/new
- [ ] Add DATABASE_URI env var
- [ ] Deploy
```

**Verify:**
```bash
- [ ] curl "https://your-app.vercel.app/api/stats"
- [ ] curl "https://your-app.vercel.app/api/search?q=test"
```

---

## Post-Deployment (All)

**Testing:**
- [ ] Basic: `curl ".../api/search?q=rekenen&limit=3"`
- [ ] Combined: `curl ".../api/search?q=democratie"`
- [ ] Details: `curl ".../api/doelzin/1"`
- [ ] LLM: `curl ".../api/search?q=test&rerank=true"` (if enabled)

**Security:**
- [ ] Rotate exposed API keys (if any shared!)
- [ ] Firewall configured
- [ ] HTTPS enabled
- [ ] Strong database password

**Optimization:**
- [ ] Monitor response times
- [ ] Check DB connection pool
- [ ] Test vector index performance
- [ ] Consider query caching

**Backup:**
- [ ] Automated DB backups configured
- [ ] Test restore procedure
- [ ] Document backup schedule

---

## Health Check Script

Save as `health-check.sh`:
```bash
#!/bin/bash
API_URL="${1:-http://localhost:8000}"

echo "=== Health Check: $API_URL ==="

# API responding
curl -sf "$API_URL/api/stats" >/dev/null && echo "✓ API responding" || echo "✗ API down"

# Data loaded
COUNT=$(curl -s "$API_URL/api/stats" | grep -o '"total": [0-9]*' | head -1 | awk -F': ' '{print $2}')
[ "$COUNT" = "2642" ] && echo "✓ Full data (2642)" || echo "⚠ Data: $COUNT/2642"

# Search works
RESULTS=$(curl -s "$API_URL/api/search?q=test&limit=1" | grep -o '"count": [0-9]*' | awk -F': ' '{print $2}')
[ "$RESULTS" -gt 0 ] && echo "✓ Search works" || echo "✗ Search fails"

# LLM (if configured)
if curl -s "$API_URL/api/search?q=test&rerank=true" | grep -q llm_score; then
  echo "✓ LLM re-ranking active"
fi

echo "=== Done ==="
```

Run: `bash health-check.sh [http://your-api-url]`

---

## Emergency Procedures

**Complete Reset:**
```bash
docker compose down -v --rmi all
rm -rf databases/ ssl/ api.log venv/
# Then follow checklist from top
```

**Quick Rollback:**
```bash
docker compose down
gunzip -c backup.sql.gz | docker compose exec -T postgres psql -U slo_user slo_search
docker compose up -d
```

**Re-ingest Data:**
```bash
export DATABASE_URI="postgres://..."
python ingest.py  # Overwrites existing
```
