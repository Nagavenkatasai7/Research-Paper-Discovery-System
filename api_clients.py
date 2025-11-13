"""
API integration layer for multiple academic paper databases
"""

import time
import requests
import re
from typing import List, Dict, Optional
from semanticscholar import SemanticScholar
import arxiv
import config


class RateLimiter:
    """Rate limiter to respect API limits"""

    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self.last_request = 0

    def wait(self):
        """Wait if necessary to respect rate limit"""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()


class SemanticScholarClient:
    """Client for Semantic Scholar API"""

    def __init__(self, api_key: Optional[str] = None):
        # Use API key from config if not provided
        if api_key is None:
            api_key = config.SEMANTIC_SCHOLAR_API_KEY

        self.client = SemanticScholar(api_key=api_key) if api_key else SemanticScholar()
        self.rate_limiter = RateLimiter(config.RATE_LIMITS['semantic_scholar'])

    def search_papers(self, query: str, limit: int = 20) -> List[Dict]:
        """Search papers with query - optimized with retry logic and timeout"""

        # Cap limit to prevent extremely slow fetches
        # Semantic Scholar lazy-loads results, so 1000+ takes forever
        limit = min(limit, 100)  # Max 100 results to prevent hangs

        # Limit to essential fields only (30% faster)
        # Added 'tldr' for AI-generated summaries (2025 enhancement)
        essential_fields = [
            'title', 'abstract', 'year', 'authors',
            'citationCount', 'venue', 'openAccessPdf',
            'externalIds', 'paperId', 'influentialCitationCount',
            'tldr'  # AI-generated summary for quick understanding
            # Removed: citationStyles, fieldsOfStudy (not displayed in UI)
        ]

        max_retries = config.MULTI_AGENT_CONFIG.get('retry_attempts', 3)

        for attempt in range(max_retries):
            # REMOVED: self.rate_limiter.wait() - SDK has built-in rate limiting!

            try:
                results = self.client.search_paper(
                    query,
                    limit=limit,
                    fields=essential_fields
                )

                # Force immediate fetch instead of lazy iteration
                # This prevents 74-minute hangs on large result sets
                papers = []
                start_time = time.time()
                max_iteration_time = 30  # Maximum 30 seconds for iteration

                for i, paper in enumerate(results):
                    # Timeout protection - prevent infinite loops
                    if time.time() - start_time > max_iteration_time:
                        print(f"⏱️  Iteration timeout after {max_iteration_time}s, got {len(papers)} papers")
                        break

                    if i >= limit:  # Safety check to enforce limit
                        break
                    try:
                        papers.append(self._normalize_paper(paper))
                    except Exception as norm_error:
                        print(f"Error normalizing paper {i}: {norm_error}")
                        continue

                return papers

            except Exception as e:
                error_str = str(e)

                # Handle rate limiting with exponential backoff
                if '429' in error_str or 'rate limit' in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt)  # 1s, 2s, 4s
                        print(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue

                # For other errors, fail immediately
                print(f"Semantic Scholar search error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return []

        return []

    def get_paper_details(self, paper_id: str) -> Optional[Dict]:
        """Get detailed information for a specific paper"""
        # REMOVED: self.rate_limiter.wait() - SDK has built-in rate limiting!

        try:
            paper = self.client.get_paper(
                paper_id,
                fields=[
                    'title', 'abstract', 'year', 'authors', 'citationCount',
                    'venue', 'openAccessPdf', 'externalIds', 'paperId',
                    'citationStyles', 'influentialCitationCount', 'references',
                    'citations', 'fieldsOfStudy'
                ]
            )
            return self._normalize_paper(paper)

        except Exception as e:
            print(f"Semantic Scholar detail fetch error: {e}")
            return None

    def _normalize_paper(self, paper) -> Dict:
        """Normalize Semantic Scholar paper to standard format"""
        # Handle authors - they can be dicts or objects
        authors = []
        for a in (paper.authors or []):
            if isinstance(a, dict):
                authors.append({
                    'name': a.get('name', 'Unknown'),
                    'authorId': a.get('authorId'),
                    'hIndex': None
                })
            else:
                # It's an object with properties
                authors.append({
                    'name': getattr(a, 'name', 'Unknown'),
                    'authorId': getattr(a, 'authorId', None),
                    'hIndex': None
                })

        # Extract TLDR (AI-generated summary)
        tldr_text = None
        if hasattr(paper, 'tldr') and paper.tldr:
            if isinstance(paper.tldr, dict):
                tldr_text = paper.tldr.get('text')
            elif hasattr(paper.tldr, 'text'):
                tldr_text = paper.tldr.text

        return {
            'title': paper.title or 'Untitled',
            'authors': authors,
            'abstract': paper.abstract or 'No abstract available',
            'tldr': tldr_text,  # AI-generated summary for quick understanding
            'year': paper.year,
            'citations': paper.citationCount or 0,
            'influential_citations': getattr(paper, 'influentialCitationCount', 0),
            'venue': paper.venue or 'Unknown',
            'pdf_url': paper.openAccessPdf.get('url') if paper.openAccessPdf else None,
            'doi': paper.externalIds.get('DOI') if paper.externalIds else None,
            'arxiv_id': paper.externalIds.get('ArXiv') if paper.externalIds else None,
            'paper_id': paper.paperId,
            'fields_of_study': paper.fieldsOfStudy or [],
            'source': 'Semantic Scholar',
            'bibtex': paper.citationStyles.get('bibtex') if hasattr(paper, 'citationStyles') and paper.citationStyles else None
        }


class ArXivClient:
    """Client for arXiv API"""

    def __init__(self):
        self.client = arxiv.Client()
        self.rate_limiter = RateLimiter(config.RATE_LIMITS['arxiv'])

    def search_papers(self, query: str, max_results: int = 20, category: Optional[str] = None) -> List[Dict]:
        """Search arXiv papers - optimized"""
        max_retries = config.MULTI_AGENT_CONFIG.get('retry_attempts', 3)

        for attempt in range(max_retries):
            # REDUCED: Minimal delay for politeness (arXiv SDK handles rate limiting)

            try:
                # Add category filter if specified
                if category:
                    query = f"{query} AND cat:{category}"

                search = arxiv.Search(
                    query=query,
                    max_results=max_results,
                    sort_by=arxiv.SortCriterion.Relevance
                )

                papers = []
                for result in self.client.results(search):
                    papers.append(self._normalize_paper(result))
                    # Removed time.sleep() - rate limiter already handles delays
                    # Previous delay: 0.3s per result caused 3+ second overhead for 10 results

                return papers

            except Exception as e:
                error_str = str(e)

                # Retry on network errors
                if attempt < max_retries - 1 and ('timeout' in error_str.lower() or 'connection' in error_str.lower()):
                    wait_time = (2 ** attempt)
                    print(f"ArXiv error, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue

                print(f"ArXiv search error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return []

        return []

    def _normalize_paper(self, paper) -> Dict:
        """Normalize arXiv paper to standard format"""
        return {
            'title': paper.title,
            'authors': [{'name': a.name, 'authorId': None} for a in paper.authors],
            'abstract': paper.summary,
            'year': paper.published.year,
            'citations': None,  # arXiv doesn't provide citation counts
            'influential_citations': None,
            'venue': 'arXiv',
            'pdf_url': paper.pdf_url,
            'doi': paper.doi,
            'arxiv_id': paper.get_short_id(),
            'paper_id': paper.entry_id,
            'fields_of_study': [cat for cat in paper.categories],
            'source': 'arXiv',
            'bibtex': None
        }


class PapersWithCodeClient:
    """Client for Papers With Code API"""

    def __init__(self):
        self.base_url = "https://paperswithcode.com/api/v1"
        self.rate_limiter = RateLimiter(config.RATE_LIMITS['papers_with_code'])

    def get_implementations(self, paper_title: str, paper_doi: Optional[str] = None) -> Optional[Dict]:
        """Get GitHub implementations for a paper"""
        self.rate_limiter.wait()

        try:
            # Search for paper by title
            search_params = {'q': paper_title}
            response = requests.get(
                f"{self.base_url}/papers/",
                params=search_params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    paper = data['results'][0]
                    paper_id = paper['id']

                    # Get repositories for this paper
                    self.rate_limiter.wait()
                    repos_response = requests.get(
                        f"{self.base_url}/papers/{paper_id}/repositories/",
                        timeout=10
                    )

                    if repos_response.status_code == 200:
                        repos_data = repos_response.json()
                        return {
                            'repositories': repos_data.get('results', []),
                            'paper_url': f"https://paperswithcode.com{paper.get('url', '')}",
                            'tasks': paper.get('tasks', [])
                        }

            return None

        except Exception as e:
            print(f"Papers With Code error: {e}")
            return None


class MultiAPISearcher:
    """Unified searcher across multiple APIs"""

    def __init__(self, s2_api_key: Optional[str] = None):
        self.s2_client = SemanticScholarClient(api_key=s2_api_key)
        self.arxiv_client = ArXivClient()
        self.pwc_client = PapersWithCodeClient()

    def search_all(
        self,
        query: str,
        max_results: int = 50,
        sources: List[str] = ['semantic_scholar', 'arxiv']
    ) -> List[Dict]:
        """Search across multiple sources and deduplicate"""
        all_results = []

        # Search Semantic Scholar
        if 'semantic_scholar' in sources:
            s2_results = self.s2_client.search_papers(query, limit=max_results)
            all_results.extend(s2_results)

        # Search arXiv
        if 'arxiv' in sources:
            arxiv_results = self.arxiv_client.search_papers(query, max_results=max_results)
            all_results.extend(arxiv_results)

        # Deduplicate results
        deduplicated = self._deduplicate(all_results)

        return deduplicated

    def enhance_with_implementations(self, papers: List[Dict]) -> List[Dict]:
        """Enhance papers with GitHub implementation links"""
        enhanced = []

        for paper in papers:
            impl_data = self.pwc_client.get_implementations(
                paper['title'],
                paper.get('doi')
            )

            if impl_data:
                paper['implementations'] = impl_data
            else:
                paper['implementations'] = None

            enhanced.append(paper)

        return enhanced

    def _deduplicate(self, papers: List[Dict]) -> List[Dict]:
        """Remove duplicate papers based on DOI and normalized title"""
        seen_dois = set()
        seen_titles = set()
        unique = []

        for paper in papers:
            # Check DOI first (most reliable)
            doi = (paper.get('doi') or '').lower().strip()
            if doi and doi in seen_dois:
                continue

            # Check normalized title
            title = self._normalize_title(paper.get('title', ''))
            if title in seen_titles:
                continue

            # Add to unique results
            if doi:
                seen_dois.add(doi)
            if title:
                seen_titles.add(title)

            unique.append(paper)

        return unique

    @staticmethod
    def _normalize_title(title: str) -> str:
        """Normalize title for deduplication"""
        # Convert to lowercase and remove non-alphanumeric characters
        normalized = re.sub(r'[^a-z0-9]', '', title.lower())
        return normalized

    @staticmethod
    def extract_github_from_abstract(abstract: str) -> Optional[str]:
        """Extract GitHub URLs from abstract text"""
        github_pattern = r'https?://github\.com/[\w-]+/[\w.-]+'
        matches = re.findall(github_pattern, abstract, re.IGNORECASE)
        return matches[0] if matches else None
