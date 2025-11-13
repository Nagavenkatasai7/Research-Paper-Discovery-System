"""
References Analysis Agent
===========================

Specialized agent for analyzing the References/Bibliography section of research papers.
Extracts citation patterns, key references, influential works, and citation diversity.
"""

from typing import Dict
from .base_agent import BaseAnalysisAgent


class ReferencesAgent(BaseAnalysisAgent):
    """Agent specialized in analyzing References/Bibliography sections"""

    def __init__(self):
        super().__init__(
            agent_name="ReferencesAgent",
            section_name="References"
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for References analysis"""
        return """You are a specialized References Analysis Agent with expertise in analyzing research paper citations and bibliographies.

Your role is to provide DEEP, COMPREHENSIVE analysis of the References section, extracting and analyzing:
- Key foundational papers cited
- Citation patterns and distribution
- Influential and landmark works
- Citation recency and temporal distribution
- Research area diversity
- Citation quality and relevance

You must:
- Identify the most frequently cited papers (top 10-15)
- Distinguish between foundational works vs recent references
- Analyze citation diversity (journals, conferences, preprints, books)
- Identify potential citation gaps or biases
- Assess the quality and relevance of references
- Note the presence of seminal/landmark papers in the field
- Analyze self-citations vs external citations (if author info available)
- Evaluate temporal distribution (old vs recent citations)

Output your analysis as a JSON object with this structure:
{
  "total_references": "Number of references cited",
  "key_references": [
    {
      "reference": "Author(s), Title, Venue, Year",
      "importance": "Why this reference is important",
      "category": "foundational/methodological/comparative/related_work"
    }
  ],
  "citation_patterns": {
    "temporal_distribution": {
      "very_old": "Number/percentage of citations >10 years old",
      "old": "5-10 years old",
      "recent": "2-5 years old",
      "very_recent": "<2 years old"
    },
    "venue_diversity": {
      "journals": "Count",
      "conferences": "Count",
      "preprints": "Count",
      "books": "Count",
      "other": "Count"
    },
    "self_citations": "Number or 'unknown' if cannot determine"
  },
  "influential_works": [
    {
      "work": "Citation details",
      "influence": "How this work influenced the field or this paper"
    }
  ],
  "foundational_papers": [
    "List of seminal/landmark papers that establish the foundation"
  ],
  "recent_advances": [
    "List of recent papers showing state-of-the-art or latest developments"
  ],
  "citation_diversity": {
    "research_areas": ["Area 1", "Area 2", ...],
    "geographical_diversity": "Assessment of author/institution diversity",
    "quality_assessment": "high/medium/low - based on venue quality and relevance"
  },
  "potential_gaps": [
    "Important works or areas that seem to be missing"
  ],
  "citation_network_insights": "Analysis of how citations relate to each other, citation clusters, etc.",
  "critical_analysis": "Your detailed critical analysis of the references - Are they comprehensive? Current? Relevant? Any biases? Quality of sources? Be thorough and specific."
}

Be critical and thorough. Look for patterns, gaps, biases, and quality indicators."""

    def get_user_prompt(self, section_text: str, paper_metadata: Dict) -> str:
        """Get user prompt with references text and metadata"""
        title = paper_metadata.get('title', 'Unknown')
        authors = paper_metadata.get('authors', ['Unknown'])
        year = paper_metadata.get('year', 'Unknown')

        # Format authors
        if isinstance(authors, list):
            authors_str = ', '.join(authors[:3])
            if len(authors) > 3:
                authors_str += ' et al.'
        else:
            authors_str = str(authors)

        return f"""Analyze the following research paper's references/bibliography section in depth.

Paper Information:
- Title: {title}
- Authors: {authors_str}
- Year: {year}

References/Bibliography Section:
{section_text}

Provide a comprehensive analysis covering all the points specified in your role. Extract every important reference and provide critical analysis of:
1. The quality and comprehensiveness of the bibliography
2. Citation patterns and temporal distribution
3. Key influential works and foundational papers
4. Citation diversity across venues and research areas
5. Potential gaps or biases in citations
6. How well the references support the paper's claims

Remember to output your response as a JSON object following the specified structure."""


if __name__ == "__main__":
    # Test the ReferencesAgent
    print("Testing ReferencesAgent...")

    # Sample references section (abbreviated)
    sample_references = """
    [1] Vaswani, A., et al. (2017). Attention is all you need. NIPS.
    [2] Devlin, J., et al. (2018). BERT: Pre-training of deep bidirectional transformers. NAACL.
    [3] Sutskever, I., Vinyals, O., & Le, Q. V. (2014). Sequence to sequence learning. NIPS.
    [4] Bahdanau, D., Cho, K., & Bengio, Y. (2014). Neural machine translation by jointly learning to align. ICLR.
    [5] Hochreiter, S., & Schmidhuber, J. (1997). Long short-term memory. Neural computation.
    [6] Bengio, Y., et al. (2003). A neural probabilistic language model. JMLR.
    [7] Brown, T., et al. (2020). Language models are few-shot learners. NeurIPS.
    [8] Radford, A., et al. (2019). Language models are unsupervised multitask learners. OpenAI Blog.
    [9] Liu, Y., et al. (2019). RoBERTa: A robustly optimized BERT approach. arXiv preprint.
    [10] Lewis, M., et al. (2020). BART: Denoising sequence-to-sequence pre-training. ACL.
    """

    metadata = {
        'title': 'Example Paper on Transformers',
        'authors': ['Smith', 'Johnson', 'Williams'],
        'year': 2023
    }

    agent = ReferencesAgent()
    print(f"Agent initialized: {agent.agent_name}")
    print(f"Section: {agent.section_name}")
    print("\nSystem prompt preview:")
    print(agent.get_system_prompt()[:200] + "...")
    print("\nUser prompt preview:")
    print(agent.get_user_prompt(sample_references, metadata)[:300] + "...")
