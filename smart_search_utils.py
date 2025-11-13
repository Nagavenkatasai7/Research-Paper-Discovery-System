"""
Smart Search Utilities - Phase 1 Improvements
Implements: Date filtering, Citation threshold, Relevance scoring, Title search
"""

from typing import List, Dict, Optional
from datetime import datetime


# ============================================================================
# Phase 1.1: Date Range Filtering
# ============================================================================

def get_year_range(years_back: int = 5) -> tuple:
    """
    Get year range for filtering (default: last 5 years)

    Args:
        years_back: Number of years to go back from current year

    Returns:
        tuple: (min_year, max_year)
    """
    current_year = datetime.now().year
    min_year = current_year - years_back
    max_year = current_year

    return min_year, max_year


def filter_by_date_range(papers: List[Dict], min_year: Optional[int] = None, max_year: Optional[int] = None) -> List[Dict]:
    """
    Filter papers by publication year range

    Args:
        papers: List of paper dictionaries
        min_year: Minimum year (inclusive)
        max_year: Maximum year (inclusive)

    Returns:
        Filtered list of papers
    """
    if min_year is None and max_year is None:
        return papers

    filtered = []
    for paper in papers:
        year = paper.get('year')

        if year is None:
            continue  # Skip papers without year

        # Check year range
        if min_year and year < min_year:
            continue
        if max_year and year > max_year:
            continue

        filtered.append(paper)

    return filtered


# ============================================================================
# Phase 1.2: Citation Threshold Filtering
# ============================================================================

def get_min_citations(year_published: int, base_threshold: int = 10) -> int:
    """
    Get minimum citation threshold based on paper age

    Optimized thresholds based on 2024 best practices:
    - Very new papers (≤1 year): No threshold
    - Recent papers (2 years): Low threshold (2 citations)
    - Established papers (3 years): Moderate threshold (5 citations)
    - Older papers: Higher threshold (10 citations)

    Args:
        year_published: Year the paper was published
        base_threshold: Base citation threshold for older papers

    Returns:
        Minimum citation count for that year
    """
    current_year = datetime.now().year
    age = current_year - year_published

    if age <= 1:
        return 0   # New papers (2024-2025), no threshold
    elif age == 2:
        return 2   # 2-year papers: lowered from 5 to 2 (less aggressive)
    elif age == 3:
        return 5   # 3-year papers: lowered from 10 to 5
    elif age <= 5:
        return base_threshold  # 4-5 year papers
    else:
        return base_threshold * 1.5  # Older papers (lowered from 2x to 1.5x)


def filter_by_citations(papers: List[Dict], min_citations: Optional[int] = None, adaptive: bool = True) -> List[Dict]:
    """
    Filter papers by citation count

    Args:
        papers: List of paper dictionaries
        min_citations: Minimum citation count (if adaptive=False)
        adaptive: Use adaptive thresholding based on paper age

    Returns:
        Filtered list of papers
    """
    filtered = []

    for paper in papers:
        citations = paper.get('citations')
        # Handle None citations
        if citations is None:
            citations = 0
        year = paper.get('year', datetime.now().year)

        if adaptive:
            # Use age-based threshold
            threshold = get_min_citations(year)
        else:
            # Use fixed threshold
            threshold = min_citations if min_citations is not None else 0

        if citations >= threshold:
            filtered.append(paper)

    return filtered


# ============================================================================
# Phase 1.3: Relevance Scoring
# ============================================================================

def calculate_relevance_score(paper: Dict, query: str, weights: Optional[Dict] = None) -> float:
    """
    Calculate multi-factor relevance score

    Scoring factors:
    - Title match (weight: 3.0)
    - Abstract match (weight: 2.0)
    - Citation count (weight: 1.5, normalized)
    - Recency (weight: 1.0)
    - Venue quality (weight: 1.0)
    - Open access (weight: 0.5)

    Args:
        paper: Paper dictionary
        query: Search query
        weights: Optional custom weights dict

    Returns:
        Relevance score (0-10 scale)
    """
    # Default weights
    default_weights = {
        'title_match': 3.0,
        'abstract_match': 2.0,
        'citations': 1.5,
        'recency': 1.0,
        'venue': 1.0,
        'open_access': 0.5
    }

    w = weights if weights else default_weights
    score = 0.0

    # Normalize query
    query_terms = set(query.lower().split())

    # 1. Title match (weight: 3.0)
    title = paper.get('title', '').lower()
    title_words = set(title.split())
    title_match_ratio = len(query_terms & title_words) / len(query_terms) if query_terms else 0
    score += w['title_match'] * title_match_ratio

    # 2. Abstract match (weight: 2.0)
    abstract = paper.get('abstract', '').lower()
    abstract_words = set(abstract.split())
    abstract_match_ratio = len(query_terms & abstract_words) / len(query_terms) if query_terms else 0
    score += w['abstract_match'] * abstract_match_ratio

    # 3. Citation count (weight: 1.5, normalized to 0-1)
    citations = paper.get('citations') or 0  # Handle None from arXiv/PubMed
    if citations is None:
        citations = 0
    # Cap at 100 citations for normalization
    citation_score = min(float(citations) / 100.0, 1.0)
    score += w['citations'] * citation_score

    # 4. Recency (weight: 1.0)
    year = paper.get('year', 2000)
    current_year = datetime.now().year
    years_old = current_year - year
    # Decay over 10 years
    recency_score = max(0, 1.0 - (years_old / 10.0))
    score += w['recency'] * recency_score

    # 5. Venue quality (weight: 1.0)
    venue = paper.get('venue', '').lower()
    top_venues = [
        'nature', 'science', 'cell', 'lancet', 'jama',
        'neurips', 'icml', 'cvpr', 'iclr', 'acl', 'emnlp',
        'aaai', 'ijcai', 'kdd', 'www', 'sigir',
        'ieee', 'acm', 'plos', 'proceedings of the national academy'
    ]

    if any(v in venue for v in top_venues):
        score += w['venue'] * 1.0

    # 6. Open access (weight: 0.5)
    has_pdf = paper.get('pdf_url') or paper.get('isOpenAccess')
    if has_pdf:
        score += w['open_access'] * 0.5

    return score


