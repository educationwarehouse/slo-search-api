# MCP Server - SLO Curriculum Search

Model Context Protocol server voor semantisch zoeken in het Nederlandse curriculum (SLO).

## Wat is MCP?

**Model Context Protocol (MCP)** is een standaardprotocol waarmee AI assistenten (zoals Claude, ChatGPT, etc.) kunnen communiceren met externe tools en diensten. Dit maakt het mogelijk om:

- AI's toegang te geven tot domein-specifieke data (zoals het SLO curriculum)
- Semantic search uit te voeren vanuit je AI assistent
- Gestructureerde data te doorzoeken zonder alles in de context te laden

## Beschikbare Tools

### 1. `search` - Gecombineerd zoeken (aanbevolen)

Zoekt in zowel doelzinnen als uitwerkingen met hybride semantic + lexical search.

```python
search(
    query: str,              # Zoekterm
    limit: int = 100,        # Max aantal resultaten
    threshold: float = 0.6,  # Min similarity score (0-1)
    weight: float = 0.7,     # Doelzin weight (0-1)
    rerank: bool = True      # LLM re-ranking voor betere resultaten
)
```

**Voorbeeld:**
```python
# Zoek naar fotosynthese met LLM re-ranking
search(query="fotosynthese", limit=10, rerank=True)
```

### 2. `search_goals` - Zoek alleen doelzinnen

Zoekt alleen in de leerdoelen (doelzinnen).

```python
search_goals(
    query: str,
    limit: int = 10,
    threshold: float = 0.0
)
```

### 3. `search_elaborations` - Zoek alleen uitwerkingen

Zoekt alleen in de uitgebreide beschrijvingen (uitwerkingen).

```python
search_elaborations(
    query: str,
    limit: int = 10,
    threshold: float = 0.0
)
```

### 4. `get_goal` - Haal specifieke doelzin op

Haalt een specifieke doelzin op met alle gekoppelde uitwerkingen.

```python
get_goal(doelzin_id: int)
```

### 5. `stats` - Database statistieken

Toont aantal doelzinnen en uitwerkingen in de database.

```python
stats()
```

## Installatie & Setup

### 1. Dependencies installeren

```bash
pip install -r requirements-dev.txt
```

Dit installeert onder andere `fastmcp` voor de MCP server.

### 2. Database moet geïnitialiseerd zijn

Zorg dat de database bestaat en data is ingevoerd:

```bash
# Via Docker
docker compose up -d
docker compose exec api python ingest.py

# Of lokaal
python ingest.py
```

### 3. Ollama moet draaien

De embeddings en re-ranking gebruiken Ollama:

```bash
# Check of Ollama draait
curl http://localhost:11434/api/version

# Zorg dat het model beschikbaar is
ollama pull nomic-embed-text
ollama pull llama3.2:latest
```

## MCP Server starten

### Development mode (stdio)

```bash
python mcp_server.py
```

De server luistert naar commando's via stdio (standard input/output).

### Testen

Test de MCP server met het test script:

```bash
python test_mcp.py
```

Dit voert verschillende test queries uit en toont de resultaten.

## Gebruik met Claude Desktop

Voeg de server toe aan je Claude Desktop configuratie:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "slo-curriculum": {
      "command": "python",
      "args": ["/absolute/path/to/slo-search/mcp_server.py"],
      "env": {
        "DATABASE_URI": "sqlite:////absolute/path/to/slo-search/slo_search.db",
        "OLLAMA_HOST": "http://localhost:11434"
      }
    }
  }
}
```

**Let op**: Gebruik absolute paden, geen `~` of relatieve paden.

### Controleer of het werkt

1. Herstart Claude Desktop
2. Kijk in de logs of de server gestart is
3. Vraag Claude: "Zoek in het SLO curriculum naar fotosynthese"
4. Claude zou de `search` tool moeten gebruiken

## Gebruik Voorbeelden

### Via Claude Desktop

> **User:** Kun je in het SLO curriculum zoeken naar leerdoelen over programmeren?

> **Claude:** Natuurlijk, ik ga dat voor je opzoeken.
> *[Gebruikt search tool met query="programmeren"]*

> **Claude:** Ik heb 15 relevante leerdoelen gevonden over programmeren. De meest relevante zijn:
> 1. [toont resultaat]
> 2. [toont resultaat]

### Programmatisch (Python)

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def search_curriculum():
    params = StdioServerParameters(
        command='python',
        args=['mcp_server.py']
    )
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Zoek naar fotosynthese
            result = await session.call_tool('search', {
                'query': 'fotosynthese',
                'limit': 5,
                'threshold': 0.6,
                'rerank': True
            })
            
            print(result.content[0].text)

asyncio.run(search_curriculum())
```

## Architectuur
