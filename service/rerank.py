"""LLM-based reranking using OpenRouter."""
import re
from typing import List, Dict
from openai import OpenAI
from config import config

def rerank_results(query: str, results: List[Dict], limit: int = None) -> List[Dict]:
    """Rerank search results using OpenRouter LLM scoring with streaming and timeout."""
    if not results:
        return results
    
    client = OpenAI(
        base_url=config.OPENROUTER_BASE_URL,
        api_key=config.OPENROUTER_API_KEY,
        timeout=5.0  # 5-second timeout per request
    )
    
    scored_results = []
    
    for result in results:
        # Create prompt for direct scoring (no reasoning)
        prompt = f"""Score relevance 0-10. Only output the number.
Query: {query}
Title: {result['title']}
Description: {result['description']}"""

        try:
            # Use streaming to get results faster
            stream = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=3,  # Just need 1-2 digits
                stream=True
            )
            
            # Accumulate streamed response
            score_text = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    score_text += chunk.choices[0].delta.content
                    # Try to extract number as soon as we have it
                    match = re.search(r'\d+\.?\d*', score_text)
                    if match:
                        llm_score = float(match.group()) / 10.0
                        break
            else:
                # No number found in stream
                llm_score = result['similarity']
                
        except Exception:
            # Fallback to original similarity on timeout or error
            llm_score = result['similarity']
        
        result['llm_score'] = llm_score
        result['original_similarity'] = result['similarity']
        result['similarity'] = llm_score  # Replace similarity with LLM score
        scored_results.append(result)
    
    # Sort by LLM score
    scored_results.sort(key=lambda x: x['llm_score'], reverse=True)
    
    return scored_results[:limit] if limit else scored_results
