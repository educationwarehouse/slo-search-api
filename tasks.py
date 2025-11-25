"""Task automation using edwh/invoke style."""
from pathlib import Path
import subprocess
import sys


def db_create():
    """Create PostgreSQL database."""
    subprocess.run([
        'psql', '-c', 'CREATE DATABASE slo_search;'
    ])
    print("✓ Database created")


def db_reset():
    """Drop and recreate database."""
    subprocess.run(['psql', '-c', 'DROP DATABASE IF EXISTS slo_search;'])
    db_create()


def ingest(data_dir='../curriculum-fo/data'):
    """Run data ingestion pipeline."""
    subprocess.run([sys.executable, 'ingest.py'])


def dev():
    """Start development server."""
    subprocess.run([
        'py4web', 'run', 'apps',
        '--watch=off',
        '--port=8000'
    ])


def serve(port=8000):
    """Start production server."""
    subprocess.run([
        'py4web', 'run', 'apps',
        '--host=0.0.0.0',
        f'--port={port}',
        '--watch=off'
    ])


# Docker tasks
def docker_build():
    """Build Docker images."""
    subprocess.run(['docker-compose', 'build'])


def docker_up():
    """Start Docker containers."""
    subprocess.run(['docker-compose', 'up', '-d'])


def docker_down():
    """Stop Docker containers."""
    subprocess.run(['docker-compose', 'down'])


def docker_logs():
    """Show Docker logs."""
    subprocess.run(['docker-compose', 'logs', '-f'])


def docker_ingest():
    """Run ingestion in Docker container."""
    subprocess.run([
        'docker-compose', 'exec', 'api',
        'python', 'ingest.py'
    ])


def docker_shell():
    """Open shell in API container."""
    subprocess.run([
        'docker-compose', 'exec', 'api',
        'bash'
    ])


def docker_psql():
    """Open PostgreSQL shell."""
    subprocess.run([
        'docker-compose', 'exec', 'postgres',
        'psql', '-U', 'slo_user', '-d', 'slo_search'
    ])


def ssl_generate():
    """Generate self-signed SSL certificates."""
    subprocess.run(['bash', 'generate_ssl.sh'])


def test():
    """Run search test."""
    from models import get_db
    from search import search_doelzinnen, search_combined
    
    db = get_db()
    
    test_queries = [
        "leerlingen leren over fotosynthese",
        "rekenen met breuken",
        "Nederlands lezen en begrijpen",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        results = search_combined(db, query, limit=3)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']} ({result['similarity']:.3f})")
            print(f"   {result['description'][:100]}...")
            print(f"   Prefix: {result['prefix']} | Soort: {result['soort']}")


if __name__ == '__main__':
    # Simple CLI
    import sys
    if len(sys.argv) > 1:
        task = sys.argv[1]
        globals()[task]()
    else:
        print("Available tasks: db_create, db_reset, ingest, dev, serve, test")
