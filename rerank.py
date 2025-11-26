"""LLM-based reranking using Ollama."""
import requests
from typing import List, Dict
from config import config

def rerank_results(query: str, results: List[Dict], limit: int = None) -> List[Dict]:
    """Rerank search results using Ollama LLM scoring."""
    if not results:
        return results
    
    scored_results = []
    
    for result in results:
        # Create prompt for relevance scoring
        prompt = f"""Score the relevance of this curriculum item to the query on a scale of 0-10.
Query: {query}

Title: {result['title']}
Description: {result['description']}

Respond with only a number between 0 and 10."""

        try:
            response = requests.post(
                f"{config.OLLAMA_HOST}/api/generate",
                json={
                    "model": config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=10
            )
            
            if response.ok:
                score_text = response.json()['response'].strip()
                # Extract first number from response
                import re
                match = re.search(r'\d+\.?\d*', score_text)
                llm_score = float(match.group()) / 10.0 if match else result['similarity']
            else:
                llm_score = result['similarity']
                
        except:
            # Fallback to original similarity on error
            llm_score = result['similarity']
        
        result['llm_score'] = llm_score
        result['original_similarity'] = result['similarity']
        result['similarity'] = llm_score  # Replace similarity with LLM score
        scored_results.append(result)
    
    # Sort by LLM score
    scored_results.sort(key=lambda x: x['llm_score'], reverse=True)
    
    return scored_results[:limit] if limit else scored_results
