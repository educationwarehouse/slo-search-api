# Quick Start

## Install & Run (5 minutes)

```bash
# 1. Install
pip install -r requirements.txt
python setup.py

# 2. Load data
python ingest.py

# 3. Start API
py4web run . --port 8000

# 4. Test
curl "http://localhost:8000/api/search?q=fotosynthese"
```

## Usage Examples

### Python
```python
import requests

# Search
r = requests.get('http://localhost:8000/api/search', 
                 params={'q': 'breuken rekenen', 'limit': 5})
for result in r.json()['results']:
    print(f"{result['similarity']:.3f} - {result['title']}")

# Get details
doelzin_id = r.json()['results'][0]['id']
r = requests.get(f'http://localhost:8000/api/doelzin/{doelzin_id}')
print(r.json())
```

### cURL
```bash
# Simple search
curl "http://localhost:8000/api/search?q=natuurkunde"

# With parameters
curl "http://localhost:8000/api/search?q=wiskunde&limit=3&weight=0.8"

# JSON POST
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "geschiedenis", "limit": 5}'
```

## Project Structure
