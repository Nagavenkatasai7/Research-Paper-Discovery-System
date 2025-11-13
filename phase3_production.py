"""
Phase 3: Production Polish
Implements: Adaptive search, Result diversification, Performance optimization
"""

from typing import List, Dict, Optional, Set
from datetime import datetime
from collections import defaultdict
import hashlib
import json
import time


# ============================================================================
# Phase 3.1: Adaptive Search
# ============================================================================

def classify_query_intent(query: str, grok_client) -> Dict:
    """
    Use Grok to classify query intent and suggest optimal search strategy

    Query types:
    - Exploratory: Broad topic exploration
    - Specific: Looking for specific paper/method
    - Survey: Want overview/survey papers
    - Recent: Want latest developments
    - Foundational: Want seminal/classic papers

    Args:
        query: Search query
        grok_client: Grok API client

    Returns:
        Dict with intent, confidence, recommended_settings
    """
    prompt = f"""Analyze this research paper search query and classify its intent:

Query: "{query}"

Classify into ONE of these types:
1. EXPLORATORY - Broad topic exploration (e.g., "machine learning", "digital twins")
2. SPECIFIC - Looking for specific paper, method, or author (e.g., "BERT paper", "Vaswani attention")
3. SURVEY - Wants overview/survey/review papers (e.g., "survey of deep learning", "review of transformers")
4. RECENT - Wants latest/cutting-edge developments (e.g., "latest in LLMs", "2024 advances")
5. FOUNDATIONAL - Wants seminal/classic/highly-cited papers (e.g., "foundational papers", "classic work")

Respond ONLY with this format:
INTENT: <type>
CONFIDENCE: <0.0-1.0>
REASONING: <brief explanation>"""

    try:
        response = grok_client.chat.completions.create(
            model="grok-beta",
            messages=[
                {"role": "system", "content": "You are a research query intent classifier."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150
        )

        result_text = response.choices[0].message.content.strip()

        # Parse response
        intent = "EXPLORATORY"  # default
        confidence = 0.7
        reasoning = ""

        for line in result_text.split('\n'):
            line = line.strip()
            if line.startswith('INTENT:'):
                intent = line.replace('INTENT:', '').strip()
            elif line.startswith('CONFIDENCE:'):
                try:
                    confidence = float(line.replace('CONFIDENCE:', '').strip())
                except (ValueError, TypeError) as e:
                    # Default confidence if parsing fails
                    confidence = 0.7
            elif line.startswith('REASONING:'):
                reasoning = line.replace('REASONING:', '').strip()

        # Determine recommended settings based on intent
        settings = get_adaptive_settings(intent)

        return {
            'intent': intent,
            'confidence': confidence,
            'reasoning': reasoning,
            'recommended_settings': settings
        }

    except Exception as e:
        print(f"   ⚠️  Query classification failed: {e}, using default")
        return {
            'intent': 'EXPLORATORY',
            'confidence': 0.5,
            'reasoning': 'Failed to classify',
            'recommended_settings': get_adaptive_settings('EXPLORATORY')
        }


def get_adaptive_settings(intent: str) -> Dict:
    """
    Get recommended search settings based on query intent

    Args:
        intent: Query intent type

    Returns:
        Dict with recommended settings
    """
    settings = {
        'EXPLORATORY': {
            'max_results': 50,
            'min_year': datetime.now().year - 5,
            'min_citations': 10,
            'use_citation_network': True,
            'diversify_results': True,
            'sort_by': 'relevance'
        },
        'SPECIFIC': {
            'max_results': 20,
            'min_year': datetime.now().year - 10,
            'min_citations': 0,  # Don't filter by citations
            'use_citation_network': False,
            'diversify_results': False,
            'sort_by': 'relevance'
        },
        'SURVEY': {
            'max_results': 30,
            'min_year': datetime.now().year - 3,
            'min_citations': 50,  # Higher threshold for surveys
            'use_citation_network': True,
            'diversify_results': True,
            'sort_by': 'citations',
            'filter_surveys': True  # Prioritize papers with 'survey', 'review' in title
        },
        'RECENT': {
            'max_results': 40,
            'min_year': datetime.now().year - 2,  # Last 2 years only
            'min_citations': 5,  # Lower threshold for recent
            'use_citation_network': False,
            'diversify_results': True,
            'sort_by': 'year'
        },
        'FOUNDATIONAL': {
            'max_results': 30,
            'min_year': 2000,  # Go back further
            'min_citations': 100,  # High citation threshold
            'use_citation_network': True,
            'diversify_results': False,
            'sort_by': 'citations'
        }
    }

    return settings.get(intent, settings['EXPLORATORY'])


# ============================================================================
# Phase 3.2: Result Diversification
# ============================================================================

def diversify_results(
    papers: List[Dict],
    max_results: int = 20,
    diversity_factors: Optional[List[str]] = None
) -> List[Dict]:
    """
    Ensure diversity in results across multiple dimensions

    Diversity factors:
    - venue: Different conferences/journals
    - year: Spread across years
    - authors: Different research groups
    - citations: Mix of highly-cited and newer papers

    Args:
        papers: Papers to diversify
        max_results: Maximum results to return
        diversity_factors: Factors to diversify on (default: ['venue', 'year', 'authors'])

    Returns:
        Diversified list of papers
    """
    if not papers or len(papers) <= max_results:
        return papers

    if diversity_factors is None:
        diversity_factors = ['venue', 'year', 'authors']

    diversified = []
    remaining = papers.copy()

    # Track what we've selected
    selected_venues = set()
    selected_years = set()
    selected_authors = set()

    # Round-robin selection with diversity constraints
    while len(diversified) < max_results and remaining:
        best_paper = None
        best_diversity_score = -1

        for paper in remaining[:min(50, len(remaining))]:  # Consider top 50 remaining
            diversity_score = 0

            # Venue diversity
            if 'venue' in diversity_factors:
                venue = paper.get('venue', '').lower()
                if venue and venue not in selected_venues:
                    diversity_score += 2  # Strong bonus for new venue

            # Year diversity
            if 'year' in diversity_factors:
                year = paper.get('year')
                if year and year not in selected_years:
                    diversity_score += 1.5

            # Author diversity
            if 'authors' in diversity_factors:
                authors = paper.get('authors', [])
                author_names = {a.get('name', '').lower() for a in authors}
                if not (author_names & selected_authors):  # No overlap
                    diversity_score += 1

            # Base relevance (to not completely ignore quality)
            relevance = paper.get('stage2_score') or paper.get('relevance_score', 0)
            diversity_score += relevance * 0.3  # 30% weight on relevance

            if diversity_score > best_diversity_score:
                best_diversity_score = diversity_score
                best_paper = paper

        if best_paper:
            diversified.append(best_paper)
            remaining.remove(best_paper)

            # Update selected sets
            if 'venue' in diversity_factors:
                venue = best_paper.get('venue', '').lower()
                if venue:
                    selected_venues.add(venue)

            if 'year' in diversity_factors:
                year = best_paper.get('year')
                if year:
                    selected_years.add(year)

            if 'authors' in diversity_factors:
                authors = best_paper.get('authors', [])
                author_names = {a.get('name', '').lower() for a in authors}
                selected_authors.update(author_names)
        else:
            # No more papers to select, break
            break

    # Fill remaining slots with top-scored papers if needed
    while len(diversified) < max_results and remaining:
        diversified.append(remaining.pop(0))

    return diversified


def ensure_temporal_diversity(papers: List[Dict], year_bins: int = 3) -> List[Dict]:
    """
    Ensure papers are spread across time periods

    Args:
        papers: Papers to diversify
        year_bins: Number of time bins to create

    Returns:
        Papers with temporal diversity
    """
    if not papers:
        return papers

    # Group by year
    years = [p.get('year', 0) for p in papers if p.get('year')]
    if not years:
        return papers

    min_year = min(years)
    max_year = max(years)
    year_range = max_year - min_year

    if year_range == 0:
        return papers

    # Create bins
    bin_size = year_range / year_bins
    bins = defaultdict(list)

    for paper in papers:
        year = paper.get('year', min_year)
        bin_idx = min(int((year - min_year) / bin_size), year_bins - 1)
        bins[bin_idx].append(paper)

    # Select papers round-robin from bins
    result = []
    max_per_bin = len(papers) // year_bins + 1

    for bin_idx in range(year_bins):
        result.extend(bins[bin_idx][:max_per_bin])

    return result


# ============================================================================
# Phase 3.3: Performance Optimization
# ============================================================================

class SearchCache:
    """In-memory cache for search results"""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Args:
            max_size: Maximum cache entries
            ttl_seconds: Time-to-live for cache entries (default: 1 hour)
        """
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds

    def _make_key(self, query: str, **params) -> str:
        """Generate cache key from query and parameters"""
        # Sort params for consistent hashing
        param_str = json.dumps(sorted(params.items()))
        key_str = f"{query}:{param_str}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, query: str, **params) -> Optional[List[Dict]]:
        """Get cached results if available and not expired"""
        key = self._make_key(query, **params)

        if key not in self.cache:
            return None

        # Check if expired
        if time.time() - self.access_times[key] > self.ttl_seconds:
            del self.cache[key]
            del self.access_times[key]
            return None

        # Update access time
        self.access_times[key] = time.time()
        return self.cache[key]

    def set(self, query: str, results: List[Dict], **params):
        """Cache results"""
        key = self._make_key(query, **params)

        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = min(self.access_times, key=self.access_times.get)
            del self.cache[oldest_key]
            del self.access_times[oldest_key]

        self.cache[key] = results
        self.access_times[key] = time.time()

    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.access_times.clear()

    def stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'utilization': len(self.cache) / self.max_size if self.max_size > 0 else 0
        }


# Global cache instance
_global_cache = SearchCache(max_size=100, ttl_seconds=1800)  # 30 min TTL


def get_cache() -> SearchCache:
    """Get global cache instance"""
    return _global_cache


def batch_process_papers(
    papers: List[Dict],
    process_func,
    batch_size: int = 50
) -> List[Dict]:
    """
    Process papers in batches for better performance

    Args:
        papers: Papers to process
        process_func: Function to apply to each batch
        batch_size: Size of each batch

    Returns:
        Processed papers
    """
    results = []

    for i in range(0, len(papers), batch_size):
        batch = papers[i:i+batch_size]
        processed_batch = process_func(batch)
        results.extend(processed_batch)

    return results


# ============================================================================
# Combined Phase 3 Pipeline
# ============================================================================

def adaptive_search_pipeline(
    agent,
    query: str,
    grok_client,
    s2_api_key: Optional[str] = None,
    use_cache: bool = True,
    auto_adapt: bool = True,
    diversify: bool = True
) -> Dict:
    """
    Complete Phase 3 production-ready search pipeline

    Args:
        agent: Search agent
        query: Search query
        grok_client: Grok API client
        s2_api_key: Semantic Scholar API key
        use_cache: Enable result caching
        auto_adapt: Automatically adapt settings based on query
        diversify: Enable result diversification

    Returns:
        Dict with results, settings, and metadata
    """
    print(f"\n🎯 Phase 3: Adaptive Production Search")
    print(f"Query: '{query}'")

    # Check cache first
    cache = get_cache()
    if use_cache:
        cached = cache.get(query, s2_api_key=s2_api_key, diversify=diversify)
        if cached:
            print(f"   ✅ Cache hit! Returning cached results")
            return {
                'main_results': cached,
                'from_cache': True,
                'cache_stats': cache.stats()
            }

    # Step 1: Classify query intent (if auto-adapt enabled)
    if auto_adapt:
        print(f"\n📋 Step 1: Analyzing query intent...")
        intent_analysis = classify_query_intent(query, grok_client)
        print(f"   Intent: {intent_analysis['intent']} (confidence: {intent_analysis['confidence']:.2f})")
        print(f"   Reasoning: {intent_analysis['reasoning']}")

        settings = intent_analysis['recommended_settings']
    else:
        settings = {
            'max_results': 50,
            'min_year': datetime.now().year - 5,
            'min_citations': 10,
            'use_citation_network': True,
            'diversify_results': True,
            'sort_by': 'relevance'
        }
        intent_analysis = {'intent': 'DEFAULT', 'confidence': 1.0}

    print(f"\n   Adaptive settings:")
    print(f"      Max results: {settings['max_results']}")
    print(f"      Year range: {settings['min_year']}-{datetime.now().year}")
    print(f"      Min citations: {settings['min_citations']}")
    print(f"      Citation network: {settings.get('use_citation_network', False)}")

    # Step 2: Execute search with adaptive settings
    print(f"\n🔍 Step 2: Executing adaptive search...")

    # Import Phase 2 pipeline
    from phase2_advanced_search import phase2_advanced_search

    results = phase2_advanced_search(
        agent=agent,
        query=query,
        grok_client=grok_client,
        s2_api_key=s2_api_key,
        use_query_expansion=True,
        use_multistage_ranking=True,
        use_citation_network=settings.get('use_citation_network', True),
        max_results=settings['max_results']
    )

    main_results = results['main_results']

    # Step 3: Apply diversification (if enabled)
    if diversify and settings.get('diversify_results', True):
        print(f"\n🎨 Step 3: Diversifying results...")
        print(f"   Before: {len(main_results)} papers")

        main_results = diversify_results(
            main_results,
            max_results=min(20, len(main_results)),
            diversity_factors=['venue', 'year', 'authors']
        )

        print(f"   After: {len(main_results)} papers")

        # Show diversity stats
        venues = set(p.get('venue', 'Unknown') for p in main_results)
        years = set(p.get('year', 0) for p in main_results)
        print(f"   Unique venues: {len(venues)}")
        print(f"   Year spread: {len(years)} different years")

    # Step 4: Cache results
    if use_cache:
        cache.set(query, main_results, s2_api_key=s2_api_key, diversify=diversify)

    return {
        'main_results': main_results,
        'intent_analysis': intent_analysis,
        'settings_used': settings,
        'query_expansion': results.get('query_expansion', {}),
        'citation_network': results.get('citation_network', {}),
        'from_cache': False,
        'cache_stats': cache.stats()
    }
