"""API controller for curriculum search."""
from py4web import action, request, HTTP
from py4web.utils.cors import CORS
from models import get_db
from config import config
from search import (
    search_doelzinnen, 
    search_uitwerkingen, 
    search_combined,
    get_doelzin_with_uitwerkingen
)
import json


# Initialize database
db = get_db()


@action('api/search/doelzinnen', method=['POST', 'GET'])
@action.uses(CORS())
def api_search_doelzinnen():
    """
    Search doelzinnen by lesson description.
    
    Query params:
        q: search query
        limit: max results (default 10)
        threshold: min similarity 0-1 (default 0.0)
    """
    query = request.params.get('q') or request.json.get('query')
    if not query:
        raise HTTP(400, 'Missing query parameter')
    
    limit = int(request.params.get('limit', 10))
    threshold = float(request.params.get('threshold', 0.0))
    
    results = search_doelzinnen(db, query, limit=limit, threshold=threshold)
    
    return {
        'query': query,
        'count': len(results),
        'results': results
    }


@action('api/search/uitwerkingen', method=['POST', 'GET'])
@action.uses(CORS())
def api_search_uitwerkingen():
    """Search uitwerkingen by description."""
    query = request.params.get('q') or request.json.get('query')
    if not query:
        raise HTTP(400, 'Missing query parameter')
    
    limit = int(request.params.get('limit', 10))
    threshold = float(request.params.get('threshold', 0.0))
    
    results = search_uitwerkingen(db, query, limit=limit, threshold=threshold)
    
    return {
        'query': query,
        'count': len(results),
        'results': results
    }


@action('api/search', method=['POST', 'GET'])
@action.uses(CORS())
def api_search_combined():
    """
    Combined search across doelzinnen and uitwerkingen.
    
    Query params:
        q: search query
        limit: max results (default 10)
        weight: doelzin weight 0-1 (default 0.7)
    """
    query = request.params.get('q') or request.json.get('query')
    if not query:
        raise HTTP(400, 'Missing query parameter')
    
    limit = int(request.params.get('limit', 10))
    weight = float(request.params.get('weight', 0.7))
    
    results = search_combined(db, query, limit=limit, doelzin_weight=weight)
    
    return {
        'query': query,
        'count': len(results),
        'results': results
    }


@action('api/doelzin/<doelzin_id:int>', method='GET')
@action.uses(CORS())
def api_get_doelzin(doelzin_id):
    """Get full doelzin with linked uitwerkingen."""
    result = get_doelzin_with_uitwerkingen(db, doelzin_id)
    if not result:
        raise HTTP(404, 'Doelzin not found')
    
    return result


@action('api/stats', method='GET')
@action.uses(CORS())
def api_stats():
    """Get database statistics."""
    doelzin_count = db(db.doelzin).count()
    uitwerking_count = db(db.uitwerking).count()
    doelzin_embedded = db(db.doelzin_embedding).count()
    uitwerking_embedded = db(db.uitwerking_embedding).count()
    
    return {
        'doelzinnen': {
            'total': doelzin_count,
            'embedded': doelzin_embedded
        },
        'uitwerkingen': {
            'total': uitwerking_count,
            'embedded': uitwerking_embedded
        }
    }
