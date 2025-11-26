"""Migrate from SQLite to PostgreSQL with pgvector."""
import psycopg2
from pydal import DAL, Field

def get_sqlite_db():
    """Connect to SQLite (read-only)."""
    db = DAL('sqlite:////app/slo_search.db', folder='.', migrate=False, pool_size=1)
    
    db.define_table('doelzin',
        Field('fo_id', 'string'),
        Field('title', 'text'),
        Field('description', 'text'),
        Field('prefix', 'string'),
        Field('soort', 'string'),
        Field('ce', 'integer'),
        Field('se', 'integer'),
        Field('status', 'string'),
        Field('uitwerking_ids', 'json'),
        Field('metadata', 'json'),
    )
    
    db.define_table('uitwerking',
        Field('fo_id', 'string'),
        Field('title', 'text'),
        Field('description', 'text'),
        Field('prefix', 'string'),
        Field('niveau_ids', 'json'),
        Field('status', 'string'),
    )
    
    db.define_table('doelzin_embedding',
        Field('doelzin_id', 'reference doelzin'),
        Field('embedding_model', 'string'),
        Field('embedding', 'json'),
    )
    
    db.define_table('uitwerking_embedding',
        Field('uitwerking_id', 'reference uitwerking'),
        Field('embedding_model', 'string'),
        Field('embedding', 'json'),
    )
    
    return db

def migrate():
    print("Connecting to SQLite source...")
    db_sqlite = get_sqlite_db()
    
    print("Connecting to PostgreSQL...")
    pg_conn = psycopg2.connect(
        dbname='slo_search',
        user='slo',
        password='slo_password',
        host='postgres',
        port='5432'
    )
    pg_cur = pg_conn.cursor()
    
    # Drop existing embedding tables
    print("Dropping existing embedding tables...")
    pg_cur.execute("DROP TABLE IF EXISTS doelzin_embedding CASCADE;")
    pg_cur.execute("DROP TABLE IF EXISTS uitwerking_embedding CASCADE;")
    pg_conn.commit()
    
    # Create tables with vector type
    print("Creating tables with vector type...")
    pg_cur.execute("""
        CREATE TABLE doelzin_embedding (
            id SERIAL PRIMARY KEY,
            doelzin_id INTEGER UNIQUE NOT NULL REFERENCES doelzin(id),
            embedding_model VARCHAR(512) NOT NULL,
            embedding vector(768) NOT NULL
        );
    """)
    pg_cur.execute("""
        CREATE TABLE uitwerking_embedding (
            id SERIAL PRIMARY KEY,
            uitwerking_id INTEGER UNIQUE NOT NULL REFERENCES uitwerking(id),
            embedding_model VARCHAR(512) NOT NULL,
            embedding vector(768) NOT NULL
        );
    """)
    pg_conn.commit()
    print("✓ Tables created")
    
    # Migrate doelzin embeddings
    print("Migrating doelzin embeddings...")
    count = 0
    for row in db_sqlite(db_sqlite.doelzin_embedding).select():
        # Convert JSON array to vector format string
        vector_str = '[' + ','.join(map(str, row.embedding)) + ']'
        pg_cur.execute(
            "INSERT INTO doelzin_embedding (doelzin_id, embedding_model, embedding) VALUES (%s, %s, %s)",
            (row.doelzin_id, row.embedding_model, vector_str)
        )
        count += 1
        if count % 100 == 0:
            pg_conn.commit()
            print(f"  {count} embeddings migrated...")
    pg_conn.commit()
    print(f"✓ Migrated {count} doelzin embeddings")
    
    # Migrate uitwerking embeddings
    print("Migrating uitwerking embeddings...")
    count = 0
    for row in db_sqlite(db_sqlite.uitwerking_embedding).select():
        vector_str = '[' + ','.join(map(str, row.embedding)) + ']'
        pg_cur.execute(
            "INSERT INTO uitwerking_embedding (uitwerking_id, embedding_model, embedding) VALUES (%s, %s, %s)",
            (row.uitwerking_id, row.embedding_model, vector_str)
        )
        count += 1
        if count % 100 == 0:
            pg_conn.commit()
            print(f"  {count} embeddings migrated...")
    pg_conn.commit()
    print(f"✓ Migrated {count} uitwerking embeddings")
    
    # Create indexes
    print("Creating vector indexes...")
    pg_cur.execute("""
        CREATE INDEX doelzin_embedding_vector_idx 
        ON doelzin_embedding USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)
    pg_cur.execute("""
        CREATE INDEX uitwerking_embedding_vector_idx 
        ON uitwerking_embedding USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)
    pg_conn.commit()
    print("✓ Created vector indexes")
    
    pg_cur.close()
    pg_conn.close()
    db_sqlite.close()
    
    print("\n✓ Migration to pgvector complete!")

if __name__ == '__main__':
    migrate()
