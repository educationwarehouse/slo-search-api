"""Query-boosted cosine similarity for enhanced search results."""
import numpy as np
from typing import List, Dict
import re
from collections import Counter

def calculate_bm25_score(query: str, document: str, k1: float = 1.5, b: float = 0.75) -> float:
    """Calculate BM25 score for keyword matching."""
    # Tokenize and normalize
    query_terms = set(re.findall(r'\w+', query.lower()))
    doc_terms = re.findall(r'\w+', document.lower())
    
    if not doc_terms:
        return 0.0
    
    doc_length = len(doc_terms)
    avg_doc_length = 50  # Approximate average for curriculum descriptions
    
    doc_freq = Counter(doc_terms)
    score = 0.0
    
    for term in query_terms:
        if term in doc_freq:
            tf = doc_freq[term]
            # BM25 formula
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
            score += numerator / denominator
    
    return score

def enhance_with_qb_cosine(
    query: str,
    results: List[Dict],
    semantic_weight: float = 0.7,
    lexical_weight: float = 0.1
) -> List[Dict]:
    """
    Enhance results with query-boosted cosine similarity.
    Combines semantic (embedding) similarity with lexical (keyword) matching.
    
    Args:
        query: Search query
        results: List of search results with similarity scores
        semantic_weight: Weight for semantic similarity (default: 0.7)
        lexical_weight: Weight for lexical matching (default: 0.3)
    
    Returns:
        Enhanced and re-sorted results
    """
    if not results:
        return results
    
    # Calculate combined scores
    enhanced_results = []
    max_bm25 = 0.0
    
    # First pass: calculate BM25 scores
    for result in results:
        # Combine title, description AND uitwerking texts for lexical matching
        document = f"{result['title']} {result['description']}"
        
        # Include uitwerking texts if available
        if 'uitwerking_texts' in result and result['uitwerking_texts']:
            document += " " + " ".join(result['uitwerking_texts'])
        
        bm25_score = calculate_bm25_score(query, document)
        max_bm25 = max(max_bm25, bm25_score)
        result['bm25_score'] = bm25_score
    
    # Second pass: normalize and combine scores
    for result in results:
        # Normalize BM25 to 0-1 range
        norm_bm25 = result['bm25_score'] / max_bm25 if max_bm25 > 0 else 0
        
        # Get semantic similarity (stored as 'similarity' or 'llm_score')
        semantic_sim = result.get('llm_score', result.get('similarity', 0))
        
        # Calculate query-boosted cosine similarity
        # Use additive model: semantic score + lexical bonus (preserves high semantic scores)
        qb_cosine = semantic_sim + (lexical_weight * norm_bm25)
        # Note: Score can exceed 1.0 when both semantic and lexical signals are strong
        
        # Store enhanced scores
        result['qb_cosine'] = qb_cosine
        result['semantic_score'] = semantic_sim
        result['lexical_score'] = norm_bm25
        result['original_rank'] = results.index(result)
        
        # Update main similarity score
        result['similarity'] = qb_cosine
        
        enhanced_results.append(result)
    
    # Re-sort by qb_cosine score
    enhanced_results.sort(key=lambda x: x['qb_cosine'], reverse=True)
    
    return enhanced_results
