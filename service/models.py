"""Database models for curriculum search."""
from pydal import DAL, Field
from config import config

def get_db(db_uri=None, fake_migrate=False):
    """Initialize database with curriculum tables.
    
    Args:
        db_uri: Database connection string
        fake_migrate: If True, recreate .table files without running migrations
    """
    db_uri = db_uri or config.DATABASE_URI
    db = DAL(db_uri, folder='.', migrate=not fake_migrate, fake_migrate=fake_migrate, pool_size=1)
    
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
    
    # Embedding tables - use pgvector for PostgreSQL (tables already exist, skip migration)
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
    
    return db