def rank_by_relevance(papers: List[Dict], query: str, weights: Optional[Dict] = None) -> List[Dict]:
    """
    Rank papers by relevance score

    Args:
        papers: List of paper dictionaries
        query: Search query
        weights: Optional custom weights

    Returns:
        Papers sorted by relevance (highest first), with 'relevance_score' added
    """
    # Calculate scores
    scored_papers = []
    for paper in papers:
        score = calculate_relevance_score(paper, query, weights)
        paper_with_score = {**paper, 'relevance_score': score}
        scored_papers.append(paper_with_score)

    # Sort by score (descending)
    ranked = sorted(scored_papers, key=lambda p: p['relevance_score'], reverse=True)

    return ranked


# ============================================================================
# Phase 1.4: Title-Specific Search
# ============================================================================

def parse_field_query(query: str) -> Dict[str, str]:
    """
    Parse query for field-specific searches

    Supports:
    - title:("search term")
    - abstract:("search term")
    - author:("author name")

    Args:
        query: Search query string

    Returns:
        Dict with fields: {'title': '...', 'abstract': '...', 'default': '...'}
    """
    import re

    fields = {
        'title': None,
        'abstract': None,
        'author': None,
        'default': query  # Fallback to full query
    }

    # Match field:("term") or field:(term)
    patterns = {
        'title': r'title:\s*["\(]([^")\]]+)["\)]',
        'abstract': r'abstract:\s*["\(]([^")\]]+)["\)]',
        'author': r'author:\s*["\(]([^")\]]+)["\)]'
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            fields[field] = match.group(1).strip()
            # Remove field-specific part from default query
            fields['default'] = re.sub(pattern, '', fields['default'], flags=re.IGNORECASE).strip()

    # If no field-specific queries, use the whole query as default
    if not any([fields['title'], fields['abstract'], fields['author']]):
        fields['default'] = query

    return fields


def filter_by_title(papers: List[Dict], title_query: str, exact: bool = False) -> List[Dict]:
    """
    Filter papers by title match

    Args:
        papers: List of paper dictionaries
        title_query: Title search term
        exact: If True, require exact match; if False, require contains

    Returns:
        Filtered papers
    """
    filtered = []
    title_query_lower = title_query.lower()

    for paper in papers:
        title = paper.get('title', '').lower()

        if exact:
            if title == title_query_lower:
                filtered.append(paper)
        else:
            if title_query_lower in title:
                filtered.append(paper)

    return filtered


# ============================================================================
# Combined Smart Search
# ============================================================================

def smart_search_filter(
    papers: List[Dict],
    query: str,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    min_citations: Optional[int] = None,
    adaptive_citations: bool = True,
    rank_by_relevance_score: bool = True
) -> List[Dict]:
    """
    Apply all Phase 1 smart search improvements

    Args:
        papers: List of paper dictionaries
        query: Search query
        min_year: Minimum publication year
        max_year: Maximum publication year
        min_citations: Minimum citation count (if adaptive_citations=False)
        adaptive_citations: Use age-based citation thresholds
        rank_by_relevance_score: Sort by relevance score

    Returns:
        Filtered and ranked papers
    """
    # 1. Date range filtering
    filtered = filter_by_date_range(papers, min_year, max_year)

    # 2. Citation threshold filtering
    filtered = filter_by_citations(filtered, min_citations, adaptive_citations)

    # 3. Relevance ranking
    if rank_by_relevance_score:
        filtered = rank_by_relevance(filtered, query)

    return filtered


# ============================================================================
# Utility Functions
# ============================================================================

def print_search_stats(original_count: int, filtered_count: int, top_n: int = 10):
    """Print search filtering statistics"""
    print(f"\n📊 Smart Search Stats:")
    print(f"   Original results: {original_count}")
    print(f"   After filtering: {filtered_count}")
    print(f"   Reduction: {100 * (1 - filtered_count/original_count):.1f}%")
    print(f"   Showing top: {min(top_n, filtered_count)}")
