# 🚀 START HERE - SLO Curriculum Search API

Quick guide om te bepalen welke documentatie je nodig hebt.

## Ik wil...

### → Snel testen / Development
**Lees:** [QUICKSTART.md](QUICKSTART.md)
```bash
pip install -r requirements-dev.txt
python ingest.py
python api_fastapi.py &
curl "http://localhost:8000/api/search?q=test"
```
**Tijd:** 15 minuten

---

### → Production deployment op eigen server
**Lees:** [SELFHOST.md](SELFHOST.md) + [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
```bash
cp .env.example .env
bash generate_ssl.sh
docker compose up -d
# Data laden: zie SELFHOST.md stap 6
```
**Tijd:** 30 minuten
**Kosten:** €5-10/maand (VPS)

---

### → Serverless deployment (Vercel)
**Lees:** [VERCEL.md](VERCEL.md)
```bash
# 1. Setup Supabase/Neon (external DB)
# 2. python ingest.py (local → external DB)
# 3. vercel --prod
```
**Tijd:** 20 minuten
**Kosten:** Gratis tier / €45+ paid

---

### → LLM re-ranking toevoegen
**Lees:** [LLM_RERANKING.md](LLM_RERANKING.md)
```bash
echo "OPENAI_API_KEY=sk-..." >> .env
# Add ?rerank=true to search queries
```
**Extra kosten:** ~€0.001 per query

---

### → Problemen oplossen
**Lees:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**Top 5 most common issues:**
1. Nginx crasht → SSL certificates: `bash generate_ssl.sh`
2. Data niet geladen → Check SELFHOST.md stap 6 (mount issue!)
3. API reageert niet → Wacht 30-60s voor PyTorch loading
4. Search returns 0 → Run `python ingest.py`
5. LLM fails → Check OPENAI_API_KEY in .env

---

## Project Structure
## Project Structure
slo-search/
├── 📘 START_HERE.md           ← You are here!
│
├── 🚀 Quick Start
│   ├── QUICKSTART.md          # 5-min local test
│   └── DEPLOYMENT_CHECKLIST.md # Step-by-step checklists
│
├── 📖 Deployment Guides  
│   ├── SELFHOST.md            # Docker production (recommended)
│   ├── VERCEL.md              # Serverless deployment
│   └── LLM_RERANKING.md       # Add AI re-ranking
│
├── 🔧 Reference
│   ├── README.md              # Overview + API docs
│   ├── TROUBLESHOOTING.md     # Problem solving
│   └── SETUP.md               # Detailed local setup
│
└── 💻 Code
    ├── api_fastapi.py         # Main API (FastAPI)
    ├── models.py              # Database schema
    ├── search.py              # Vector search
    ├── search_llm.py          # LLM re-ranking
    ├── embeddings.py          # Embedding generation
    ├── ingest.py              # Data loader
    └── config.py              # Configuration

## Quick Reference

**API Endpoints:**
```bash
# Stats
curl http://localhost:8000/api/stats

# Basic search
curl "http://localhost:8000/api/search?q=QUERY&limit=5"

# With LLM re-ranking
curl "http://localhost:8000/api/search?q=QUERY&rerank=true"

# Get full doelzin
curl http://localhost:8000/api/doelzin/123
```

**Docker Commands:**
```bash
docker compose up -d        # Start
docker compose ps           # Status
docker compose logs -f api  # Logs
docker compose restart      # Restart
docker compose down         # Stop
```

**Data Management:**
```bash
python ingest.py            # Load data
curl .../api/stats          # Verify
```

## Deployment Matrix

| Scenario | Use | Documentation | Time | Cost |
|----------|-----|---------------|------|------|
| **Development** | Testing locally | QUICKSTART.md | 15min | €0 |
| **Self-Hosted** | Production control | SELFHOST.md | 30min | €6/mo |
| **Vercel** | Serverless/demo | VERCEL.md | 20min | Free/€45 |

## Known Issues & Workarounds

1. **Nginx SSL crash** → Run `bash generate_ssl.sh` before `docker compose up`
2. **Data ingestion in Docker** → Run locally: `export DATABASE_URI=... && python ingest.py`
3. **Slow API startup** → Normal (PyTorch loading), wait 60s
4. **No search results** → Data not loaded, check with `/api/stats`

## Success Criteria

Your deployment is successful when:
```bash
✓ curl http://your-api/api/stats
  # Returns: {"doelzinnen": {"total": 2642, ...}}

✓ curl "http://your-api/api/search?q=rekenen&limit=3"
  # Returns: {"count": 3, "results": [...]}

✓ Results have similarity scores > 0.3 for relevant queries
✓ (Optional) LLM re-ranking returns llm_score and llm_reasoning
```

## Need Help?

1. **Check:** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. **Read:** Relevant deployment guide
3. **Verify:** Run health-check.sh
4. **Debug:** Check logs with `docker compose logs -f`

## Next Steps After Deployment

- [ ] Test alle use cases (zie DEPLOYMENT_CHECKLIST.md)
- [ ] Setup monitoring/alerting
- [ ] Configure backups
- [ ] Document custom configurations
- [ ] (Optional) Add caching layer
- [ ] (Optional) Setup CI/CD

---

**You're ready to deploy!** Pick your path above and follow the guide. 🎯
