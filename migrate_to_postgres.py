"""Migrate data from SQLite to PostgreSQL."""
from pydal import DAL, Field

def get_db_for_migration(uri, enable_migrate=True):
    """Get database connection with migration control."""
    db = DAL(uri, folder='.', migrate=enable_migrate, fake_migrate_all=not enable_migrate, pool_size=1)
    
    # Define tables
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

def migrate():
    print("Connecting to SQLite source...")
    db_sqlite = get_db_for_migration('sqlite:////app/slo_search.db', enable_migrate=False)
    
    print("Connecting to PostgreSQL target (creating tables)...")
    db_postgres = get_db_for_migration('postgres://slo:slo_password@postgres:5432/slo_search', enable_migrate=True)
    
    # Copy doelzinnen
    print("Migrating doelzinnen...")
    count = 0
    for row in db_sqlite(db_sqlite.doelzin).select():
        db_postgres.doelzin.insert(**row.as_dict())
        count += 1
        if count % 100 == 0:
            db_postgres.commit()
            print(f"  {count} doelzinnen migrated...")
    db_postgres.commit()
    print(f"✓ Migrated {count} doelzinnen")
    
    # Copy uitwerkingen
    print("Migrating uitwerkingen...")
    count = 0
    for row in db_sqlite(db_sqlite.uitwerking).select():
        db_postgres.uitwerking.insert(**row.as_dict())
        count += 1
        if count % 100 == 0:
            db_postgres.commit()
            print(f"  {count} uitwerkingen migrated...")
    db_postgres.commit()
    print(f"✓ Migrated {count} uitwerkingen")
    
    # Copy doelzin embeddings
    print("Migrating doelzin embeddings...")
    count = 0
    for row in db_sqlite(db_sqlite.doelzin_embedding).select():
        db_postgres.doelzin_embedding.insert(**row.as_dict())
        count += 1
        if count % 100 == 0:
            db_postgres.commit()
            print(f"  {count} embeddings migrated...")
    db_postgres.commit()
    print(f"✓ Migrated {count} doelzin embeddings")
    
    # Copy uitwerking embeddings
    print("Migrating uitwerking embeddings...")
    count = 0
    for row in db_sqlite(db_sqlite.uitwerking_embedding).select():
        db_postgres.uitwerking_embedding.insert(**row.as_dict())
        count += 1
        if count % 100 == 0:
            db_postgres.commit()
            print(f"  {count} embeddings migrated...")
    db_postgres.commit()
    print(f"✓ Migrated {count} uitwerking embeddings")
    
    print("\n✓ Migration complete!")
    db_sqlite.close()
    db_postgres.close()

if __name__ == '__main__':
    migrate()
