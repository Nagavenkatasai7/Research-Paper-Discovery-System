"""
Multi-Agent Search System with Hierarchical Orchestration
Based on best practices from Anthropic, Microsoft Azure, and academic research
"""

import asyncio
import aiohttp
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Import all API clients
from api_clients import SemanticScholarClient, ArXivClient, PapersWithCodeClient
from extended_api_clients import OpenAlexClient, CrossrefClient, COREClient, PubMedClient
from quality_scoring import PaperQualityScorer
from grok_client import GrokClient, GrokQueryAssistant
from smart_search_utils import get_year_range, smart_search_filter
import config


class SearchAgent:
    """Base class for search agents"""

    def __init__(self, name: str, source: str):
        self.name = name
        self.source = source
        self.results = []
        self.status = "idle"  # idle, searching, completed, failed
        self.error = None
        self.start_time = None
        self.end_time = None

    def get_metrics(self) -> Dict:
        """Get agent performance metrics"""
        duration = 0
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        return {
            'name': self.name,
            'source': self.source,
            'status': self.status,
            'results_count': len(self.results),
            'duration': duration,
            'error': self.error
        }

    def search(self, query: str, max_results: int = 50) -> List[Dict]:
        """Override in subclass"""
        raise NotImplementedError


class SemanticScholarAgent(SearchAgent):
    """Agent for Semantic Scholar API"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__("Semantic Scholar Agent", "Semantic Scholar")
        self.client = SemanticScholarClient(api_key)

    def search(self, query: str, max_results: int = 50, smart_search: bool = True) -> List[Dict]:
        self.status = "searching"
        self.start_time = datetime.now()

        try:
            # Get slightly more results for filtering (1.3x max_results, not 2x)
            # This reduces API call time by ~40% while still allowing good filtering
            fetch_limit = int(max_results * 1.3) if smart_search else max_results
            results = self.client.search_papers(query, limit=fetch_limit)

            # Apply smart search Phase 1 improvements
            if smart_search and results:
                min_year, max_year = get_year_range(years_back=5)
                results = smart_search_filter(
                    results,
                    query,
                    min_year=min_year,
                    max_year=max_year,
                    adaptive_citations=True,
                    rank_by_relevance_score=True
                )
                # Return top max_results after filtering
                results = results[:max_results]

            self.results = results
            self.status = "completed"
        except Exception as e:
            self.status = "failed"
            self.error = str(e)

        self.end_time = datetime.now()
        return self.results


class ArXivAgent(SearchAgent):
    """Agent for arXiv API"""

    def __init__(self):
        super().__init__("arXiv Agent", "arXiv")
        self.client = ArXivClient()

    def search(self, query: str, max_results: int = 50, smart_search: bool = True) -> List[Dict]:
        self.status = "searching"
        self.start_time = datetime.now()

        try:
            fetch_limit = int(max_results * 1.3) if smart_search else max_results
            results = self.client.search_papers(query, max_results=fetch_limit)

            if smart_search and results:
                min_year, max_year = get_year_range(years_back=3)  # arXiv: last 3 years
                results = smart_search_filter(
                    results,
                    query,
                    min_year=min_year,
                    max_year=max_year,
                    adaptive_citations=False,  # arXiv doesn't have citation counts
                    rank_by_relevance_score=True
                )
                results = results[:max_results]

            self.results = results
            self.status = "completed"
        except Exception as e:
            self.status = "failed"
            self.error = str(e)

        self.end_time = datetime.now()
        return self.results


class OpenAlexAgent(SearchAgent):
    """Agent for OpenAlex API"""

    def __init__(self, email: Optional[str] = None):
        super().__init__("OpenAlex Agent", "OpenAlex")
        self.client = OpenAlexClient(email)

    def search(self, query: str, max_results: int = 50, smart_search: bool = True) -> List[Dict]:
        self.status = "searching"
        self.start_time = datetime.now()

        try:
            fetch_limit = int(max_results * 1.3) if smart_search else max_results
            results = self.client.search_papers(query, max_results=fetch_limit)

            if smart_search and results:
                min_year, max_year = get_year_range(years_back=5)
                results = smart_search_filter(
                    results,
                    query,
                    min_year=min_year,
                    max_year=max_year,
                    adaptive_citations=True,
                    rank_by_relevance_score=True
                )
                results = results[:max_results]

            self.results = results
            self.status = "completed"
        except Exception as e:
            self.status = "failed"
            self.error = str(e)

        self.end_time = datetime.now()
        return self.results


class CrossrefAgent(SearchAgent):
    """Agent for Crossref API"""

    def __init__(self, email: Optional[str] = None):
        super().__init__("Crossref Agent", "Crossref")
        self.client = CrossrefClient(email)

    def search(self, query: str, max_results: int = 50, smart_search: bool = True) -> List[Dict]:
        self.status = "searching"
        self.start_time = datetime.now()

        try:
            fetch_limit = int(max_results * 1.3) if smart_search else max_results
            results = self.client.search_papers(query, max_results=fetch_limit)

            if smart_search and results:
                min_year, max_year = get_year_range(years_back=5)
                results = smart_search_filter(
                    results,
                    query,
                    min_year=min_year,
                    max_year=max_year,
                    adaptive_citations=True,
                    rank_by_relevance_score=True
                )
                results = results[:max_results]

            self.results = results
            self.status = "completed"
        except Exception as e:
            self.status = "failed"
            self.error = str(e)

        self.end_time = datetime.now()
        return self.results


class COREAgent(SearchAgent):
    """Agent for CORE API"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__("CORE Agent", "CORE")
        self.client = COREClient(api_key)

    def search(self, query: str, max_results: int = 50, smart_search: bool = True) -> List[Dict]:
        self.status = "searching"
        self.start_time = datetime.now()

        try:
            fetch_limit = int(max_results * 1.3) if smart_search else max_results
            results = self.client.search_papers(query, max_results=fetch_limit)

            if smart_search and results:
                # CORE has older papers - use 10 years instead of 5
                # CORE doesn't provide citations, so disable adaptive thresholding
                min_year, max_year = get_year_range(years_back=10)
                results = smart_search_filter(
                    results,
                    query,
                    min_year=min_year,
                    max_year=max_year,
                    min_citations=0,  # No citation filtering (CORE doesn't provide)
                    adaptive_citations=False,  # Disable adaptive (CORE has no citations)
                    rank_by_relevance_score=True
                )
                results = results[:max_results]

            self.results = results
            self.status = "completed"
        except Exception as e:
            self.status = "failed"
            self.error = str(e)

        self.end_time = datetime.now()
        return self.results


