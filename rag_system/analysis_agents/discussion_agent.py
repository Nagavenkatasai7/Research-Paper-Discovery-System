"""
Discussion Analysis Agent
==========================

Specialized agent for analyzing the Discussion section.
Extracts interpretations, implications, and limitations.
"""

from typing import Dict
from .base_agent import BaseAnalysisAgent


class DiscussionAgent(BaseAnalysisAgent):
    """Agent specialized in analyzing Discussion sections"""

    def __init__(self):
        super().__init__(
            agent_name="DiscussionAgent",
            section_name="Discussion"
        )

    def get_system_prompt(self) -> str:
        return """You are a specialized Discussion Analysis Agent.

Analyze the Discussion section comprehensively, extracting:
- Interpretation of results
- Theoretical implications
- Practical implications
- Comparison with prior work
- Limitations
- Threats to validity

Output as JSON:
{
  "results_interpretation": "How authors interpret their results",
  "theoretical_implications": ["Implication 1", "Implication 2", ...],
  "practical_implications": ["Practical use 1", "Practical use 2", ...],
  "comparison_with_literature": "How results compare to prior work",
  "limitations": ["Limitation 1", "Limitation 2", ...],
  "threats_to_validity": ["Threat 1", ...] or [],
  "generalizability": "Assessment of how generalizable the findings are",
  "discussion_quality": {
    "depth": "high/medium/low",
    "balanced": "yes/no",
    "limitations_honest": "yes/no"
  },
  "critical_analysis": "Detailed analysis of discussion quality - depth of interpretation, honesty about limitations, balance"
}"""

    def get_user_prompt(self, section_text: str, paper_metadata: Dict) -> str:
        return f"""Analyze this Discussion section:

Paper: {paper_metadata.get('title', 'Unknown')}

Discussion Section:
{section_text}

Provide comprehensive analysis as JSON following the specified structure."""
