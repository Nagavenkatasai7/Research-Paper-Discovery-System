"""
Grok API Integration
Fast and efficient LLM client using Grok-4 for multi-agent orchestration
"""

import requests
from typing import List, Dict, Optional
import sys
import time

# Conditional Streamlit import to avoid cache warnings in non-Streamlit contexts
_is_streamlit = 'streamlit' in sys.modules and hasattr(sys.modules.get('streamlit'), 'runtime') and hasattr(sys.modules['streamlit'].runtime, 'exists')

if _is_streamlit:
    import streamlit as st
else:
    # Create dummy decorators when not in Streamlit context
    class DummySt:
        @staticmethod
        def cache_resource(func):
            return func
        @staticmethod
        def cache_data(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
    st = DummySt()


class GrokClient:
    """Client for Grok API (xAI)"""

    def __init__(self, api_key: str, model: str = "grok-4-fast-reasoning", validate: bool = True):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.x.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.is_validated = False

        # Validate API key on initialization if requested
        if validate:
            self.validate_connection()

    def validate_connection(self, timeout: int = 5) -> bool:
        """
        Validate API connection with a simple test request
        Returns True if connection is valid, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5
                },
                timeout=timeout
            )

            if response.status_code == 200:
                self.is_validated = True
                return True
            elif response.status_code == 401:
                raise ValueError("Invalid API key - authentication failed")
            elif response.status_code == 429:
                raise ValueError("Rate limit exceeded - too many requests")
            else:
                raise ValueError(f"API returned status code {response.status_code}")

        except requests.exceptions.Timeout:
            raise ValueError(f"Connection timeout after {timeout} seconds - API may be unavailable")
        except requests.exceptions.ConnectionError:
            raise ValueError("Could not connect to Grok API - check your internet connection")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Request failed: {str(e)}")

        return False

    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate text from prompt"""
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content']
            else:
                return "Error: No response from Grok API"

        except requests.exceptions.Timeout:
            return "Error: Grok API request timed out"
        except requests.exceptions.RequestException as e:
            return f"Error: Grok API request failed - {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Chat-based generation with conversation history"""
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content']
            else:
                return "Error: No response from Grok API"

        except Exception as e:
            return f"Error in Grok chat: {str(e)}"

    def batch_generate(self, prompts: List[str], max_tokens: int = 500) -> List[str]:
        """Generate responses for multiple prompts (sequential for now)"""
        results = []
        for prompt in prompts:
            result = self.generate(prompt, max_tokens=max_tokens)
            results.append(result)
            time.sleep(0.1)  # Small delay to avoid rate limits
        return results


class GrokPaperAnalyzer:
    """Analyze research papers using Grok-4"""

    def __init__(self, grok_client: GrokClient):
        self.grok = grok_client

    def summarize_paper(self, paper: Dict) -> str:
        """Generate a concise summary of a paper using Grok"""
        title = paper.get('title', 'Unknown')
        abstract = paper.get('abstract', 'No abstract available')
        year = paper.get('year', 'N/A')
        authors = ', '.join([a.get('name', 'Unknown') for a in paper.get('authors', [])[:3]])

        prompt = f"""You are a research assistant. Provide a concise 3-4 sentence summary of this research paper.
Focus on: (1) Main problem addressed, (2) Key approach/method, (3) Main findings/contributions.

Title: {title}
Authors: {authors}
Year: {year}
Abstract: {abstract[:1000]}

Summary:"""

        return self.grok.generate(prompt, max_tokens=300, temperature=0.5)

    def extract_key_insights(self, paper: Dict) -> Dict[str, str]:
        """Extract structured insights from a paper"""
        title = paper.get('title', 'Unknown')
        abstract = paper.get('abstract', 'No abstract available')

        prompt = f"""Analyze this research paper and extract key information in a structured format.

Title: {title}
Abstract: {abstract[:1000]}

Provide:
1. Main Problem: (1 sentence - what problem does this paper address?)
2. Key Method: (1 sentence - what is the main approach or technique?)
3. Main Contribution: (1 sentence - what is the key innovation or finding?)
4. Limitations: (1 sentence - what are potential limitations or future work?)

Format your response as:
Main Problem: ...
Key Method: ...
Main Contribution: ...
Limitations: ..."""

        response = self.grok.generate(prompt, max_tokens=400, temperature=0.5)

        # Parse structured response
        insights = {}
        for line in response.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                insights[key.strip()] = value.strip()

        return insights

    def compare_papers(self, papers: List[Dict]) -> str:
        """Compare multiple papers"""
        if len(papers) < 2:
            return "Need at least 2 papers to compare"

        papers_info = []
        for i, paper in enumerate(papers[:3], 1):
            title = paper.get('title', 'Unknown')
            abstract = paper.get('abstract', 'No abstract')[:300]
            papers_info.append(f"Paper {i}: {title}\nAbstract: {abstract}")

        papers_text = "\n\n".join(papers_info)

        prompt = f"""Compare these research papers and identify:
1. Common themes or problems they address
2. Different approaches or methods they use
3. How they differ in their contributions

{papers_text}

Comparison:"""

        return self.grok.generate(prompt, max_tokens=600, temperature=0.6)


class GrokQueryAssistant:
    """Assist with query formulation using Grok's fast reasoning"""

    def __init__(self, grok_client: GrokClient):
        self.grok = grok_client

    def suggest_better_queries(self, original_query: str, domain: Optional[str] = None) -> List[str]:
        """Suggest improved search queries using Grok's reasoning"""
        domain_context = f" in the domain of {domain}" if domain else ""

        prompt = f"""You are a research librarian helping formulate better academic search queries.

Original query: "{original_query}"
Research domain{domain_context}

Suggest 5 alternative or improved search queries that would help find relevant academic papers.
Make them more specific, use technical terms, and consider different phrasings.

Provide one query per line, without numbering or bullets:"""

        response = self.grok.generate(prompt, max_tokens=300, temperature=0.7)

        # Parse suggestions
        suggestions = [
            line.strip()
            for line in response.split('\n')
            if line.strip() and not line.strip().startswith('#') and len(line.strip()) > 10
        ]

        return suggestions[:5]

    def expand_query_with_keywords(self, query: str) -> List[str]:
        """Suggest related keywords using Grok's fast reasoning"""
        prompt = f"""Given this research query: "{query}"

Suggest 8 related technical keywords, concepts, or phrases that researchers should consider.
These should be specific technical terms commonly used in academic papers.

Provide one keyword/phrase per line, without numbering:"""

        response = self.grok.generate(prompt, max_tokens=250, temperature=0.6)

        keywords = [
            line.strip()
            for line in response.split('\n')
            if line.strip() and len(line.strip()) > 2 and not line.startswith('-')
        ]

        return keywords[:8]

    def plan_multi_agent_search(self, query: str, available_sources: List[str]) -> Dict:
        """Use Grok to plan an optimal multi-agent search strategy"""
        sources_str = ', '.join(available_sources)

        prompt = f"""You are an AI research orchestrator. Plan an optimal search strategy for this query.

Query: "{query}"
Available sources: {sources_str}

Analyze the query and provide:
1. Refined Query: An improved version with technical terms
2. Source Priority: Which sources to prioritize (comma-separated)
3. Key Terms: 5 essential keywords to focus on
4. Strategy: 2-sentence search strategy

Format your response exactly as:
Refined Query: [your refined query]
Source Priority: [sources in priority order]
Key Terms: [term1, term2, term3, term4, term5]
Strategy: [your strategy]"""

        response = self.grok.generate(prompt, max_tokens=400, temperature=0.5)

        # Parse response
        plan = {
            'original_query': query,
            'refined_query': query,
            'source_priority': available_sources,
            'key_terms': [],
            'reasoning': ''
        }

        for line in response.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                if key == 'Refined Query':
                    plan['refined_query'] = value
                elif key == 'Source Priority':
                    plan['source_priority'] = [s.strip() for s in value.split(',')]
                elif key == 'Key Terms':
                    plan['key_terms'] = [t.strip() for t in value.split(',')]
                elif key == 'Strategy':
                    plan['reasoning'] = value

        return plan

    def synthesize_results(self, papers: List[Dict], query: str, top_n: int = 10) -> str:
        """Synthesize findings from multiple papers using Grok"""
        if not papers:
            return "No papers to synthesize"

        papers_info = []
        for paper in papers[:top_n]:
            title = paper.get('title', 'Unknown')
            abstract = paper.get('abstract', 'No abstract')[:200]
            year = paper.get('year', 'N/A')
            citations = paper.get('citations', 0)
            papers_info.append(f"[{year}, {citations} cites] {title}\n{abstract}")

        papers_text = "\n\n".join(papers_info)

        prompt = f"""Synthesize the key findings from these research papers related to: "{query}"

Papers:
{papers_text}

Provide a 4-5 sentence synthesis covering:
1. Main themes across papers
2. Key innovations or trends
3. Common approaches
4. Gaps or future directions

Synthesis:"""

        return self.grok.generate(prompt, max_tokens=500, temperature=0.6)


# Cached functions for Streamlit
@st.cache_resource
def get_grok_client(api_key: str, model: str = "grok-4-fast-reasoning", _validate: bool = True) -> Optional[GrokClient]:
    """
    Get cached Grok client with validation
    Returns None if validation fails
    """
    try:
        client = GrokClient(api_key, model, validate=_validate)
        return client
    except ValueError as e:
        # Log error but don't crash - return None to indicate failure
        print(f"Grok client initialization failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error initializing Grok client: {e}")
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def cached_grok_summarize(_grok_client: GrokClient, paper_id: str, paper: Dict) -> str:
    """Cached paper summarization using Grok"""
    analyzer = GrokPaperAnalyzer(_grok_client)
    return analyzer.summarize_paper(paper)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_grok_insights(_grok_client: GrokClient, paper_id: str, paper: Dict) -> Dict:
    """Cached insights extraction using Grok"""
    analyzer = GrokPaperAnalyzer(_grok_client)
    return analyzer.extract_key_insights(paper)


@st.cache_data(ttl=1800, show_spinner=False)
def cached_grok_suggest_queries(_grok_client: GrokClient, query: str, domain: Optional[str] = None) -> List[str]:
    """Cached query suggestions using Grok"""
    assistant = GrokQueryAssistant(_grok_client)
    return assistant.suggest_better_queries(query, domain)


@st.cache_data(ttl=1800, show_spinner=False)
def cached_grok_expand_keywords(_grok_client: GrokClient, query: str) -> List[str]:
    """Cached keyword expansion using Grok"""
    assistant = GrokQueryAssistant(_grok_client)
    return assistant.expand_query_with_keywords(query)


@st.cache_data(ttl=600, show_spinner=False)
def cached_grok_plan_search(_grok_client: GrokClient, query: str, sources: tuple) -> Dict:
    """Cached search planning using Grok"""
    assistant = GrokQueryAssistant(_grok_client)
    return assistant.plan_multi_agent_search(query, list(sources))


@st.cache_data(ttl=600, show_spinner=False)
def cached_grok_synthesize(_grok_client: GrokClient, query: str, papers_hash: str, papers: List[Dict], top_n: int) -> str:
    """Cached result synthesis using Grok"""
    assistant = GrokQueryAssistant(_grok_client)
    return assistant.synthesize_results(papers, query, top_n)
