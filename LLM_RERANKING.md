# LLM Re-ranking Feature

Verbeter zoekresultaten met intelligent herordenen via LLM's.

## Hoe het werkt

**Two-stage retrieval:**
1. **Stage 1** (vector search): Snelle kandidaatselectie via embeddings
2. **Stage 2** (LLM re-rank): Diepe contextbegrip voor beste matches

## Setup

### OpenAI (Recommended - Goedkoop & Snel)

```bash
# Install dependencies
pip install openai

# Configure
echo "LLM_PROVIDER=openai" >> .env
echo "OPENAI_API_KEY=sk-your-key-here" >> .env
echo "OPENAI_MODEL=gpt-4o-mini" >> .env
```

**Cost:** ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens

### Anthropic Claude

```bash
pip install anthropic

echo "LLM_PROVIDER=anthropic" >> .env
echo "ANTHROPIC_API_KEY=sk-ant-your-key" >> .env
echo "ANTHROPIC_MODEL=claude-3-5-haiku-20241022" >> .env
```

**Cost:** ~$1.00 per 1M input tokens, ~$5.00 per 1M output tokens

### Ollama (Lokaal - Gratis)

```bash
# Install Ollama first: https://ollama.ai
ollama pull llama3.2

echo "LLM_PROVIDER=ollama" >> .env
echo "OLLAMA_URL=http://localhost:11434" >> .env
echo "OLLAMA_MODEL=llama3.2" >> .env
```

**Cost:** Gratis, maar langzamer

## Gebruik

### API Call met Re-ranking

```bash
# Zonder LLM (standaard - snel)
curl "http://localhost:8000/api/search?q=democratie&limit=5"

# Met LLM re-ranking (beter maar langzamer)
curl "http://localhost:8000/api/search?q=democratie&limit=5&rerank=true"
```

### Response Format

```json
{
  "query": "democratie weerbaarheid",
  "count": 5,
  "results": [
    {
      "id": 123,
      "title": "Eindterm 8",
      "description": "...",
      "similarity": 0.56,
      "llm_score": 9.2,
      "llm_reasoning": "Perfect match: behandelt democratische waarden en weerbaarheid",
      "llm_match": "democratische waarden, grondrechten",
      "original_rank": 3
    }
  ],
  "reranked": true
}
```

### Python Client

```python
import requests

# Basis search
response = requests.get(
    'http://localhost:8000/api/search',
    params={'q': 'democratie 1600 verslag', 'limit': 5, 'rerank': True}
)

for result in response.json()['results']:
    print(f"LLM Score: {result['llm_score']}/10")
    print(f"Match: {result['title']}")
    print(f"Reasoning: {result['llm_reasoning']}")
    print(f"Was rank #{result['original_rank']}, now rank #1\n")
```

## Performance

**Without LLM:**
- Response time: ~50ms
- Cost: €0
- Accuracy: Goed voor exacte matches

**With LLM (OpenAI gpt-4o-mini):**
- Response time: ~2-5s (voor 10 resultaten)
- Cost: ~€0.001 per query
- Accuracy: Excellent voor complexe queries met context

## Best Practices

1. **Use re-ranking voor complexe queries:**
   - ✅ "leerlingen maken verslag over democratie in 1600"
   - ❌ "rekenen" (te simpel, vector search is voldoende)

2. **Batch size beperken:**
   - Default: 10 resultaten re-ranked
   - Voor kostenbeheersing en snelheid

3. **Cache results:**
   - Overweeg caching voor veelvoorkomende queries

4. **Monitor costs:**
   - OpenAI dashboard: platform.openai.com
   - Track usage per query

## Voorbeeld: Docent Use Case

**Query:** "leerlingen onderzoeken weerbaarheid democratie, vergelijken 1600 met nu, maken verslag"

**Zonder LLM:**
Results: mediocre matches op tekst-niveau
- [0.40] Generic match zonder context begrip
- [0.38] Mogelijk irrelevant
- [0.35] Tangentieel gerelateerd

**Met LLM Re-ranking:**
Results: intelligente prioritering
- [9/10] "Democratische waarden in grondrechten" - Perfect match: behandelt democratie & weerbaarheid
- [8/10] "Historische doorwerking fenomenen" - Sterk: vergelijkt tijdsperioden zoals gevraagd  
- [7/10] "Onderzoek & rapportage" - Relevant: verslaglegging aspect

## Real-World Voorbeeld

**Echte test resultaten:**

```bash
# Query: "democratie weerbaarheid 1600 nu verslag"

# Zonder LLM (vector similarity: 0.398)
Top 3: Alle identieke "Eindterm 8" matches zonder differentiatie

# Met LLM (scores: 9/10)
1. Eindterm 8 - democratische waarden (9/10)
   "Perfect match: behandelt democratie én weerbaarheid expliciet"
   
2. Eindterm 8 - grondrechten focus (9/10)  
   "Zeer relevant: grondrechten essentieel voor democratische weerbaarheid"
   
3. Eindterm 8 - mensenrechten (9/10)
   "Sterk match: mensenrechten fundament van democratie"
```

**LLM voegt toe:**
- Context begrip (begrijpt dat het een opdracht betreft)
- Nuance (onderscheidt tussen identieke titels op basis van uitwerkingen)
- Uitleg (docent ziet WAAROM iets relevant is)

## Kosten Calculatie

**Per query met re-ranking (5 resultaten):**
- Input: ~2,000 tokens × 5 = 10,000 tokens
- Output: ~500 tokens × 5 = 2,500 tokens

**OpenAI gpt-4o-mini:**
- Input: $0.150 per 1M tokens = $0.0015
- Output: $0.600 per 1M tokens = $0.0015
- **Total: ~$0.003 per query**

**Maandelijkse kosten:**
- 100 queries/dag = $9/maand
- 500 queries/dag = $45/maand
- 1000 queries/dag = $90/maand

## Optimalisaties

### Response Caching

```python
# Add Redis caching
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str, limit: int):
    return rerank_with_llm(db, query, results)
```

### Batch Processing

Voor bulk queries (bijvoorbeeld alle lessen analyseren):
```bash
# Process multiple queries efficient
cat lessons.txt | while read lesson; do
  curl "http://localhost:8000/api/search?q=$lesson&rerank=true"
  sleep 0.5  # Rate limiting
done
```

## Alternatief: Lokale LLM (Gratis)

**Ollama setup:**
```bash
# Install
curl https://ollama.ai/install.sh | sh

# Download model
ollama pull llama3.2  # 2B params, fast
# or: ollama pull mixtral  # 8×7B, better quality

# Configure
echo "LLM_PROVIDER=ollama" >> .env
echo "OLLAMA_MODEL=llama3.2" >> .env

# Test
curl "http://localhost:8000/api/search?q=test&rerank=true"
```

**Trade-offs:**
- ✅ Gratis
- ✅ Privacy (data blijft lokaal)
- ✅ Geen rate limits
- ❌ Langzamer (~10-30s per query)
- ❌ Lagere kwaliteit dan GPT-4

## Conclusie

LLM re-ranking transformeert search van:
- **"Welke teksten lijken op mijn query?"** (vector search)

Naar:
- **"Welke leerdoelen passen écht bij mijn les?"** (LLM re-ranking)

**Aanbevolen gebruik:**
- Development: Zonder LLM (snel itereren)
- Production: Met LLM voor docenten (betere UX)
- Kostenbewust: Ollama lokaal (gratis, privacy)
