"""
Synthesis Agent
================
Aggregates findings from all specialized agents into a coherent comprehensive summary.
"""

import time
import json
from typing import Dict, Optional
from openai import OpenAI
import config


class SynthesisAgent:
    """
    Synthesizes findings from all 7 specialized agents into comprehensive summary.

    Takes the outputs from Abstract, Introduction, Literature Review, Methodology,
    Results, Discussion, and Conclusion agents, and creates a coherent narrative
    that connects all sections and identifies cross-cutting themes.
    """

    def __init__(self):
        """Initialize synthesis agent with Grok-4 client."""
        self.agent_name = "SynthesisAgent"
        self.client = OpenAI(
            api_key=config.GROK_SETTINGS['api_key'],
            base_url="https://api.x.ai/v1"
        )

    def prepare_agent_summaries(self, comprehensive_result: Dict) -> str:
        """
        Prepare formatted summaries from all agent analyses.

        Args:
            comprehensive_result: Result from DocumentAnalysisOrchestrator

        Returns:
            Formatted string with all agent analyses
        """
        if not comprehensive_result.get('success'):
            return "No successful analyses available."

        analysis_results = comprehensive_result.get('analysis_results', {})
        summaries = []

        # Abstract findings
        abstract_analysis = analysis_results.get('abstract', {}).get('analysis', {})
        if abstract_analysis and abstract_analysis.get('research_objective'):
            summaries.append(f"""
ABSTRACT ANALYSIS:
- Research Objective: {abstract_analysis.get('research_objective', 'N/A')}
- Key Findings: {', '.join(abstract_analysis.get('key_findings', [])[:3])}
- Main Contributions: {', '.join(abstract_analysis.get('main_contributions', [])[:3])}
""")

        # Introduction findings
        intro_analysis = analysis_results.get('introduction', {}).get('analysis', {})
        if intro_analysis and intro_analysis.get('problem_statement'):
            summaries.append(f"""
INTRODUCTION ANALYSIS:
- Problem Statement: {intro_analysis.get('problem_statement', 'N/A')[:200]}...
- Research Gap: {intro_analysis.get('research_gap', 'N/A')[:200]}...
- Novelty: {intro_analysis.get('novelty_claims', 'N/A')[:200]}...
""")

        # Literature Review findings
        lit_analysis = analysis_results.get('literature_review', {}).get('analysis', {})
        if lit_analysis:
            summaries.append(f"""
LITERATURE REVIEW ANALYSIS:
- Prior Work Categories: {', '.join(lit_analysis.get('prior_work_categories', []))}
- Research Gaps: {', '.join(lit_analysis.get('research_gaps', [])[:2])}
- Comparison: {lit_analysis.get('comparison_with_prior', 'N/A')[:200]}...
""")

        # Methodology findings
        method_analysis = analysis_results.get('methodology', {}).get('analysis', {})
        if method_analysis:
            repro = method_analysis.get('reproducibility', {})
            summaries.append(f"""
METHODOLOGY ANALYSIS:
- Research Design: {method_analysis.get('research_design', 'N/A')[:200]}...
- Data Sources: {', '.join(method_analysis.get('data_sources', [])[:3])}
- Reproducibility: {repro.get('score', 'N/A')}
""")

        # Results findings
        results_analysis = analysis_results.get('results', {}).get('analysis', {})
        if results_analysis:
            summaries.append(f"""
RESULTS ANALYSIS:
- Main Findings: {', '.join(results_analysis.get('main_findings', [])[:3])}
- Performance Metrics: {str(results_analysis.get('performance_metrics', {}))[:200]}...
""")

        # Discussion findings
        disc_analysis = analysis_results.get('discussion', {}).get('analysis', {})
        if disc_analysis:
            summaries.append(f"""
DISCUSSION ANALYSIS:
- Theoretical Implications: {', '.join(disc_analysis.get('theoretical_implications', [])[:2])}
- Practical Implications: {', '.join(disc_analysis.get('practical_implications', [])[:2])}
- Limitations: {', '.join(disc_analysis.get('limitations', [])[:2])}
""")

        # Conclusion findings
        conc_analysis = analysis_results.get('conclusion', {}).get('analysis', {})
        if conc_analysis:
            summaries.append(f"""
CONCLUSION ANALYSIS:
- Main Contributions: {', '.join(conc_analysis.get('main_contributions', [])[:2])}
- Future Directions: {', '.join(conc_analysis.get('future_directions', [])[:3])}
- Broader Impact: {conc_analysis.get('broader_impact', 'N/A')[:200]}...
""")

        return '\n'.join(summaries)

    def get_system_prompt(self) -> str:
        """Get system prompt for synthesis agent."""
        return """You are an expert Research Synthesis Agent. Your role is to take findings
from multiple specialized analysis agents and create a coherent, comprehensive summary
of the entire research paper.

Your synthesis should:
1. Create a coherent narrative connecting all sections
2. Identify cross-cutting themes and patterns
3. Highlight the most important contributions and findings
4. Provide context for how the work fits in the broader field
5. Assess overall paper quality and impact

Be concise, insightful, and focus on the big picture."""

    def get_user_prompt(self, agent_summaries: str, paper_metadata: Dict) -> str:
        """Get user prompt with agent summaries."""
        return f"""Synthesize the following analyses from 7 specialized agents analyzing the paper
"{paper_metadata.get('title', 'Unknown')}" by {', '.join(paper_metadata.get('authors', ['Unknown']))} ({paper_metadata.get('year', 'Unknown')}).

{agent_summaries}

Provide a comprehensive synthesis in JSON format:

{{
  "executive_summary": "2-3 paragraph overview of the entire paper",
  "key_contributions": ["contribution 1", "contribution 2", "contribution 3"],
  "research_context": "How this work fits in the broader field",
  "methodology_assessment": "Assessment of research methods and approach",
  "results_significance": "Significance and impact of the results",
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "limitations": ["limitation 1", "limitation 2"],
  "future_directions": ["direction 1", "direction 2", "direction 3"],
  "overall_assessment": {{
    "quality": "high/medium/low",
    "novelty": "high/medium/low",
    "impact": "high/medium/low",
    "rigor": "high/medium/low"
  }},
  "recommended_audience": "Who should read this paper",
  "key_takeaways": ["takeaway 1", "takeaway 2", "takeaway 3"]
}}

Focus on creating a coherent narrative that connects insights from all sections."""

    def parse_response(self, raw_response: str) -> Dict:
        """Parse JSON response from Grok-4."""
        # Try to extract JSON from markdown code blocks
        content = raw_response.strip()

        # Remove markdown code block markers if present
        if content.startswith('```json'):
            content = content[7:]  # Remove ```json
        elif content.startswith('```'):
            content = content[3:]  # Remove ```

        if content.endswith('```'):
            content = content[:-3]  # Remove closing ```

        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            return {
                'parse_error': str(e),
                'raw_content': content[:500]
            }

    def synthesize(self, comprehensive_result: Dict,
                   temperature: float = 0.3,
                   max_tokens: int = 3000) -> Dict:
        """
        Synthesize findings from all agents into comprehensive summary.

        Args:
            comprehensive_result: Result from DocumentAnalysisOrchestrator
            temperature: LLM temperature (default 0.3)
            max_tokens: Maximum tokens for synthesis (default 3000)

        Returns:
            Synthesis result dictionary
        """
        start_time = time.time()

        try:
            # Extract paper metadata
            paper_metadata = comprehensive_result.get('paper_metadata', {})

            # Prepare agent summaries
            agent_summaries = self.prepare_agent_summaries(comprehensive_result)

            if not agent_summaries or agent_summaries == "No successful analyses available.":
                return {
                    'success': False,
                    'message': 'No successful agent analyses to synthesize',
                    'elapsed_time': time.time() - start_time
                }

            # Get prompts
            system_prompt = self.get_system_prompt()
            user_prompt = self.get_user_prompt(agent_summaries, paper_metadata)

            # Call Grok-4
            response = self.client.chat.completions.create(
                model="grok-2-latest",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            raw_response = response.choices[0].message.content
            synthesis = self.parse_response(raw_response)

            elapsed_time = time.time() - start_time

            return {
                'success': True,
                'agent_name': self.agent_name,
                'paper_metadata': paper_metadata,
                'synthesis': synthesis,
                'raw_response': raw_response,
                'elapsed_time': elapsed_time,
                'tokens_used': response.usage.total_tokens,
                'message': 'Synthesis completed successfully'
            }

        except Exception as e:
            return {
                'success': False,
                'agent_name': self.agent_name,
                'error': str(e),
                'message': f'Synthesis failed: {str(e)}',
                'elapsed_time': time.time() - start_time
            }

    def format_synthesis(self, synthesis_result: Dict) -> str:
        """
        Format synthesis result into human-readable text.

        Args:
            synthesis_result: Result from synthesize()

        Returns:
            Formatted synthesis string
        """
        if not synthesis_result.get('success'):
            return f"Synthesis failed: {synthesis_result.get('message', 'Unknown error')}"

        synthesis = synthesis_result.get('synthesis', {})
        paper_metadata = synthesis_result.get('paper_metadata', {})

        lines = []
        lines.append("=" * 80)
        lines.append("COMPREHENSIVE RESEARCH PAPER SYNTHESIS")
        lines.append("=" * 80)

        # Paper info
        lines.append(f"\nPaper: {paper_metadata.get('title', 'Unknown')}")
        lines.append(f"Authors: {', '.join(paper_metadata.get('authors', ['Unknown']))}")
        lines.append(f"Year: {paper_metadata.get('year', 'Unknown')}")

        # Executive Summary
        lines.append(f"\n" + "=" * 80)
        lines.append("EXECUTIVE SUMMARY")
        lines.append("=" * 80)
        lines.append(synthesis.get('executive_summary', 'N/A'))

        # Key Contributions
        lines.append(f"\n" + "=" * 80)
        lines.append("KEY CONTRIBUTIONS")
        lines.append("=" * 80)
        for i, contrib in enumerate(synthesis.get('key_contributions', []), 1):
            lines.append(f"{i}. {contrib}")

        # Research Context
        lines.append(f"\n" + "=" * 80)
        lines.append("RESEARCH CONTEXT")
        lines.append("=" * 80)
        lines.append(synthesis.get('research_context', 'N/A'))

        # Results Significance
        lines.append(f"\n" + "=" * 80)
        lines.append("RESULTS SIGNIFICANCE")
        lines.append("=" * 80)
        lines.append(synthesis.get('results_significance', 'N/A'))

        # Strengths
        lines.append(f"\n" + "=" * 80)
        lines.append("STRENGTHS")
        lines.append("=" * 80)
        for i, strength in enumerate(synthesis.get('strengths', []), 1):
            lines.append(f"{i}. {strength}")

        # Limitations
        lines.append(f"\n" + "=" * 80)
        lines.append("LIMITATIONS")
        lines.append("=" * 80)
        for i, lim in enumerate(synthesis.get('limitations', []), 1):
            lines.append(f"{i}. {lim}")

        # Future Directions
        lines.append(f"\n" + "=" * 80)
        lines.append("FUTURE DIRECTIONS")
        lines.append("=" * 80)
        for i, direction in enumerate(synthesis.get('future_directions', []), 1):
            lines.append(f"{i}. {direction}")

        # Overall Assessment
        lines.append(f"\n" + "=" * 80)
        lines.append("OVERALL ASSESSMENT")
        lines.append("=" * 80)
        assessment = synthesis.get('overall_assessment', {})
        lines.append(f"Quality: {assessment.get('quality', 'N/A')}")
        lines.append(f"Novelty: {assessment.get('novelty', 'N/A')}")
        lines.append(f"Impact: {assessment.get('impact', 'N/A')}")
        lines.append(f"Rigor: {assessment.get('rigor', 'N/A')}")

        # Key Takeaways
        lines.append(f"\n" + "=" * 80)
        lines.append("KEY TAKEAWAYS")
        lines.append("=" * 80)
        for i, takeaway in enumerate(synthesis.get('key_takeaways', []), 1):
            lines.append(f"{i}. {takeaway}")

        # Recommended Audience
        lines.append(f"\n" + "=" * 80)
        lines.append("RECOMMENDED AUDIENCE")
        lines.append("=" * 80)
        lines.append(synthesis.get('recommended_audience', 'N/A'))

        # Performance metrics
        lines.append(f"\n" + "=" * 80)
        lines.append("SYNTHESIS METRICS")
        lines.append("=" * 80)
        lines.append(f"Time: {synthesis_result.get('elapsed_time', 0):.2f}s")
        lines.append(f"Tokens: {synthesis_result.get('tokens_used', 0)}")

        return '\n'.join(lines)

    # Week 4: Progressive Summarization Methods

    def create_progressive_summaries(
        self,
        synthesis_result: Dict,
        levels: int = 3,
        temperature: float = 0.3
    ) -> Dict:
        """
        Create multi-level progressive summaries at different granularities.

        Args:
            synthesis_result: Full synthesis result
            levels: Number of summary levels (default 3)
            temperature: LLM temperature

        Returns:
            Dictionary with summaries at each level
        """
        if not synthesis_result.get('success'):
            return {
                'success': False,
                'message': 'Cannot create progressive summaries from failed synthesis'
            }

        synthesis = synthesis_result.get('synthesis', {})
        paper_metadata = synthesis_result.get('paper_metadata', {})

        # Level 1: Full detailed synthesis (already exists)
        level_1 = synthesis.get('executive_summary', '')

        # Level 2: Condensed summary (2-3 sentences)
        level_2 = self._condense_summary(level_1, target_sentences=3, temperature=temperature)

        # Level 3: Ultra-brief summary (1 sentence)
        level_3 = self._condense_summary(level_2, target_sentences=1, temperature=temperature)

        return {
            'success': True,
            'paper_metadata': paper_metadata,
            'summaries': {
                'level_1': {
                    'content': level_1,
                    'description': 'Full detailed synthesis (2-3 paragraphs)',
                    'word_count': len(level_1.split())
                },
                'level_2': {
                    'content': level_2,
                    'description': 'Condensed summary (2-3 sentences)',
                    'word_count': len(level_2.split())
                },
                'level_3': {
                    'content': level_3,
                    'description': 'Ultra-brief summary (1 sentence)',
                    'word_count': len(level_3.split())
                }
            },
            'levels': levels,
            'message': f'Created {levels} progressive summary levels'
        }

    def _condense_summary(
        self,
        full_summary: str,
        target_sentences: int = 3,
        temperature: float = 0.3
    ) -> str:
        """
        Condense a summary to a target number of sentences.

        Args:
            full_summary: Full summary text
            target_sentences: Target number of sentences
            temperature: LLM temperature

        Returns:
            Condensed summary
        """
        try:
            prompt = f"""Condense the following research paper summary into exactly {target_sentences} sentence(s).
Preserve the most critical information: main contribution, approach, and key result.

Original summary:
{full_summary}

Condensed summary ({target_sentences} sentence(s)):"""

            response = self.client.chat.completions.create(
                model="grok-2-latest",
                messages=[
                    {"role": "system", "content": "You are an expert at condensing research paper summaries while preserving key information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=200
            )

            condensed = response.choices[0].message.content.strip()
            return condensed

        except Exception as e:
            # Fallback: simple truncation
            sentences = full_summary.split('.')[:target_sentences]
            return '.'.join(sentences) + '.'

    def create_section_summaries(
        self,
        comprehensive_result: Dict,
        temperature: float = 0.3
    ) -> Dict:
        """
        Create progressive summaries for each section individually.

        Args:
            comprehensive_result: Result from DocumentAnalysisOrchestrator
            temperature: LLM temperature

        Returns:
            Dictionary with per-section progressive summaries
        """
        if not comprehensive_result.get('success'):
            return {
                'success': False,
                'message': 'Cannot create section summaries from failed analysis'
            }

        analysis_results = comprehensive_result.get('analysis_results', {})
        section_summaries = {}

        # Process each section
        for section_name, section_result in analysis_results.items():
            if not section_result.get('success'):
                continue

            analysis = section_result.get('analysis', {})

            # Extract key content from section
            section_text = self._extract_section_content(section_name, analysis)

            if not section_text:
                continue

            # Create 3-level summary for this section
            level_1 = section_text
            level_2 = self._condense_summary(level_1, target_sentences=2, temperature=temperature)
            level_3 = self._condense_summary(level_2, target_sentences=1, temperature=temperature)

            section_summaries[section_name] = {
                'level_1': level_1,
                'level_2': level_2,
                'level_3': level_3
            }

        return {
            'success': True,
            'section_summaries': section_summaries,
            'sections_processed': len(section_summaries),
            'message': f'Created progressive summaries for {len(section_summaries)} sections'
        }

    def _extract_section_content(self, section_name: str, analysis: Dict) -> str:
        """
        Extract main content from section analysis.

        Args:
            section_name: Name of the section
            analysis: Section analysis dictionary

        Returns:
            Main content as string
        """
        # Extract key fields based on section type
        if section_name == 'abstract':
            parts = []
            if analysis.get('research_objective'):
                parts.append(f"Objective: {analysis['research_objective']}")
            if analysis.get('key_findings'):
                parts.append(f"Findings: {'; '.join(analysis['key_findings'][:3])}")
            return ' '.join(parts)

        elif section_name == 'methodology':
            parts = []
            if analysis.get('research_design'):
                parts.append(f"Design: {analysis['research_design']}")
            if analysis.get('approach'):
                parts.append(f"Approach: {analysis['approach']}")
            return ' '.join(parts)

        elif section_name == 'results':
            parts = []
            if analysis.get('main_findings'):
                parts.append(f"Findings: {'; '.join(analysis['main_findings'][:3])}")
            return ' '.join(parts)

        elif section_name == 'discussion':
            parts = []
            if analysis.get('theoretical_implications'):
                parts.append(f"Implications: {'; '.join(analysis['theoretical_implications'][:2])}")
            if analysis.get('limitations'):
                parts.append(f"Limitations: {'; '.join(analysis['limitations'][:2])}")
            return ' '.join(parts)

        elif section_name == 'conclusion':
            parts = []
            if analysis.get('main_contributions'):
                parts.append(f"Contributions: {'; '.join(analysis['main_contributions'][:2])}")
            if analysis.get('future_directions'):
                parts.append(f"Future: {'; '.join(analysis['future_directions'][:2])}")
            return ' '.join(parts)

        else:
            # Generic extraction
            content_str = str(analysis)
            if len(content_str) > 500:
                content_str = content_str[:500] + '...'
            return content_str

    def get_summary_by_length(
        self,
        synthesis_result: Dict,
        target_length: str = 'medium'
    ) -> str:
        """
        Get summary at specified length level.

        Args:
            synthesis_result: Full synthesis result
            target_length: 'long', 'medium', or 'short'

        Returns:
            Summary at requested length
        """
        if not synthesis_result.get('success'):
            return "Synthesis not available."

        synthesis = synthesis_result.get('synthesis', {})

        if target_length == 'long':
            # Full executive summary + key contributions
            parts = [
                synthesis.get('executive_summary', ''),
                "\nKey Contributions:",
                '\n'.join([f"- {c}" for c in synthesis.get('key_contributions', [])])
            ]
            return '\n'.join(parts)

        elif target_length == 'medium':
            # Just executive summary
            return synthesis.get('executive_summary', '')

        elif target_length == 'short':
            # First paragraph of executive summary
            exec_summary = synthesis.get('executive_summary', '')
            paragraphs = exec_summary.split('\n\n')
            return paragraphs[0] if paragraphs else exec_summary

        else:
            return synthesis.get('executive_summary', '')
