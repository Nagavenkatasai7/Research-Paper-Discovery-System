"""
Figures Analysis Agent
=======================

Specialized agent for analyzing figures, plots, diagrams, and visualizations in research papers.
Extracts insights from visual content, architectural diagrams, and graphical representations.
"""

from typing import Dict
from .base_agent import BaseAnalysisAgent


class FiguresAgent(BaseAnalysisAgent):
    """Agent specialized in analyzing Figures and visual content"""

    def __init__(self):
        super().__init__(
            agent_name="FiguresAgent",
            section_name="Figures"
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for Figures analysis"""
        return """You are a specialized Figures Analysis Agent with expertise in interpreting visual content from research papers.

Your role is to provide DEEP, COMPREHENSIVE analysis of all figures in the paper, extracting and analyzing:
- Figure types and purposes (plots, diagrams, architectures, examples, screenshots)
- Key insights from plots and visualizations
- Architecture diagrams and system designs
- Trends, patterns, and relationships shown visually
- Quality and effectiveness of visualizations
- Supporting visual evidence for claims

You must:
- Catalog all figures and their purposes
- Extract insights from plot data (trends, comparisons, distributions)
- Interpret architecture diagrams and system designs
- Analyze example visualizations and their implications
- Identify key takeaways from each figure
- Assess visualization quality and clarity
- Note how figures support the paper's arguments
- Identify missing visualizations that would be helpful
- Evaluate the effectiveness of visual communication

Output your analysis as a JSON object with this structure:
{
  "total_figures": "Number of figures in the paper",
  "figures_summary": [
    {
      "figure_number": "Figure number or identifier",
      "caption": "Figure caption",
      "type": "plot/diagram/architecture/screenshot/example/schematic/other",
      "purpose": "What this figure shows or demonstrates",
      "key_insights": ["Insight 1 from this figure", "Insight 2", ...]
    }
  ],
  "architecture_diagrams": [
    {
      "figure_id": "Which figure",
      "architecture_type": "e.g., 'neural network', 'system pipeline', 'data flow'",
      "components": ["Component 1", "Component 2", ...],
      "connections": "How components interact",
      "novel_aspects": "What's novel or unique about this architecture",
      "description": "Detailed description of the architecture"
    }
  ],
  "plots_and_graphs": [
    {
      "figure_id": "Which figure",
      "plot_type": "line/bar/scatter/heatmap/box/other",
      "x_axis": "What's on x-axis",
      "y_axis": "What's on y-axis",
      "trends_observed": ["Trend 1", "Trend 2", ...],
      "comparisons": "What is being compared",
      "key_findings": "Main takeaways from this plot"
    }
  ],
  "examples_and_demonstrations": [
    {
      "figure_id": "Which figure",
      "what_is_shown": "Description of example",
      "purpose": "Why this example is included",
      "insights": "What this example demonstrates about the method"
    }
  ],
  "visualization_insights": [
    "Key insights that can ONLY be understood through the visual representations"
  ],
  "visual_evidence": {
    "claims_supported": [
      {
        "claim": "Claim from the paper",
        "figure": "Which figure provides evidence",
        "how": "How the figure supports this claim"
      }
    ],
    "qualitative_results": "Description of qualitative results shown visually",
    "visual_comparisons": "What visual comparisons are made with other methods"
  },
  "trends_and_patterns": [
    {
      "pattern": "Description of observed pattern or trend",
      "figures": "Which figures show this",
      "significance": "Why this pattern matters"
    }
  ],
  "visualization_quality": {
    "clarity": "high/medium/low - Are figures clear and readable?",
    "completeness": "high/medium/low - Are all necessary visualizations present?",
    "effectiveness": "high/medium/low - Do figures effectively communicate insights?",
    "missing_visualizations": ["What visualizations would be helpful but are missing"],
    "improvement_suggestions": ["How figures could be improved"]
  },
  "cross_figure_insights": "Insights that emerge when considering multiple figures together",
  "critical_analysis": "Your detailed critical analysis of the figures - Are they informative? Clear? Well-designed? Do they effectively support the paper's claims? Are important visualizations missing? Be thorough and specific."
}

Be critical and thorough. Assess both what figures show and what they DON'T show."""

    def get_user_prompt(self, section_text: str, paper_metadata: Dict) -> str:
        """Get user prompt with figures content and metadata"""
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

        return f"""Analyze all figures from the following research paper in depth.

Paper Information:
- Title: {title}
- Authors: {authors_str}
- Year: {year}

Figures Content (captions and descriptions):
{section_text}

NOTE: You are analyzing figure CAPTIONS and DESCRIPTIONS extracted from the paper. Use these to infer what the figures show and their purpose.

Provide a comprehensive analysis covering all the points specified in your role. For each figure, analyze:
1. What type of visualization it is and why it's used
2. What insights or information it conveys
3. How it supports the paper's arguments
4. Architecture details (if it's an architecture diagram)
5. Trends and patterns (if it's a plot)
6. Examples and demonstrations (if showing qualitative results)
7. Quality and effectiveness of the visualization

Pay special attention to:
- Architecture diagrams (extract component details and connections)
- Performance plots (identify trends and comparisons)
- Ablation study visualizations
- Qualitative examples (what they demonstrate)
- How figures complement the textual content

Remember to output your response as a JSON object following the specified structure."""


if __name__ == "__main__":
    # Test the FiguresAgent
    print("Testing FiguresAgent...")

    # Sample figures content
    sample_figures = """
    Figure 1: The Transformer model architecture. The encoder is on the left and decoder is on the right.
    Components include multi-head attention layers, feed-forward networks, and residual connections with layer normalization.

    Figure 2: Multi-head attention mechanism. Shows how queries, keys, and values are linearly projected h times
    with different learned projections, then concatenated and projected again.

    Figure 3: Training loss curves. Comparison of training loss over time for Transformer (base), Transformer (big),
    and baseline models (LSTM, ConvS2S). Transformer models converge faster and achieve lower final loss.

    Figure 4: Attention visualization. Example of attention weights learned by different heads in the model.
    Different heads appear to learn different linguistic phenomena (e.g., syntactic dependencies, anaphora resolution).

    Figure 5: BLEU scores vs. model size. Shows that BLEU score increases logarithmically with model size
    (number of parameters), with diminishing returns after 100M parameters.
    """

    metadata = {
        'title': 'Attention Is All You Need',
        'authors': ['Vaswani', 'Shazeer', 'Parmar'],
        'year': 2017
    }

    agent = FiguresAgent()
    print(f"Agent initialized: {agent.agent_name}")
    print(f"Section: {agent.section_name}")
    print("\nSystem prompt preview:")
    print(agent.get_system_prompt()[:200] + "...")
    print("\nUser prompt preview:")
    print(agent.get_user_prompt(sample_figures, metadata)[:300] + "...")
