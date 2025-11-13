"""
Phase 2: Advanced Smart Search
Implements: Multi-stage ranking, Query expansion, Citation network
"""

from typing import List, Dict, Optional, Set
import requests
from datetime import datetime


# ============================================================================
# Phase 2.1: Multi-Stage Ranking
# ============================================================================

def multi_stage_ranking(
    papers: List[Dict],
    query: str,
    grok_client,
    top_k_stage1: int = 50,
    top_k_final: int = 10
) -> List[Dict]:
    """
    Multi-stage ranking pipeline

    Stage 1: Basic relevance filtering -> top 50
    Stage 2: LLM deep re-ranking -> top 10

    Args:
        papers: List of papers (100-500 candidates)
        query: Original search query
        grok_client: Grok API client for deep re-ranking
        top_k_stage1: Number to keep after stage 1
        top_k_final: Number to keep after final stage

    Returns:
        Top-ranked papers with 'stage2_score' added
    """
    if not papers:
        return []

    # Stage 1: Already have relevance scores from Phase 1
    # Take top 50 by relevance score
    stage1_results = sorted(
        papers,
        key=lambda p: p.get('relevance_score', 0),
        reverse=True
    )[:top_k_stage1]

    print(f"   Stage 1: {len(papers)} → {len(stage1_results)} papers")

    # Stage 2: LLM deep re-ranking
    if len(stage1_results) <= top_k_final:
        # Already few enough, just return
        for p in stage1_results:
            p['stage2_score'] = p.get('relevance_score', 0)
        return stage1_results

    print(f"   Stage 2: LLM re-ranking top {len(stage1_results)} to {top_k_final}...")

    # Use Grok to re-rank based on title + abstract
    reranked = llm_rerank_papers(stage1_results, query, grok_client, top_k_final)

    return reranked


