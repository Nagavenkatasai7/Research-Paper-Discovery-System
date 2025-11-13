"""
Methodology Analysis Agent
===========================

Specialized agent for analyzing the Methods/Methodology section.
Extracts research design, data collection, techniques, and reproducibility.
"""

from typing import Dict
from .base_agent import BaseAnalysisAgent


class MethodologyAgent(BaseAnalysisAgent):
    """Agent specialized in analyzing Methodology sections"""

    def __init__(self):
        super().__init__(
            agent_name="MethodologyAgent",
            section_name="Methodology"
        )

    def get_system_prompt(self) -> str:
        return """You are a specialized Methodology Analysis Agent.

Analyze the Methods/Methodology section comprehensively, extracting:
- Research design and approach
- Data collection methods
- Analysis techniques
- Tools, frameworks, and materials used
- Experimental setup and procedures
- Parameters and configurations
- Reproducibility assessment

Output as JSON:
{
  "research_design": "Overall research design/approach",
  "data_sources": ["Source 1", "Source 2", ...],
  "data_collection": "How data was collected",
  "sample_size": "Sample size if mentioned",
  "analysis_techniques": ["Technique 1", "Technique 2", ...],
  "tools_and_frameworks": ["Tool 1", "Tool 2", ...],
  "experimental_setup": "Description of experimental setup",
  "parameters": {"param1": "value1", ...},
  "evaluation_metrics": ["Metric 1", "Metric 2", ...],
  "reproducibility": {
    "score": "high/medium/low",
    "details_provided": ["Detail 1", ...],
    "missing_details": ["Missing 1", ...]
  },
  "critical_analysis": "Detailed analysis of methodology quality, rigor, appropriateness, and reproducibility"
}"""

    def get_user_prompt(self, section_text: str, paper_metadata: Dict) -> str:
        return f"""Analyze this Methodology section:

Paper: {paper_metadata.get('title', 'Unknown')}

Methodology Section:
{section_text}

Provide comprehensive analysis as JSON following the specified structure."""
