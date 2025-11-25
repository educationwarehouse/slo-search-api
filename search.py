"""Search functionality using embeddings."""
import numpy as np
from typing import List, Dict, Optional
from models import get_db
from embeddings import get_embeddings

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search_doelzinnen(
    db,
    query: str,
    limit: int = 10,
    threshold: float = 0.0
) -> List[Dict]:
    """Search doelzinnen using embeddings."""
    
    # Get query embedding
    embedder = get_embeddings()
    query_embedding = embedder.encode(query, convert_to_numpy=True)
    
    # Load all embeddings
    rows = db(db.doelzin_embedding).select(
        db.doelzin_embedding.doelzin_id,
        db.doelzin_embedding.embedding
    )
    
    # Calculate similarities
    results = []
    for row in rows:
        emb = np.array(row.embedding)
        similarity = cosine_similarity(query_embedding, emb)
        
        if similarity >= threshold:
            doelzin = db.doelzin[row.doelzin_id]
            results.append({
                'id': doelzin.id,
                'fo_id': doelzin.fo_id,
                'title': doelzin.title,
                'description': doelzin.description,
                'prefix': doelzin.prefix,
                'soort': doelzin.soort,
                'similarity': float(similarity)
            })
    
    # Sort by similarity and limit
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:limit]

def search_uitwerkingen(
    db,
    query: str,
    limit: int = 10,
    threshold: float = 0.0
) -> List[Dict]:
    """Search uitwerkingen using embeddings."""
    
    # Get query embedding
    embedder = get_embeddings()
    query_embedding = embedder.encode(query, convert_to_numpy=True)
    
    # Load all embeddings
    rows = db(db.uitwerking_embedding).select(
        db.uitwerking_embedding.uitwerking_id,
        db.uitwerking_embedding.embedding
    )
    
    # Calculate similarities
    results = []
    for row in rows:
        emb = np.array(row.embedding)
        similarity = cosine_similarity(query_embedding, emb)
        
        if similarity >= threshold:
            uitwerking = db.uitwerking[row.uitwerking_id]
            results.append({
                'id': uitwerking.id,
                'fo_id': uitwerking.fo_id,
                'title': uitwerking.title,
                'description': uitwerking.description,
                'prefix': uitwerking.prefix,
                'similarity': float(similarity)
            })
    
    # Sort by similarity and limit
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:limit]

def search_combined(
    db,
    query: str,
    limit: int = 10,
    threshold: float = 0.0,
    doelzin_weight: float = 0.7
) -> List[Dict]:
    """Combined search across doelzinnen and uitwerkingen with weighted scoring."""
    
    embedder = get_embeddings()
    query_embedding = embedder.encode(query, convert_to_numpy=True)
    
    # Search both with higher limit
    doelzin_results = {}
    uitwerking_parent_scores = {}
    
    # Get doelzin similarities
    for row in db(db.doelzin_embedding).select():
        emb = np.array(row.embedding)
        sim = cosine_similarity(query_embedding, emb)
        doelzin_results[row.doelzin_id] = sim
    
    # Get uitwerking similarities and map to parent doelzinnen
    for row in db(db.uitwerking_embedding).select():
        uitwerking = db.uitwerking[row.uitwerking_id]
        emb = np.array(row.embedding)
        sim = cosine_similarity(query_embedding, emb)
        
        # Find parent doelzinnen
        for doelzin in db(db.doelzin.uitwerking_ids.contains(uitwerking.fo_id)).select():
            if doelzin.id not in uitwerking_parent_scores:
                uitwerking_parent_scores[doelzin.id] = []
            uitwerking_parent_scores[doelzin.id].append(sim)
    
    # Combine scores
    results = []
    for doelzin_id, doelzin_sim in doelzin_results.items():
        # Get best uitwerking similarity for this doelzin
        uitwerking_sim = max(uitwerking_parent_scores.get(doelzin_id, [0.0]))
        
        # Weighted combined score
        combined_score = (doelzin_weight * doelzin_sim + 
                         (1 - doelzin_weight) * uitwerking_sim)
        
        if combined_score >= threshold:
            doelzin = db.doelzin[doelzin_id]
            results.append({
                'id': doelzin.id,
                'fo_id': doelzin.fo_id,
                'title': doelzin.title,
                'description': doelzin.description,
                'prefix': doelzin.prefix,
                'soort': doelzin.soort,
                'similarity': float(combined_score),
                'doelzin_similarity': float(doelzin_sim),
                'uitwerking_similarity': float(uitwerking_sim)
            })
    
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:limit]

def get_doelzin_with_uitwerkingen(db, doelzin_id: int) -> Optional[Dict]:
    """Get a doelzin with all its uitwerkingen."""
    
    doelzin = db.doelzin[doelzin_id]
    if not doelzin:
        return None
    
    # Get linked uitwerkingen
    uitwerkingen = []
    if doelzin.uitwerking_ids:
        for fo_id in doelzin.uitwerking_ids:
            uitwerking = db(db.uitwerking.fo_id == fo_id).select().first()
            if uitwerking:
                uitwerkingen.append({
                    'id': uitwerking.id,
                    'fo_id': uitwerking.fo_id,
                    'title': uitwerking.title,
                    'description': uitwerking.description,
                    'prefix': uitwerking.prefix,
                })
    
    return {
        'id': doelzin.id,
        'fo_id': doelzin.fo_id,
        'title': doelzin.title,
        'description': doelzin.description,
        'prefix': doelzin.prefix,
        'soort': doelzin.soort,
        'ce': doelzin.ce,
        'se': doelzin.se,
        'status': doelzin.status,
        'uitwerkingen': uitwerkingen
    }
