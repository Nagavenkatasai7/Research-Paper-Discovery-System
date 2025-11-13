"""
Results Analysis Agent
=======================

Specialized agent for analyzing the Results/Findings section.
Extracts main findings, metrics, and statistical significance.
"""

from typing import Dict
from .base_agent import BaseAnalysisAgent


class ResultsAgent(BaseAnalysisAgent):
    """Agent specialized in analyzing Results sections"""

    def __init__(self):
        super().__init__(
            agent_name="ResultsAgent",
            section_name="Results"
        )

    def get_system_prompt(self) -> str:
        return """You are a specialized Results Analysis Agent.

Analyze the Results section comprehensively, extracting:
- Main findings and outcomes
- Performance metrics and scores
- Statistical significance
- Comparisons with baselines
- Visualizations and tables summary
- Unexpected or surprising results

Output as JSON:
{
  "main_findings": ["Finding 1", "Finding 2", ...],
  "performance_metrics": {"metric1": "value1", "metric2": "value2", ...},
  "statistical_tests": ["Test 1 results", "Test 2 results", ...],
  "comparisons": {
    "baseline_models": ["Model 1", "Model 2", ...],
    "performance_comparison": "Summary of how this work compares"
  },
  "visualizations_summary": "Summary of key figures/tables",
  "unexpected_results": ["Unexpected 1", ...] or [],
  "results_quality": {
    "statistical_rigor": "high/medium/low",
    "completeness": "high/medium/low"
  },
  "critical_analysis": "Detailed analysis of results - significance, robustness, interpretation, limitations in presentation"
}"""

    def get_user_prompt(self, section_text: str, paper_metadata: Dict) -> str:
        return f"""Analyze this Results section:

Paper: {paper_metadata.get('title', 'Unknown')}

Results Section:
{section_text}

Provide comprehensive analysis as JSON following the specified structure."""
