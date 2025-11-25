"""Main application entry point for py4web."""
from py4web import action, request, redirect, URL
from models import get_db


# Initialize database connection
db = get_db()


@action('index')
def index():
    """Redirect to API docs."""
    return redirect(URL('api/docs'))


@action('api/docs')
def api_docs():
    """Simple API documentation."""
    return {
        'service': 'SLO Curriculum Search API',
        'version': '0.1.0',
        'endpoints': {
            'POST/GET /api/search': {
                'description': 'Combined search across doelzinnen and uitwerkingen',
                'params': {
                    'q': 'search query (required)',
                    'limit': 'max results (default: 10)',
                    'weight': 'doelzin weight 0-1 (default: 0.7)'
                },
                'example': '/api/search?q=leerlingen leren over fotosynthese&limit=5'
            },
            'POST/GET /api/search/doelzinnen': {
                'description': 'Search doelzinnen only',
                'params': {
                    'q': 'search query (required)',
                    'limit': 'max results (default: 10)',
                    'threshold': 'min similarity 0-1 (default: 0.0)'
                },
                'example': '/api/search/doelzinnen?q=wiskunde algebra'
            },
            'POST/GET /api/search/uitwerkingen': {
                'description': 'Search uitwerkingen only',
                'params': {
                    'q': 'search query (required)',
                    'limit': 'max results (default: 10)',
                    'threshold': 'min similarity 0-1 (default: 0.0)'
                }
            },
            'GET /api/doelzin/<id>': {
                'description': 'Get full doelzin with linked uitwerkingen',
                'example': '/api/doelzin/1'
            },
            'GET /api/stats': {
                'description': 'Get database statistics'
            }
        },
        'usage': {
            'curl': 'curl "http://localhost:8000/api/search?q=fotosynthese"',
            'python': 'requests.get("http://localhost:8000/api/search", params={"q": "fotosynthese"})'
        }
    }


# Import API routes
from api import *
