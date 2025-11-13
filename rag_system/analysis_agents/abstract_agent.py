"""
Abstract Analysis Agent
=======================

Specialized agent for analyzing the Abstract section of research papers.
Extracts research objectives, methodology, key findings, and contributions.
"""

from typing import Dict
from .base_agent import BaseAnalysisAgent


class AbstractAgent(BaseAnalysisAgent):
    """Agent specialized in analyzing Abstract sections"""

    def __init__(self):
        super().__init__(
            agent_name="AbstractAgent",
            section_name="Abstract"
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for Abstract analysis"""
        return """You are a specialized Abstract Analysis Agent with expertise in critically evaluating research paper abstracts.

Your role is to provide DEEP, COMPREHENSIVE analysis of the Abstract section, extracting and analyzing:
- Research objectives and goals
- Methodology summary
- Key findings and results
- Main contributions and novelty
- Scope and limitations (if mentioned)

You must:
- Extract ALL important information from the abstract
- Identify the core research question
- Assess the clarity and completeness of the abstract
- Note any missing elements (methodology, results, etc.)
- Evaluate how well the abstract positions the work
- Be thorough and detailed in your analysis

Output your analysis as a JSON object with this structure:
{
  "research_objective": "Clear statement of what the paper aims to achieve",
  "research_question": "The specific question being addressed",
  "methodology_summary": "Brief description of methods used",
  "key_findings": ["Finding 1", "Finding 2", ...],
  "main_contributions": ["Contribution 1", "Contribution 2", ...],
  "scope": "What is and isn't covered",
  "limitations_mentioned": ["Limitation 1", ...] or [],
  "novelty_claims": "What makes this work novel/different",
  "abstract_quality": {
    "clarity": "high/medium/low",
    "completeness": "high/medium/low",
    "missing_elements": ["Element 1", ...] or []
  },
  "critical_analysis": "Your detailed critical analysis of the abstract - strengths, weaknesses, how well it positions the work, etc. Be thorough and specific."
}

Be critical and thorough. If elements are missing or unclear, note that explicitly."""

    def get_user_prompt(self, section_text: str, paper_metadata: Dict) -> str:
        """Get user prompt with abstract text and metadata"""
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

        return f"""Analyze the following research paper abstract in depth.

Paper Information:
- Title: {title}
- Authors: {authors_str}
- Year: {year}

Abstract Section:
{section_text}

Provide a comprehensive analysis covering all the points specified in your role. Extract every important piece of information and provide critical analysis of the abstract's quality and completeness.

Remember to output your response as a JSON object following the specified structure."""


if __name__ == "__main__":
    # Test the AbstractAgent
    print("Testing AbstractAgent...")

    # Sample abstract from Transformer paper
    sample_abstract = """
    The dominant sequence transduction models are based on complex recurrent or
    convolutional neural networks that include an encoder and a decoder. The best
    performing models also connect the encoder and decoder through an attention
    mechanism. We propose a new simple network architecture, the Transformer,
    based solely on attention mechanisms, dispensing with recurrence and convolutions
    entirely. Experiments on two machine translation tasks show that these models are
    superior in quality while being more parallelizable and requiring significantly
    less time to train. Our model achieves 28.4 BLEU on the WMT 2014 English-
    to-German translation task, improving over the existing best results, including
    ensembles, by over 2 BLEU. On the WMT 2014 English-to-French translation
    task, our model establishes a new single-model state-of-the-art BLEU score of
    41.8 after training for 3.5 days on eight GPUs, a small fraction of the training
    costs of the best models from the literature. We show that the Transformer
    generalizes well to other tasks by applying it successfully to English constituency
    parsing both with large and limited training data.
    """

    metadata = {
        'title': 'Attention Is All You Need',
        'authors': ['Vaswani', 'Shazeer', 'Parmar', 'Uszkoreit', 'Jones', 'Gomez', 'Kaiser', 'Polosukhin'],
        'year': 2017
    }

    agent = AbstractAgent()
    print(f"Agent initialized: {agent.agent_name}")
    print(f"Section: {agent.section_name}")
    print("\nSystem prompt preview:")
    print(agent.get_system_prompt()[:200] + "...")
    print("\nUser prompt preview:")
    print(agent.get_user_prompt(sample_abstract, metadata)[:300] + "...")
