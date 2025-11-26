"""Database models for curriculum search."""
from pydal import DAL, Field
from config import config

def get_db(db_uri=None):
    """Initialize database with curriculum tables."""
    db_uri = db_uri or config.DATABASE_URI
    db = DAL(db_uri, folder='.', migrate=True, fake_migrate_all=True, pool_size=1)
    
    # Define tables - pydal handles everything
    db.define_table('doelzin',
        Field('fo_id', 'string', unique=True, notnull=True),
        Field('title', 'text', notnull=True),
        Field('description', 'text', notnull=True),
        Field('prefix', 'string'),
        Field('soort', 'string'),
        Field('ce', 'integer'),
        Field('se', 'integer'),
        Field('status', 'string'),
        Field('uitwerking_ids', 'json'),
        Field('metadata', 'json'),
    )
    
    db.define_table('uitwerking',
        Field('fo_id', 'string', unique=True, notnull=True),
        Field('title', 'text'),
        Field('description', 'text', notnull=True),
        Field('prefix', 'string'),
        Field('niveau_ids', 'json'),
        Field('status', 'string'),
    )
    
    # Embedding tables - use pgvector for PostgreSQL, JSON for SQLite
    is_postgres = 'postgres' in db_uri.lower()
    
    if is_postgres:
        # For PostgreSQL with pgvector - tables already exist, skip migration
        db.define_table('doelzin_embedding',
            Field('doelzin_id', 'reference doelzin'),
            Field('embedding_model', 'string'),
            Field('embedding', 'text'),  # Actual type is vector(768) in DB
            migrate=False
        )
        
        db.define_table('uitwerking_embedding',
            Field('uitwerking_id', 'reference uitwerking'),
            Field('embedding_model', 'string'),
            Field('embedding', 'text'),  # Actual type is vector(768) in DB
            migrate=False
        )
    else:
        # For SQLite use JSON
        db.define_table('doelzin_embedding',
            Field('doelzin_id', 'reference doelzin', unique=True, notnull=True),
            Field('embedding_model', 'string', notnull=True),
            Field('embedding', 'json', notnull=True),
        )
        
        db.define_table('uitwerking_embedding',
            Field('uitwerking_id', 'reference uitwerking', unique=True, notnull=True),
            Field('embedding_model', 'string', notnull=True),
            Field('embedding', 'json', notnull=True),
        )
    
    return db
