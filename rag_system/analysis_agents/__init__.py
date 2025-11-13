"""
Analysis Agents Module
======================

Multi-agent system for comprehensive research paper analysis.
Each agent specializes in analyzing a specific section of the paper.

Enhanced 11-agent system includes:
- 7 section-based agents (Abstract, Introduction, Literature Review, Methodology, Results, Discussion, Conclusion)
- 4 specialized content agents (References, Tables, Figures, Mathematics)
"""

from .base_agent import BaseAnalysisAgent
from .abstract_agent import AbstractAgent
from .introduction_agent import IntroductionAgent
from .literature_review_agent import LiteratureReviewAgent
from .methodology_agent import MethodologyAgent
from .results_agent import ResultsAgent
from .discussion_agent import DiscussionAgent
from .conclusion_agent import ConclusionAgent
from .references_agent import ReferencesAgent
from .tables_agent import TablesAgent
from .figures_agent import FiguresAgent
from .math_agent import MathAgent
from .orchestrator import DocumentAnalysisOrchestrator
from .synthesis_agent import SynthesisAgent

__all__ = [
    'BaseAnalysisAgent',
    'AbstractAgent',
    'IntroductionAgent',
    'LiteratureReviewAgent',
    'MethodologyAgent',
    'ResultsAgent',
    'DiscussionAgent',
    'ConclusionAgent',
    'ReferencesAgent',
    'TablesAgent',
    'FiguresAgent',
    'MathAgent',
    'DocumentAnalysisOrchestrator',
    'SynthesisAgent',
]
