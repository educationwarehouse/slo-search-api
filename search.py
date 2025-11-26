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
    """Search doelzinnen using pgvector."""
    
    # Get query embedding
    embedder = get_embeddings()
    query_embedding = embedder.encode(query, convert_to_numpy=True)
    vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    # Use pgvector for similarity search (1 - cosine_distance = cosine_similarity)
    sql = f"""
        SELECT 
            d.id, d.fo_id, d.title, d.description, d.prefix, d.soort,
            1 - (e.embedding <=> '{vector_str}'::vector) as similarity
        FROM doelzin d
        JOIN doelzin_embedding e ON e.doelzin_id = d.id
        WHERE 1 - (e.embedding <=> '{vector_str}'::vector) >= {threshold}
        ORDER BY e.embedding <=> '{vector_str}'::vector
        LIMIT {limit}
    """
    
    results = []
    for row in db.executesql(sql):
        results.append({
            'id': row[0],
            'fo_id': row[1],
            'title': row[2],
            'description': row[3],
            'prefix': row[4],
            'soort': row[5],
            'similarity': float(row[6])
        })
    
    return results

def search_uitwerkingen(
    db,
    query: str,
    limit: int = 10,
    threshold: float = 0.0
) -> List[Dict]:
    """Search uitwerkingen using pgvector."""
    
    # Get query embedding
    embedder = get_embeddings()
    query_embedding = embedder.encode(query, convert_to_numpy=True)
    vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    # Use pgvector for similarity search
    sql = f"""
        SELECT 
            u.id, u.fo_id, u.title, u.description, u.prefix,
            1 - (e.embedding <=> '{vector_str}'::vector) as similarity
        FROM uitwerking u
        JOIN uitwerking_embedding e ON e.uitwerking_id = u.id
        WHERE 1 - (e.embedding <=> '{vector_str}'::vector) >= {threshold}
        ORDER BY e.embedding <=> '{vector_str}'::vector
        LIMIT {limit}
    """
    
    results = []
    for row in db.executesql(sql):
        results.append({
            'id': row[0],
            'fo_id': row[1],
            'title': row[2],
            'description': row[3],
            'prefix': row[4],
            'similarity': float(row[5])
        })
    
    return results

def search_combined(
    db,
    query: str,
    limit: int = 10,
    threshold: float = 0.0,
    doelzin_weight: float = 0.7
) -> List[Dict]:
    """Combined search using pgvector with weighted scoring."""
    
    embedder = get_embeddings()
    query_embedding = embedder.encode(query, convert_to_numpy=True)
    vector_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    # Use pgvector to get both doelzin and best uitwerking similarity
    sql = f"""
        WITH doelzin_scores AS (
            SELECT 
                de.doelzin_id,
                1 - (de.embedding <=> '{vector_str}'::vector) as doelzin_sim
            FROM doelzin_embedding de
        ),
        uitwerking_scores AS (
            SELECT 
                d.id as doelzin_id,
                MAX(1 - (ue.embedding <=> '{vector_str}'::vector)) as uitwerking_sim
            FROM doelzin d
            JOIN uitwerking u ON u.fo_id = ANY(d.uitwerking_ids)
            JOIN uitwerking_embedding ue ON ue.uitwerking_id = u.id
            GROUP BY d.id
        )
        SELECT 
            d.id, d.fo_id, d.title, d.description, d.prefix, d.soort,
            ds.doelzin_sim,
            COALESCE(us.uitwerking_sim, 0) as uitwerking_sim,
            ({doelzin_weight} * ds.doelzin_sim + {1-doelzin_weight} * COALESCE(us.uitwerking_sim, 0)) as combined
        FROM doelzin d
        JOIN doelzin_scores ds ON ds.doelzin_id = d.id
        LEFT JOIN uitwerking_scores us ON us.doelzin_id = d.id
        WHERE ({doelzin_weight} * ds.doelzin_sim + {1-doelzin_weight} * COALESCE(us.uitwerking_sim, 0)) >= {threshold}
        ORDER BY combined DESC
        LIMIT {limit * 2}
    """
    
    results = []
    for row in db.executesql(sql):
        doelzin_id = row[0]
        
        # Get uitwerking texts for qb_cosine
        uitwerking_texts = []
        doelzin = db.doelzin[doelzin_id]
        if doelzin and doelzin.uitwerking_ids:
            for fo_id in doelzin.uitwerking_ids:
                uitw = db(db.uitwerking.fo_id == fo_id).select().first()
                if uitw and uitw.description:
                    uitwerking_texts.append(uitw.description)
        
        results.append({
            'id': row[0],
            'fo_id': row[1],
            'title': row[2],
            'description': row[3],
            'prefix': row[4],
            'soort': row[5],
            'doelzin_similarity': float(row[6]),
            'uitwerking_similarity': float(row[7]),
            'similarity': float(row[8]),
            'uitwerking_texts': uitwerking_texts
        })
    
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