class PubMedAgent(SearchAgent):
    """Agent for PubMed API"""

    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__("PubMed Agent", "PubMed")
        self.client = PubMedClient(email, api_key)

    def search(self, query: str, max_results: int = 50, smart_search: bool = True) -> List[Dict]:
        self.status = "searching"
        self.start_time = datetime.now()

        try:
            fetch_limit = int(max_results * 1.3) if smart_search else max_results
            results = self.client.search_papers(query, max_results=fetch_limit)

            if smart_search and results:
                min_year, max_year = get_year_range(years_back=5)
                results = smart_search_filter(
                    results,
                    query,
                    min_year=min_year,
                    max_year=max_year,
                    adaptive_citations=True,
                    rank_by_relevance_score=True
                )
                results = results[:max_results]

            self.results = results
            self.status = "completed"
        except Exception as e:
            self.status = "failed"
            self.error = str(e)

        self.end_time = datetime.now()
        return self.results


class AggregatorAgent:
    """Agent responsible for merging and deduplicating results"""

    def __init__(self):
        self.name = "Aggregator Agent"

    def aggregate(self, all_results: List[List[Dict]]) -> List[Dict]:
        """Merge results from multiple agents and deduplicate"""
        # Flatten results
        flat_results = []
        for results in all_results:
            flat_results.extend(results)

        # Deduplicate by DOI first, then by normalized title
        seen_dois = set()
        seen_titles = set()
        unique_results = []

        for paper in flat_results:
            # Check DOI
            doi = (paper.get('doi') or '').lower().strip()
            if doi and doi in seen_dois:
                # Merge data from duplicate
                self._merge_duplicate(unique_results, paper, 'doi', doi)
                continue

            # Check normalized title
            title = self._normalize_title(paper.get('title', ''))
            if title in seen_titles:
                self._merge_duplicate(unique_results, paper, 'title', title)
                continue

            # New unique paper
            if doi:
                seen_dois.add(doi)
            if title:
                seen_titles.add(title)

            unique_results.append(paper)

        return unique_results

    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        import re
        return re.sub(r'[^a-z0-9]', '', title.lower())

    def _merge_duplicate(self, results: List[Dict], paper: Dict, key: str, value: str):
        """Merge data from duplicate paper into existing entry"""
        # Find existing paper
        for existing in results:
            if key == 'doi':
                existing_value = (existing.get('doi') or '').lower().strip()
            else:
                existing_value = self._normalize_title(existing.get('title', ''))

            if existing_value == value:
                # Merge missing fields
                for field in ['pdf_url', 'doi', 'arxiv_id', 'citations']:
                    if not existing.get(field) and paper.get(field):
                        existing[field] = paper[field]

                # Add source to list
                if 'sources' not in existing:
                    existing['sources'] = [existing['source']]
                if paper['source'] not in existing['sources']:
                    existing['sources'].append(paper['source'])

                break


