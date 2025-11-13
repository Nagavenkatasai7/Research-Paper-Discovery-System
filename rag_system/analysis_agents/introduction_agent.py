"""
Introduction Analysis Agent
============================

Specialized agent for analyzing the Introduction/Background section of research papers.
Extracts problem statement, motivation, research questions, and novelty claims.
"""

from typing import Dict
from .base_agent import BaseAnalysisAgent


class IntroductionAgent(BaseAnalysisAgent):
    """Agent specialized in analyzing Introduction sections"""

    def __init__(self):
        super().__init__(
            agent_name="IntroductionAgent",
            section_name="Introduction"
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for Introduction analysis"""
        return """You are a specialized Introduction Analysis Agent with expertise in critically evaluating research paper introductions.

Your role is to provide DEEP, COMPREHENSIVE analysis of the Introduction section, extracting and analyzing:
- Problem statement and its significance
- Research motivation and context
- Research questions and hypotheses
- Background and related work overview
- Novelty and contribution claims
- Paper organization/structure

You must:
- Extract ALL important information from the introduction
- Identify the core problem being addressed
- Assess how well the introduction motivates the research
- Note the research gap being filled
- Evaluate the clarity of research questions
- Assess how well the introduction positions the work
- Be thorough and detailed in your analysis

Output your analysis as a JSON object with this structure:
{
  "problem_statement": "Clear statement of the problem being addressed",
  "problem_significance": "Why this problem matters",
  "research_motivation": "What motivates this research",
  "research_context": "Background context and domain",
  "research_questions": ["Question 1", "Question 2", ...],
  "hypotheses": ["Hypothesis 1", ...] or [],
  "research_gap": "What gap in knowledge this fills",
  "novelty_claims": ["Novel aspect 1", "Novel aspect 2", ...],
  "background_summary": "Brief summary of background information provided",
  "paper_structure": "How the paper is organized (if mentioned)",
  "introduction_quality": {
    "clarity": "high/medium/low",
    "motivation_strength": "high/medium/low",
    "problem_definition": "high/medium/low"
  },
  "critical_analysis": "Your detailed critical analysis of the introduction - how well it sets up the paper, strengths, weaknesses, clarity of problem/motivation, etc."
}

Be critical and thorough. Assess whether the introduction effectively motivates the research and clearly defines the problem."""

    def get_user_prompt(self, section_text: str, paper_metadata: Dict) -> str:
        """Get user prompt with introduction text and metadata"""
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

        return f"""Analyze the following research paper introduction in depth.

Paper Information:
- Title: {title}
- Authors: {authors_str}
- Year: {year}

Introduction Section:
{section_text}

Provide a comprehensive analysis covering all the points specified in your role. Extract every important piece of information and provide critical analysis of how well the introduction sets up the research.

Remember to output your response as a JSON object following the specified structure."""
