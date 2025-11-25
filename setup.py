"""Setup validation and initialization."""
import sys
from pathlib import Path


def check_postgres():
    """Check PostgreSQL connection and pgvector extension."""
    try:
        import psycopg2
        conn = psycopg2.connect("dbname=postgres user=postgres")
        cur = conn.cursor()
        
        # Check pgvector
        cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
        if not cur.fetchone():
            print("⚠ pgvector extension not installed globally")
            print("  Install: sudo apt install postgresql-pgvector")
            print("  Or build from source: https://github.com/pgvector/pgvector")
        else:
            print("✓ pgvector available")
        
        conn.close()
        return True
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        return False


def check_model():
    """Check if embedding model is available."""
    try:
        from sentence_transformers import SentenceTransformer
        print("Downloading embedding model (first time ~100MB)...")
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print(f"✓ Model loaded: {model.get_sentence_embedding_dimension()}d embeddings")
        return True
    except Exception as e:
        print(f"✗ Model loading failed: {e}")
        return False


def check_data():
    """Check if curriculum data is available."""
    data_dir = Path('../curriculum-fo/data')
    if not data_dir.exists():
        print(f"✗ Data directory not found: {data_dir}")
        print("  Clone: git clone https://github.com/slonl/curriculum-fo ../curriculum-fo")
        return False
    
    files = ['doelzinnen.json', 'uitwerkingen.json']
    for f in files:
        if not (data_dir / f).exists():
            print(f"✗ Missing: {f}")
            return False
    
    print(f"✓ Data directory found: {data_dir}")
    return True


def create_database():
    """Create database if it doesn't exist."""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    try:
        conn = psycopg2.connect("dbname=postgres user=postgres")
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname='slo_search'")
        if cur.fetchone():
            print("✓ Database 'slo_search' exists")
        else:
            cur.execute("CREATE DATABASE slo_search")
            print("✓ Created database 'slo_search'")
        
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Database creation failed: {e}")
        return False


def init_tables():
    """Initialize database tables."""
    try:
        from models import get_db
        db = get_db()
        print("✓ Database tables initialized")
        db.close()
        return True
    except Exception as e:
        print(f"✗ Table initialization failed: {e}")
        return False


def main():
    """Run full setup validation."""
    print("SLO Search API - Setup Validation\n")
    
    checks = [
        ("PostgreSQL & pgvector", check_postgres),
        ("Embedding model", check_model),
        ("Curriculum data", check_data),
        ("Database creation", create_database),
        ("Table initialization", init_tables),
    ]
    
    results = []
    for name, check in checks:
        print(f"\n{name}:")
        results.append(check())
    
    print("\n" + "="*60)
    if all(results):
        print("✓ Setup complete! Ready to ingest data.")
        print("\nNext steps:")
        print("  1. python ingest.py")
        print("  2. python tasks.py dev")
        print("  3. curl http://localhost:8000/api/search?q=test")
    else:
        print("✗ Setup incomplete. Fix errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
