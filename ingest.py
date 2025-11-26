"""Load curriculum data from JSON files into database."""
import json
import sys
from pathlib import Path
from datetime import datetime

def log(msg):
    """Print with timestamp and flush."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)
    sys.stdout.flush()

log("Starting ingest script...")
log("Importing modules...")
from models import get_db
from embeddings import create_embeddings_batch, combine_text_for_embedding
log("✓ Modules imported")


def load_json(filepath: Path) -> list:
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def ingest_doelzinnen(db, data_dir: Path, model_name=None):
    """Ingest doelzinnen with embeddings."""
    log(f"Reading doelzinnen from {data_dir / 'doelzinnen.json'}")
    doelzinnen = load_json(data_dir / 'doelzinnen.json')
    log(f"✓ Loaded {len(doelzinnen)} doelzinnen from JSON")
    
    log(f"Inserting {len(doelzinnen)} doelzinnen into database...")
    
    # Prepare data
    records = []
    texts = []
    
    for doel in doelzinnen:
        record = {
            'fo_id': doel['id'],
            'title': doel['title'],
            'description': doel['description'],
            'prefix': doel.get('prefix'),
            'soort': doel.get('soort'),
            'ce': doel.get('ce'),
            'se': doel.get('se'),
            'status': doel.get('status'),
            'uitwerking_ids': doel.get('fo_uitwerking_id', []),
        }
        records.append(record)
        texts.append(combine_text_for_embedding(doel['title'], doel['description']))
    
    # Insert records
    inserted_ids = []
    for record in records:
        existing = db(db.doelzin.fo_id == record['fo_id']).select().first()
        if existing:
            db(db.doelzin.fo_id == record['fo_id']).update(**record)
            inserted_ids.append(existing.id)
        else:
            inserted_ids.append(db.doelzin.insert(**record))
    
    db.commit()
    
    # Generate embeddings in batch
    model = model_name or config.EMBEDDING_MODEL
    log(f"Generating embeddings using model: {model}")
    log(f"Total texts to embed: {len(texts)}")
    embeddings = create_embeddings_batch(texts, model)
    log(f"✓ Generated {len(embeddings)} embeddings")
    
    # Insert embeddings with batch commits
    log("Storing embeddings in database...")
    for i, (doelzin_id, embedding) in enumerate(zip(inserted_ids, embeddings)):
        existing = db(db.doelzin_embedding.doelzin_id == doelzin_id).select().first()
        if existing:
            db(db.doelzin_embedding.doelzin_id == doelzin_id).update(embedding=embedding)
        else:
            db.doelzin_embedding.insert(
                doelzin_id=doelzin_id, 
                embedding_model=model,
                embedding=embedding
            )
        
        # Commit every 100 records for progress tracking
        if (i + 1) % 100 == 0:
            db.commit()
            log(f"  Stored {i + 1}/{len(embeddings)} embeddings")
    
    db.commit()
    print(f"✓ Loaded {len(doelzinnen)} doelzinnen with embeddings")


def ingest_uitwerkingen(db, data_dir: Path, model_name=None):
    """Ingest uitwerkingen with embeddings."""
    uitwerkingen = load_json(data_dir / 'uitwerkingen.json')
    
    print(f"Loading {len(uitwerkingen)} uitwerkingen...")
    
    records = []
    texts = []
    
    for uitw in uitwerkingen:
        record = {
            'fo_id': uitw['id'],
            'title': uitw.get('title', ''),
            'description': uitw['description'],
            'prefix': uitw.get('prefix'),
            'niveau_ids': uitw.get('niveau_id', []),
            'status': uitw.get('status'),
        }
        records.append(record)
        text = combine_text_for_embedding(
            uitw.get('title', ''), 
            uitw['description']
        )
        texts.append(text)
    
    # Insert records
    inserted_ids = []
    for record in records:
        existing = db(db.uitwerking.fo_id == record['fo_id']).select().first()
        if existing:
            db(db.uitwerking.fo_id == record['fo_id']).update(**record)
            inserted_ids.append(existing.id)
        else:
            inserted_ids.append(db.uitwerking.insert(**record))
    
    db.commit()
    
    # Generate embeddings
    model = model_name or config.EMBEDDING_MODEL
    print("Generating embeddings...")
    embeddings = create_embeddings_batch(texts, model)
    
    # Insert embeddings
    print("Storing embeddings...")
    for uitwerking_id, embedding in zip(inserted_ids, embeddings):
        existing = db(db.uitwerking_embedding.uitwerking_id == uitwerking_id).select().first()
        if existing:
            db(db.uitwerking_embedding.uitwerking_id == uitwerking_id).update(embedding=embedding)
        else:
            db.uitwerking_embedding.insert(
                uitwerking_id=uitwerking_id,
                embedding_model=model,
                embedding=embedding
            )
    
    db.commit()
    print(f"✓ Loaded {len(uitwerkingen)} uitwerkingen with embeddings")


from config import config

def main(data_dir=None, db_uri=None):
    """Run full ingestion pipeline."""
    data_dir = data_dir or config.DATA_DIR
    db = get_db(db_uri)
    data_path = Path(data_dir)
    
    ingest_doelzinnen(db, data_path)
    ingest_uitwerkingen(db, data_path)
    
    print("\n✓ Ingestion complete!")
    db.close()


if __name__ == '__main__':
    main()
