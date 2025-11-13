"""
Literature Review Analysis Agent
==================================

Specialized agent for analyzing the Related Work/Literature Review section.
Extracts prior work, gaps, and theoretical frameworks.
"""

from typing import Dict
from .base_agent import BaseAnalysisAgent


class LiteratureReviewAgent(BaseAnalysisAgent):
    """Agent specialized in analyzing Literature Review sections"""

    def __init__(self):
        super().__init__(
            agent_name="LiteratureReviewAgent",
            section_name="Literature Review"
        )

    def get_system_prompt(self) -> str:
        return """You are a specialized Literature Review Analysis Agent.

Analyze the Related Work/Literature Review section comprehensively, extracting:
- Categories of prior work
- Key papers and contributions cited
- Theoretical frameworks mentioned
- Research gaps identified
- How this work compares to prior work

Output as JSON:
{
  "prior_work_categories": ["Category 1", "Category 2", ...],
  "key_papers_cited": [{"title": "Paper 1", "contribution": "What it did"}, ...],
  "theoretical_frameworks": ["Framework 1", "Framework 2", ...],
  "research_gaps": ["Gap 1", "Gap 2", ...],
  "comparison_with_prior": "How this work differs from/improves upon prior work",
  "evolution_of_field": "Brief history or evolution of the field (if mentioned)",
  "literature_quality": {
    "comprehensiveness": "high/medium/low",
    "critical_analysis": "yes/no",
    "clear_gap_identification": "yes/no"
  },
  "critical_analysis": "Detailed analysis of literature review quality - comprehensiveness, critical engagement, gap identification"
}"""

    def get_user_prompt(self, section_text: str, paper_metadata: Dict) -> str:
        return f"""Analyze this Literature Review/Related Work section:

Paper: {paper_metadata.get('title', 'Unknown')}

Literature Review Section:
{section_text}

Provide comprehensive analysis as JSON following the specified structure."""