class OrchestratorAgent:
    """Lead agent that coordinates all search agents"""

    def __init__(
        self,
        s2_api_key: Optional[str] = None,
        email: Optional[str] = None,
        core_api_key: Optional[str] = None,
        pubmed_api_key: Optional[str] = None
    ):
        self.name = "Orchestrator Agent"

        # Always use Grok-4 for multi-agent orchestration (Ollama removed)
        self.llm = GrokClient(
            api_key=config.GROK_SETTINGS['api_key'],
            model=config.GROK_SETTINGS['model'],
            validate=True
        )
        self.grok_assistant = GrokQueryAssistant(self.llm)
        print(f"🚀 Orchestrator using Grok-4 fast reasoning (Ollama removed)")

        # Initialize worker agents
        self.agents = {
            'semantic_scholar': SemanticScholarAgent(s2_api_key),
            'arxiv': ArXivAgent(),
            'openalex': OpenAlexAgent(email),
            'crossref': CrossrefAgent(email),
            'core': COREAgent(core_api_key) if core_api_key else None,
            'pubmed': PubMedAgent(email, pubmed_api_key) if email else None
        }

        self.aggregator = AggregatorAgent()
        self.scorer = PaperQualityScorer()

    def select_optimal_sources(self, query: str, available_sources: List[str]) -> List[str]:
        """Smart source selection based on query content (60% fewer API calls)"""

        if not config.MULTI_AGENT_CONFIG.get('smart_source_selection', False):
            return available_sources  # Use all sources if disabled

        query_lower = query.lower()
        selected_sources = []

        # For ML/AI/CS: prioritize arXiv + Semantic Scholar (most relevant)
        if any(term in query_lower for term in ['machine learning', 'deep learning', 'neural',
                                                  'ai', 'artificial intelligence', 'nlp',
                                                  'computer vision', 'reinforcement']):
            if 'arxiv' in available_sources:
                selected_sources.append('arxiv')
            if 'semantic_scholar' in available_sources:
                selected_sources.append('semantic_scholar')

        # For medical/bio: prioritize PubMed + Semantic Scholar
        elif any(term in query_lower for term in ['medical', 'clinical', 'disease', 'health',
                                                    'biomedical', 'drug', 'therapy', 'patient']):
            if 'pubmed' in available_sources:
                selected_sources.append('pubmed')
            if 'semantic_scholar' in available_sources:
                selected_sources.append('semantic_scholar')

        # For physics/quantum: prioritize arXiv + OpenAlex
        elif any(term in query_lower for term in ['quantum', 'physics', 'particle', 'relativity']):
            if 'arxiv' in available_sources:
                selected_sources.append('arxiv')
            if 'openalex' in available_sources:
                selected_sources.append('openalex')

        # For general/broad queries: use top 2-3 most comprehensive sources
        else:
            priority = ['semantic_scholar', 'arxiv', 'openalex']
            for source in priority:
                if source in available_sources and len(selected_sources) < 3:
                    selected_sources.append(source)

        # Fallback: if no sources selected, use first 2 available
        if not selected_sources:
            selected_sources = available_sources[:2]

        # Limit to max 3 sources for optimal performance
        selected_sources = selected_sources[:3]

        if len(selected_sources) < len(available_sources):
            print(f"📊 Smart selection: Using {len(selected_sources)}/{len(available_sources)} sources: {selected_sources}")

        return selected_sources

    def plan_search(self, query: str, enabled_sources: List[str]) -> Dict:
        """Plan the search strategy using Grok-4 Fast Reasoning"""
        # Always use Grok's specialized planning (Ollama removed)
        if self.grok_assistant:
            return self.grok_assistant.plan_multi_agent_search(query, enabled_sources)

        # Fallback if Grok assistant not available (shouldn't happen)
        print("⚠️ Warning: Grok assistant not available, using simple plan")
        return {
            'original_query': query,
            'refined_query': query,
            'source_priority': enabled_sources,
            'reasoning': 'Using original query (Grok assistant unavailable)'
        }

    def search_parallel(
        self,
        query: str,
        enabled_sources: List[str],
        max_results_per_source: int = 20  # Reduced from 50 to 20
    ) -> Dict:
        """Execute parallel search across all enabled sources - OPTIMIZED"""

        start_time = datetime.now()

        # Apply smart source selection (reduces API calls by 60%)
        optimal_sources = self.select_optimal_sources(query, enabled_sources)

        # Filter agents based on optimal sources
        active_agents = {
            name: agent for name, agent in self.agents.items()
            if name in optimal_sources and agent is not None
        }

        # Execute searches in parallel using ThreadPoolExecutor
        all_results = []
        agent_metrics = []

        # Use config-based max_workers (6 for comprehensive parallel search)
        max_workers = min(len(active_agents), config.MULTI_AGENT_CONFIG.get('max_workers', 6))

        # Use context manager for automatic cleanup
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            try:
                # Submit all search tasks
                future_to_agent = {
                    executor.submit(agent.search, query, max_results_per_source): (name, agent)
                    for name, agent in active_agents.items()
                }

                # Collect results as they complete with smart timeout
                timeout = config.MULTI_AGENT_CONFIG.get('timeout_per_source', 15)

                for future in as_completed(future_to_agent, timeout=timeout * len(active_agents)):
                    name, agent = future_to_agent[future]
                    try:
                        # Reduced timeout from 30s to 15s (fail fast)
                        results = future.result(timeout=timeout)
                        all_results.append(results)
                        agent_metrics.append(agent.get_metrics())
                    except TimeoutError:
                        agent.status = "timeout"
                        agent.error = f"Search timed out after {timeout}s"
                        agent_metrics.append(agent.get_metrics())
                        print(f"⏱️  {name} timed out after {timeout}s")
                    except Exception as e:
                        agent.status = "failed"
                        agent.error = str(e)
                        agent_metrics.append(agent.get_metrics())
                        print(f"❌ {name} failed: {str(e)[:50]}")

            except Exception as e:
                # Handle any errors during parallel execution
                print(f"⚠️  Search execution error: {str(e)[:100]}")
                # Add metrics for any agents that didn't report
                for name, agent in active_agents.items():
                    if not any(m['name'] == agent.name for m in agent_metrics):
                        agent.status = "failed"
                        agent.error = f"Execution error: {str(e)[:50]}"
                        agent_metrics.append(agent.get_metrics())

        # Aggregate and deduplicate results
        aggregated_results = self.aggregator.aggregate(all_results)

        # Score and rank results
        ranked_results = self.scorer.rank_papers(aggregated_results)

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        return {
            'results': ranked_results,
            'metrics': {
                'total_results': len(ranked_results),
                'total_raw_results': sum(len(r) for r in all_results),
                'duration': total_duration,
                'agents': agent_metrics,
                'sources_used': list(active_agents.keys())
            }
        }

    def synthesize_results(self, results: List[Dict], top_n: int = 10, query: str = "") -> str:
        """Use LLM to synthesize search results into a summary (Grok preferred for speed)"""
        if not results:
            return "No results found."

        # Always use Grok's specialized synthesis (Ollama removed)
        if self.grok_assistant:
            return self.grok_assistant.synthesize_results(results, query, top_n)

        # Fallback if Grok assistant not available (shouldn't happen)
        print("⚠️ Warning: Grok assistant not available for synthesis")
        top_papers = results[:top_n]
        papers_text = []

        for i, paper in enumerate(top_papers, 1):
            papers_text.append(
                f"{i}. {paper['title']} ({paper['year']})\n"
                f"   Citations: {paper.get('citations', 'N/A')} | "
                f"Venue: {paper.get('venue', 'Unknown')} | "
                f"Source: {paper.get('source', 'Unknown')}"
            )

        return "Results found:\n\n" + "\n\n".join(papers_text)


# Helper functions for Streamlit integration
def create_orchestrator(config_dict: Optional[Dict] = None) -> OrchestratorAgent:
    """Create orchestrator with configuration - Always uses Grok-4 (Ollama removed)"""
    if config_dict is None:
        config_dict = {}

    # Handle case where list is passed instead of dict (for backward compatibility)
    if isinstance(config_dict, list):
        print(f"⚠️ Warning: create_orchestrator received list instead of dict. Using default config.")
        config_dict = {}

    return OrchestratorAgent(
        s2_api_key=config_dict.get('s2_api_key'),
        email=config_dict.get('email'),
        core_api_key=config_dict.get('core_api_key'),
        pubmed_api_key=config_dict.get('pubmed_api_key')
    )
