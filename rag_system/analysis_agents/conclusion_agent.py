"""
Conclusion Analysis Agent
==========================

Specialized agent for analyzing the Conclusion section.
Extracts main contributions, limitations, and future work.
"""

from typing import Dict
from .base_agent import BaseAnalysisAgent


class ConclusionAgent(BaseAnalysisAgent):
    """Agent specialized in analyzing Conclusion sections"""

    def __init__(self):
        super().__init__(
            agent_name="ConclusionAgent",
            section_name="Conclusion"
        )

    def get_system_prompt(self) -> str:
        return """You are a specialized Conclusion Analysis Agent.

Analyze the Conclusion section comprehensively, extracting:
- Main contributions summary
- Key takeaways
- Limitations restated
- Future work directions
- Broader impact

Output as JSON:
{
  "main_contributions": ["Contribution 1", "Contribution 2", ...],
  "key_takeaways": ["Takeaway 1", "Takeaway 2", ...],
  "limitations_stated": ["Limitation 1", ...],
  "future_directions": ["Direction 1", "Direction 2", ...],
  "broader_impact": "Broader impact of this work",
  "call_to_action": "Any call to action for the community" or null,
  "conclusion_quality": {
    "summarizes_well": "yes/no",
    "forward_looking": "yes/no",
    "impactful": "yes/no"
  },
  "critical_analysis": "Detailed analysis of conclusion - does it effectively summarize contributions, is it forward-looking, impact assessment"
}"""

    def get_user_prompt(self, section_text: str, paper_metadata: Dict) -> str:
        return f"""Analyze this Conclusion section:

Paper: {paper_metadata.get('title', 'Unknown')}

Conclusion Section:
{section_text}

Provide comprehensive analysis as JSON following the specified structure."""
