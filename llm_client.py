"""
Local LLM Integration via Ollama
Provides paper summarization, insights extraction, Q&A, and query enhancement
"""

import ollama
from typing import List, Dict, Optional
import sys

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


class OllamaLLMClient:
    """Client for interacting with local Ollama models"""

    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.available_models = self._get_available_models()

    def _get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            models = ollama.list()
            return [model['name'] for model in models.get('models', [])]
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []

    def set_model(self, model_name: str):
        """Switch to a different model"""
        if model_name in self.available_models:
            self.model_name = model_name
        else:
            raise ValueError(f"Model {model_name} not found in available models")

    def generate(self, prompt: str, stream: bool = False) -> str:
        """Generate text from prompt"""
        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                stream=stream
            )

            if stream:
                return response  # Return generator for streaming
            else:
                return response.get('response', '')

        except Exception as e:
            return f"Error generating response: {str(e)}"

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Chat-based generation"""
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=messages
            )
            return response['message']['content']
        except Exception as e:
            return f"Error in chat: {str(e)}"


class PaperAnalyzer:
    """Analyze research papers using LLM"""

    def __init__(self, llm_client: OllamaLLMClient):
        self.llm = llm_client

    def summarize_paper(self, paper: Dict) -> str:
        """Generate a concise summary of a paper"""
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

        return self.llm.generate(prompt)

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
Limitations: ...
"""

        response = self.llm.generate(prompt)

        # Parse structured response
        insights = {}
        for line in response.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                insights[key.strip()] = value.strip()

        return insights

    def answer_question_about_paper(self, paper: Dict, question: str) -> str:
        """Answer a specific question about a paper"""
        title = paper.get('title', 'Unknown')
        abstract = paper.get('abstract', 'No abstract available')
        year = paper.get('year', 'N/A')

        prompt = f"""You are a research assistant. Answer the following question about this paper based on the available information.

Paper Title: {title}
Year: {year}
Abstract: {abstract}

Question: {question}

Answer (be concise and specific):"""

        return self.llm.generate(prompt)

    def compare_papers(self, papers: List[Dict]) -> str:
        """Compare multiple papers and highlight differences"""
        if len(papers) < 2:
            return "Need at least 2 papers to compare"

        papers_info = []
        for i, paper in enumerate(papers[:3], 1):  # Limit to 3 papers
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

        return self.llm.generate(prompt)


class QueryAssistant:
    """Assist with query formulation and enhancement"""

    def __init__(self, llm_client: OllamaLLMClient):
        self.llm = llm_client

    def suggest_better_queries(self, original_query: str, domain: Optional[str] = None) -> List[str]:
        """Suggest improved search queries"""
        domain_context = f" in the domain of {domain}" if domain else ""

        prompt = f"""You are a research librarian helping formulate better academic search queries.

Original query: "{original_query}"
Research domain{domain_context}

Suggest 5 alternative or improved search queries that would help find relevant academic papers.
Make them more specific, use technical terms, and consider different phrasings.

Provide one query per line, without numbering:"""

        response = self.llm.generate(prompt)

        # Parse suggestions
        suggestions = [
            line.strip()
            for line in response.split('\n')
            if line.strip() and not line.strip().startswith('#')
        ]

        return suggestions[:5]  # Limit to 5 suggestions

    def expand_query_with_keywords(self, query: str) -> List[str]:
        """Suggest related keywords and concepts"""
        prompt = f"""Given this research query: "{query}"

Suggest 10 related technical keywords, concepts, or phrases that researchers should consider.
These should be specific technical terms commonly used in academic papers.

Provide one keyword/phrase per line:"""

        response = self.llm.generate(prompt)

        keywords = [
            line.strip()
            for line in response.split('\n')
            if line.strip() and len(line.strip()) > 2
        ]

        return keywords[:10]

    def identify_research_area(self, query: str) -> str:
        """Identify the main research area from a query"""
        prompt = f"""Identify the primary research area or field for this query: "{query}"

Choose from: Machine Learning, Natural Language Processing, Computer Vision,
Reinforcement Learning, AI Agents, Quantum Computing, Robotics, or specify another area.

Respond with just the research area name:"""

        return self.llm.generate(prompt).strip()


class LiteratureReviewAssistant:
    """Help with literature review tasks"""

    def __init__(self, llm_client: OllamaLLMClient):
        self.llm = llm_client

    def generate_research_questions(self, papers: List[Dict]) -> List[str]:
        """Generate research questions based on papers"""
        if not papers:
            return []

        papers_info = []
        for paper in papers[:5]:  # Use top 5 papers
            title = paper.get('title', 'Unknown')
            abstract = paper.get('abstract', 'No abstract')[:200]
            papers_info.append(f"- {title}\n  {abstract}")

        papers_text = "\n\n".join(papers_info)

        prompt = f"""Based on these research papers, suggest 5 interesting research questions
or gaps in the literature that could be explored:

{papers_text}

Research Questions:"""

        response = self.llm.generate(prompt)

        questions = [
            line.strip()
            for line in response.split('\n')
            if line.strip() and len(line.strip()) > 10
        ]

        return questions[:5]

    def synthesize_literature(self, papers: List[Dict], focus: str = "main findings") -> str:
        """Synthesize findings across multiple papers"""
        if not papers:
            return "No papers to synthesize"

        papers_info = []
        for paper in papers[:5]:
            title = paper.get('title', 'Unknown')
            abstract = paper.get('abstract', 'No abstract')[:300]
            year = paper.get('year', 'N/A')
            papers_info.append(f"[{year}] {title}\n{abstract}")

        papers_text = "\n\n".join(papers_info)

        prompt = f"""Synthesize the {focus} across these research papers.
Identify common themes, trends, and how the field has evolved.

Papers:
{papers_text}

Synthesis (3-4 paragraphs):"""

        return self.llm.generate(prompt)


# Cached functions for Streamlit
@st.cache_resource
def get_llm_client(model_name: str = "llama3.1:8b") -> OllamaLLMClient:
    """Get cached LLM client"""
    return OllamaLLMClient(model_name)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_summarize_paper(_llm_client: OllamaLLMClient, paper_id: str, paper: Dict) -> str:
    """Cached paper summarization"""
    analyzer = PaperAnalyzer(_llm_client)
    return analyzer.summarize_paper(paper)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_extract_insights(_llm_client: OllamaLLMClient, paper_id: str, paper: Dict) -> Dict:
    """Cached insights extraction"""
    analyzer = PaperAnalyzer(_llm_client)
    return analyzer.extract_key_insights(paper)


@st.cache_data(ttl=1800, show_spinner=False)
def cached_suggest_queries(_llm_client: OllamaLLMClient, query: str, domain: Optional[str] = None) -> List[str]:
    """Cached query suggestions"""
    assistant = QueryAssistant(_llm_client)
    return assistant.suggest_better_queries(query, domain)


@st.cache_data(ttl=1800, show_spinner=False)
def cached_expand_keywords(_llm_client: OllamaLLMClient, query: str) -> List[str]:
    """Cached keyword expansion"""
    assistant = QueryAssistant(_llm_client)
    return assistant.expand_query_with_keywords(query)