def llm_rerank_papers(
    papers: List[Dict],
    query: str,
    grok_client,
    top_k: int = 10
) -> List[Dict]:
    """
    Use LLM to deeply re-rank papers based on relevance to query

    Args:
        papers: Papers to re-rank
        query: Search query
        grok_client: Grok API client
        top_k: Number of top papers to return

    Returns:
        Re-ranked papers with 'stage2_score'
    """
    # Build prompt for LLM
    papers_text = []
    for i, paper in enumerate(papers[:20], 1):  # Limit to top 20 for context
        title = paper.get('title', 'Untitled')
        abstract = paper.get('abstract', 'No abstract')[:300]
        year = paper.get('year', 'N/A')
        cites = paper.get('citations', 0)
        papers_text.append(
            f"{i}. [{year}, {cites} cites] {title}\n   Abstract: {abstract}..."
        )

    prompt = f"""You are a research paper relevance expert. Given a search query and a list of papers, rank them by relevance to the query.

Query: "{query}"

Papers:
{chr(10).join(papers_text)}

Task: Return ONLY the numbers of the top {top_k} most relevant papers, in order from most to least relevant. Format as a comma-separated list of numbers (e.g., "3,7,1,5,2,9,4,8,6,10").

Your ranking (numbers only):"""

    try:
        # Call Grok API
        response = grok_client.chat.completions.create(
            model="grok-beta",
            messages=[
                {"role": "system", "content": "You are a research paper relevance ranking expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )

        ranking_str = response.choices[0].message.content.strip()

        # Parse ranking
        try:
            rankings = [int(x.strip()) for x in ranking_str.replace(',', ' ').split() if x.strip().isdigit()]
        except (ValueError, AttributeError) as e:
            # Fallback to original order if parsing fails
            rankings = list(range(1, min(len(papers), 20) + 1))

        # Build re-ranked list
        reranked = []
        seen_indices = set()

        for rank_num in rankings[:top_k]:
            idx = rank_num - 1  # Convert to 0-indexed
            if 0 <= idx < len(papers) and idx not in seen_indices:
                paper = papers[idx].copy()
                # Calculate stage 2 score (higher rank = higher score)
                paper['stage2_score'] = 10.0 - (len(reranked) * 0.5)
                paper['llm_rank'] = len(reranked) + 1
                reranked.append(paper)
                seen_indices.add(idx)

        # Fill remaining slots with unranked papers
        for i, paper in enumerate(papers):
            if len(reranked) >= top_k:
                break
            if i not in seen_indices:
                paper_copy = paper.copy()
                paper_copy['stage2_score'] = paper.get('relevance_score', 0) * 0.5
                paper_copy['llm_rank'] = len(reranked) + 1
                reranked.append(paper_copy)

        return reranked

    except Exception as e:
        print(f"   ⚠️  LLM re-ranking failed: {e}, using Phase 1 scores")
        # Fallback to Phase 1 scores
        for p in papers[:top_k]:
            p['stage2_score'] = p.get('relevance_score', 0)
            p['llm_rank'] = papers.index(p) + 1
        return papers[:top_k]


# ============================================================================
# Phase 2.2: Query Expansion
# ============================================================================

def expand_query_with_grok(query: str, grok_client) -> Dict[str, any]:
    """
    Use Grok-4 to expand query with synonyms and related terms

    Args:
        query: Original search query
        grok_client: Grok API client

    Returns:
        Dict with expanded_query, synonyms, related_terms
    """
    prompt = f"""You are a research query expansion expert. Given a search query, expand it with:
1. Synonyms and alternative phrasings
2. Related technical terms
3. Broader and narrower concepts

Original query: "{query}"

Provide:
1. Expanded query (original + key synonyms)
2. List of 3-5 important synonyms
3. List of 3-5 related terms

Format your response as:
EXPANDED: <expanded query here>
SYNONYMS: <synonym1>, <synonym2>, <synonym3>
RELATED: <term1>, <term2>, <term3>"""

    try:
        response = grok_client.chat.completions.create(
            model="grok-beta",
            messages=[
                {"role": "system", "content": "You are a research query expansion expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=300
        )

        result = response.choices[0].message.content.strip()

        # Parse response
        expanded_query = query
        synonyms = []
        related_terms = []

        for line in result.split('\n'):
            line = line.strip()
            if line.startswith('EXPANDED:'):
                expanded_query = line.replace('EXPANDED:', '').strip()
            elif line.startswith('SYNONYMS:'):
                synonyms = [s.strip() for s in line.replace('SYNONYMS:', '').split(',')]
            elif line.startswith('RELATED:'):
                related_terms = [t.strip() for t in line.replace('RELATED:', '').split(',')]

        return {
            'original_query': query,
            'expanded_query': expanded_query,
            'synonyms': synonyms,
            'related_terms': related_terms,
            'all_terms': [query] + synonyms + related_terms
        }

    except Exception as e:
        print(f"   ⚠️  Query expansion failed: {e}, using original query")
        return {
            'original_query': query,
            'expanded_query': query,
            'synonyms': [],
            'related_terms': [],
            'all_terms': [query]
        }


def search_with_expanded_query(
    search_func,
    query_expansion: Dict,
    max_results_per_term: int = 50
) -> List[Dict]:
    """
    Search using expanded query terms

    Args:
        search_func: Function to call for searching (e.g., agent.search)
        query_expansion: Result from expand_query_with_grok
        max_results_per_term: Max results per search term

    Returns:
        Combined and deduplicated results
    """
    all_results = []
    seen_titles = set()

    # Search with expanded query
    expanded_query = query_expansion['expanded_query']
    results = search_func(expanded_query, max_results=max_results_per_term)

    for paper in results:
        title_lower = paper.get('title', '').lower()
        if title_lower and title_lower not in seen_titles:
            seen_titles.add(title_lower)
            paper['matched_term'] = 'expanded_query'
            all_results.append(paper)

    # Optionally search synonyms (if needed)
    # for synonym in query_expansion['synonyms'][:2]:  # Limit to top 2 synonyms
    #     results = search_func(synonym, max_results=20)
    #     for paper in results:
    #         title_lower = paper.get('title', '').lower()
    #         if title_lower and title_lower not in seen_titles:
    #             seen_titles.add(title_lower)
    #             paper['matched_term'] = synonym
    #             all_results.append(paper)

    return all_results


# ============================================================================
# Phase 2.3: Citation Network Expansion
# ============================================================================

def get_cited_papers(paper_id: str, s2_api_key: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """
    Get papers cited by this paper (references)

    Args:
        paper_id: Semantic Scholar paper ID
        s2_api_key: Semantic Scholar API key
        limit: Max references to fetch

    Returns:
        List of cited papers
    """
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references"
    params = {
        'fields': 'title,year,citationCount,abstract,authors,venue,openAccessPdf,externalIds',
        'limit': limit
    }

    headers = {}
    if s2_api_key:
        headers['x-api-key'] = s2_api_key

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        cited_papers = []
        for ref in data.get('data', []):
            cited_paper = ref.get('citedPaper', {})
            if cited_paper:
                paper = {
                    'title': cited_paper.get('title', 'Untitled'),
                    'year': cited_paper.get('year'),
                    'citations': cited_paper.get('citationCount', 0),
                    'abstract': cited_paper.get('abstract', ''),
                    'authors': [{'name': a.get('name', '')} for a in cited_paper.get('authors', [])],
                    'venue': cited_paper.get('venue', ''),
                    'pdf_url': cited_paper.get('openAccessPdf', {}).get('url') if cited_paper.get('openAccessPdf') else None,
                    'paper_id': cited_paper.get('paperId'),
                    'source': 'Semantic Scholar (Citation)',
                    'doi': cited_paper.get('externalIds', {}).get('DOI')
                }
                cited_papers.append(paper)

        return cited_papers

    except Exception as e:
        print(f"   ⚠️  Failed to fetch cited papers: {e}")
        return []


def get_citing_papers(paper_id: str, s2_api_key: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """
    Get papers that cite this paper (citations)

    Args:
        paper_id: Semantic Scholar paper ID
        s2_api_key: Semantic Scholar API key
        limit: Max citations to fetch

    Returns:
        List of citing papers
    """
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations"
    params = {
        'fields': 'title,year,citationCount,abstract,authors,venue,openAccessPdf,externalIds',
        'limit': limit
    }

    headers = {}
    if s2_api_key:
        headers['x-api-key'] = s2_api_key

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        citing_papers = []
        for ref in data.get('data', []):
            citing_paper = ref.get('citingPaper', {})
            if citing_paper:
                paper = {
                    'title': citing_paper.get('title', 'Untitled'),
                    'year': citing_paper.get('year'),
                    'citations': citing_paper.get('citationCount', 0),
                    'abstract': citing_paper.get('abstract', ''),
                    'authors': [{'name': a.get('name', '')} for a in citing_paper.get('authors', [])],
                    'venue': citing_paper.get('venue', ''),
                    'pdf_url': citing_paper.get('openAccessPdf', {}).get('url') if citing_paper.get('openAccessPdf') else None,
                    'paper_id': citing_paper.get('paperId'),
                    'source': 'Semantic Scholar (Citation)',
                    'doi': citing_paper.get('externalIds', {}).get('DOI')
                }
                citing_papers.append(paper)

        return citing_papers

    except Exception as e:
        print(f"   ⚠️  Failed to fetch citing papers: {e}")
        return []


def expand_via_citations(
    seed_papers: List[Dict],
    s2_api_key: Optional[str] = None,
    max_refs_per_paper: int = 5,
    max_cites_per_paper: int = 5,
    min_citation_count: int = 10
) -> Dict[str, List[Dict]]:
    """
    Expand results using citation network

    Args:
        seed_papers: Initial papers to expand from
        s2_api_key: Semantic Scholar API key
        max_refs_per_paper: Max references to fetch per seed paper
        max_cites_per_paper: Max citations to fetch per seed paper
        min_citation_count: Min citations for a paper to be included

    Returns:
        Dict with 'references' and 'citations' lists
    """
    all_references = []
    all_citations = []
    seen_titles = set()

    # Use top 3 seed papers
    for paper in seed_papers[:3]:
        # Get paper ID
        paper_id = paper.get('paper_id')
        if not paper_id:
            continue

        # Get references (papers this paper cites)
        refs = get_cited_papers(paper_id, s2_api_key, max_refs_per_paper)
        for ref in refs:
            title_lower = ref.get('title', '').lower()
            citations = ref.get('citations', 0)
            if title_lower and title_lower not in seen_titles and citations >= min_citation_count:
                seen_titles.add(title_lower)
                all_references.append(ref)

        # Get citations (papers that cite this paper)
        cites = get_citing_papers(paper_id, s2_api_key, max_cites_per_paper)
        for cite in cites:
            title_lower = cite.get('title', '').lower()
            citations = cite.get('citations', 0)
            if title_lower and title_lower not in seen_titles and citations >= min_citation_count:
                seen_titles.add(title_lower)
                all_citations.append(cite)

    return {
        'references': all_references,
        'citations': all_citations,
        'total_expanded': len(all_references) + len(all_citations)
    }


# ============================================================================
# Combined Phase 2 Pipeline
# ============================================================================

def phase2_advanced_search(
    agent,
    query: str,
    grok_client,
    s2_api_key: Optional[str] = None,
    use_query_expansion: bool = True,
    use_multistage_ranking: bool = True,
    use_citation_network: bool = True,
    max_results: int = 10
) -> Dict:
    """
    Complete Phase 2 advanced search pipeline

    Args:
        agent: Search agent (e.g., SemanticScholarAgent)
        query: Search query
        grok_client: Grok API client for LLM features
        s2_api_key: Semantic Scholar API key for citation network
        use_query_expansion: Enable query expansion
        use_multistage_ranking: Enable multi-stage ranking
        use_citation_network: Enable citation network expansion
        max_results: Final number of results to return

    Returns:
        Dict with results and metadata
    """
    print(f"\n🚀 Phase 2 Advanced Search Pipeline")
    print(f"Query: '{query}'")

    # Step 1: Query Expansion
    if use_query_expansion:
        print(f"\n📝 Step 1: Query Expansion...")
        query_expansion = expand_query_with_grok(query, grok_client)
        print(f"   Original: {query}")
        print(f"   Expanded: {query_expansion['expanded_query']}")
        print(f"   Synonyms: {', '.join(query_expansion['synonyms'][:3])}")
        search_query = query_expansion['expanded_query']
    else:
        query_expansion = {'original_query': query, 'expanded_query': query}
        search_query = query

    # Step 2: Retrieve candidates (with Phase 1 smart search)
    print(f"\n🔍 Step 2: Retrieving candidates...")
    candidate_count = 100 if use_multistage_ranking else max_results
    candidates = agent.search(search_query, max_results=candidate_count, smart_search=True)
    print(f"   Retrieved: {len(candidates)} candidates")

    # Step 3: Multi-stage ranking
    if use_multistage_ranking and len(candidates) > max_results:
        print(f"\n🎯 Step 3: Multi-Stage Ranking...")
        ranked_results = multi_stage_ranking(
            candidates,
            query,
            grok_client,
            top_k_stage1=min(50, len(candidates)),
            top_k_final=max_results
        )
    else:
        ranked_results = candidates[:max_results]
        for p in ranked_results:
            p['stage2_score'] = p.get('relevance_score', 0)

    print(f"   Final top: {len(ranked_results)} papers")

    # Step 4: Citation network expansion (optional)
    citation_network = {'references': [], 'citations': [], 'total_expanded': 0}
    if use_citation_network and s2_api_key:
        print(f"\n🔗 Step 4: Citation Network Expansion...")
        citation_network = expand_via_citations(
            ranked_results,
            s2_api_key,
            max_refs_per_paper=5,
            max_cites_per_paper=5
        )
        print(f"   References: {len(citation_network['references'])}")
        print(f"   Citations: {len(citation_network['citations'])}")
        print(f"   Total expanded: {citation_network['total_expanded']}")

    return {
        'main_results': ranked_results,
        'query_expansion': query_expansion,
        'citation_network': citation_network,
        'total_candidates': len(candidates),
        'final_count': len(ranked_results)
    }
