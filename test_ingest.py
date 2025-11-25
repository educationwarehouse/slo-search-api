#!/usr/bin/env python3
"""Quick test ingestion - loads just 10 records to verify setup."""
import json
from pathlib import Path
import sys

# Add current dir to path
sys.path.insert(0, '/app')

from models import get_db
from embeddings import create_embeddings_batch, combine_text_for_embedding

def quick_test():
    """Load just first 10 doelzinnen for testing."""
    db = get_db()
    
    data_path = Path('/app/data/doelzinnen.json')
    with open(data_path) as f:
        all_data = json.load(f)
    
    # Take first 10 only
    doelzinnen = all_data[:10]
    
    print(f"Loading {len(doelzinnen)} test doelzinnen...")
    
    # Insert records
    for doel in doelzinnen:
        db.doelzin.insert(
            fo_id=doel['id'],
            title=doel['title'],
            description=doel['description']
        )
    db.commit()
    print(f"✓ Inserted {len(doelzinnen)} doelzinnen")
    
    # Generate embeddings
    print("Generating embeddings...")
    texts = [combine_text_for_embedding(d['title'], d['description']) for d in doelzinnen]
    embeddings = create_embeddings_batch(texts)
    
    # Store embeddings
    print("Storing embeddings...")
    rows = db(db.doelzin).select()
    for row, emb in zip(rows, embeddings):
        db.doelzin_embedding.insert(
            doelzin_id=row.id,
            embedding=emb.tolist()
        )
    db.commit()
    
    print(f"✓ Test data loaded! {len(doelzinnen)} records with embeddings")

if __name__ == '__main__':
    quick_test()
