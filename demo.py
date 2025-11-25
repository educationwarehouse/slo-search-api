"""Demo script showing API usage."""
import requests
import json
from time import sleep


def test_search(base_url='http://localhost:8000'):
    """Test search endpoints with example queries."""
    
    print("=" * 70)
    print("SLO Curriculum Search API - Demo")
    print("=" * 70)
    
    # Check server is running
    try:
        response = requests.get(f'{base_url}/api/stats')
        stats = response.json()
        print(f"\n✓ Server running")
        print(f"  Doelzinnen: {stats['doelzinnen']['embedded']}/{stats['doelzinnen']['total']}")
        print(f"  Uitwerkingen: {stats['uitwerkingen']['embedded']}/{stats['uitwerkingen']['total']}")
    except Exception as e:
        print(f"\n✗ Server not running: {e}")
        print("  Start with: py4web run . --port 8000")
        return
    
    # Test queries
    queries = [
        ("Fotosynthese les", "leerlingen leren over fotosynthese en planten"),
        ("Breuken rekenen", "leerlingen oefenen met optellen en aftrekken van breuken"),
        ("Nederlands lezen", "leerlingen lezen een verhaal en beantwoorden vragen"),
        ("Geschiedenis WOII", "leerlingen onderzoeken de tweede wereldoorlog"),
    ]
    
    for title, query in queries:
        print(f"\n{'-' * 70}")
        print(f"Query: {title}")
        print(f"  \"{query}\"")
        print('-' * 70)
        
        response = requests.get(
            f'{base_url}/api/search',
            params={'q': query, 'limit': 3}
        )
        
        data = response.json()
        results = data['results']
        
        if not results:
            print("  No results found")
            continue
        
        for i, result in enumerate(results, 1):
            sim = result['similarity']
            print(f"\n{i}. [{sim:.3f}] {result['prefix']} - {result['title']}")
            print(f"   {result['description'][:120]}...")
            
            # Show scoring breakdown if available
            if 'doelzin_similarity' in result:
                d_sim = result['doelzin_similarity']
                u_sim = result['uitwerking_similarity']
                print(f"   Scores: doelzin={d_sim:.3f}, uitwerking={u_sim:.3f}")
    
    # Test detailed retrieval
    print(f"\n{'-' * 70}")
    print("Detailed Doelzin Retrieval")
    print('-' * 70)
    
    response = requests.get(f'{base_url}/api/search', params={'q': queries[0][1], 'limit': 1})
    if response.json()['results']:
        top_result = response.json()['results'][0]
        doelzin_id = top_result['id']
        
        response = requests.get(f'{base_url}/api/doelzin/{doelzin_id}')
        full = response.json()
        
        print(f"\nDoelzin: {full['title']}")
        print(f"  {full['description']}")
        print(f"\nLinked Uitwerkingen ({len(full['uitwerkingen'])}):")
        
        for uitw in full['uitwerkingen'][:3]:
            print(f"  • {uitw.get('title', 'N/A')}")
            print(f"    {uitw['description'][:80]}...")
    
    print(f"\n{'=' * 70}")
    print("Demo complete!")
    print('=' * 70)


if __name__ == '__main__':
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8000'
    test_search(base_url)
