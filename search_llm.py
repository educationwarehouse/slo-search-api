"""LLM-based re-ranking for search results."""
import os
from typing import List, Dict, Optional
import json


def get_llm_client():
    """Get configured LLM client (OpenAI, Anthropic, or local)."""
    provider = os.getenv('LLM_PROVIDER', 'openai')
    
    if provider == 'openai':
        import openai
        openai.api_key = os.getenv('OPENAI_API_KEY')
        return ('openai', openai.OpenAI())
    elif provider == 'anthropic':
        import anthropic
        return ('anthropic', anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY')))
    elif provider == 'ollama':
        import requests
        return ('ollama', requests)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


def create_relevance_prompt(query: str, doelzin: Dict, uitwerkingen: List[Dict]) -> str:
    """Create prompt for LLM to assess relevance."""
    uitw_text = "\n".join([
        f"- {u.get('title', '')}: {u['description']}" 
        for u in uitwerkingen[:5]  # Limit to avoid token overflow
    ])
    
    return f"""Beoordeel de relevantie van dit leerdoel voor de gegeven les/opdracht.

OPDRACHT VAN DOCENT:
{query}

LEERDOEL:
Titel: {doelzin['title']}
Beschrijving: {doelzin['description']}
Type: {doelzin.get('soort', 'N/A')}

UITWERKINGEN:
{uitw_text if uitw_text else 'Geen uitwerkingen beschikbaar'}

Geef je beoordeling in JSON formaat:
{{
    "relevance_score": <0-10>,
    "reasoning": "<korte uitleg waarom dit wel/niet relevant is>",
    "key_match": "<welk aspect matcht het beste>"
}}

Wees kritisch maar eerlijk. Score 0-3 = niet relevant, 4-6 = mogelijk relevant, 7-10 = zeer relevant."""


def score_with_llm(prompt: str, provider: str, client) -> Dict:
    """Get relevance score from LLM."""
    try:
        if provider == 'openai':
            response = client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                messages=[
                    {"role": "system", "content": "Je bent een expert in Nederlandse onderwijs curriculum analyse."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            return json.loads(response.choices[0].message.content)
            
        elif provider == 'anthropic':
            response = client.messages.create(
                model=os.getenv('ANTHROPIC_MODEL', 'claude-3-5-haiku-20241022'),
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            # Extract JSON from response
            content = response.content[0].text
            # Try to find JSON in response
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"relevance_score": 5, "reasoning": content[:100], "key_match": ""}
            
        elif provider == 'ollama':
            # Local Ollama
            ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
            model = os.getenv('OLLAMA_MODEL', 'llama3.2')
            response = client.post(
                f'{ollama_url}/api/generate',
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
            )
            return json.loads(response.json()['response'])
            
    except Exception as e:
        print(f"LLM scoring error: {e}")
        return {"relevance_score": 5, "reasoning": f"Error: {str(e)}", "key_match": ""}


def rerank_with_llm(
    db, 
    query: str, 
    results: List[Dict], 
    use_llm: bool = True,
    batch_size: int = 10
) -> List[Dict]:
    """
    Re-rank search results using LLM for better relevance.
    
    Args:
        db: Database connection
        query: Original search query
        results: Initial search results from vector similarity
        use_llm: Whether to use LLM re-ranking (can be disabled)
        batch_size: Maximum results to re-rank (cost control)
    
    Returns:
        Re-ranked results with LLM scores
    """
    if not use_llm or not results:
        return results
    
    # Limit to batch_size to control costs
    results_to_rank = results[:batch_size]
    
    try:
        provider, client = get_llm_client()
    except Exception as e:
        print(f"LLM client initialization failed: {e}")
        return results  # Fallback to original ranking
    
    # Get full details for each result (including uitwerkingen)
    from search import get_doelzin_with_uitwerkingen
    
    enriched_results = []
    for result in results_to_rank:
        # Get full doelzin with uitwerkingen
        full = get_doelzin_with_uitwerkingen(db, result['id'])
        if not full:
            continue
            
        # Create prompt and get LLM score
        prompt = create_relevance_prompt(
            query, 
            result, 
            full.get('uitwerkingen', [])
        )
        
        llm_assessment = score_with_llm(prompt, provider, client)
        
        # Add LLM metadata to result
        enriched_results.append({
            **result,
            'llm_score': llm_assessment.get('relevance_score', 5),
            'llm_reasoning': llm_assessment.get('reasoning', ''),
            'llm_match': llm_assessment.get('key_match', ''),
            'original_rank': results.index(result) + 1
        })
    
    # Sort by LLM score (descending)
    enriched_results.sort(key=lambda x: x['llm_score'], reverse=True)
    
    # Add remaining results that weren't re-ranked
    if len(results) > batch_size:
        enriched_results.extend(results[batch_size:])
    
    return enriched_results
