"""
Tables Analysis Agent
======================

Specialized agent for analyzing tables in research papers.
Extracts performance metrics, experimental results, comparisons, and statistical data.
"""

from typing import Dict
from .base_agent import BaseAnalysisAgent


class TablesAgent(BaseAnalysisAgent):
    """Agent specialized in analyzing Tables and quantitative results"""

    def __init__(self):
        super().__init__(
            agent_name="TablesAgent",
            section_name="Tables"
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for Tables analysis"""
        return """You are a specialized Tables Analysis Agent with expertise in extracting and interpreting quantitative data from research paper tables.

Your role is to provide DEEP, COMPREHENSIVE analysis of all tables in the paper, extracting and analyzing:
- Performance metrics and numerical results
- Comparisons with baselines and state-of-the-art
- Statistical significance indicators
- Ablation study results
- Dataset characteristics and experimental setups
- Trends and patterns in the data

You must:
- Extract ALL numerical results from tables
- Identify the main performance metrics being measured
- Analyze comparisons with baselines (what are they comparing against?)
- Note statistical significance indicators (p-values, confidence intervals, error bars)
- Extract ablation study insights (what components were tested?)
- Identify best-performing methods and configurations
- Note dataset information (size, splits, characteristics)
- Analyze trends across different experimental conditions
- Assess the quality and completeness of experimental evaluation

Output your analysis as a JSON object with this structure:
{
  "total_tables": "Number of tables in the paper",
  "tables_summary": [
    {
      "table_number": "Table number or identifier",
      "caption": "Table caption/title",
      "purpose": "What this table shows (e.g., 'main results', 'ablation study', 'dataset statistics')",
      "key_findings": ["Finding 1 from this table", "Finding 2", ...]
    }
  ],
  "key_metrics": [
    {
      "metric_name": "e.g., 'Accuracy', 'BLEU score', 'F1 score'",
      "best_value": "Best value achieved",
      "method": "Method that achieved this value",
      "context": "On which dataset/task"
    }
  ],
  "performance_summary": {
    "main_results": "Summary of primary performance results",
    "best_performing_method": "Which method/model performed best overall",
    "performance_gains": "Improvements over baselines (e.g., '+5.2% accuracy')",
    "consistency": "Are results consistent across different settings?"
  },
  "comparisons": [
    {
      "compared_methods": ["Method 1", "Method 2", ...],
      "comparison_type": "baseline/sota/ablation/cross-dataset",
      "outcome": "What the comparison shows",
      "statistical_significance": "Yes/No/Unknown - are differences significant?"
    }
  ],
  "ablation_studies": {
    "components_tested": ["Component 1", "Component 2", ...],
    "key_insights": ["What was learned from removing/adding each component"],
    "critical_components": ["Which components are most important"]
  },
  "statistical_tests": {
    "tests_reported": "What statistical tests were used (t-test, ANOVA, etc.)",
    "significance_levels": "Reported p-values or significance thresholds",
    "error_bars": "Are error bars/standard deviations reported?"
  },
  "datasets_used": [
    {
      "dataset_name": "Name of dataset",
      "size": "Number of samples",
      "splits": "train/val/test split info",
      "characteristics": "Key characteristics"
    }
  ],
  "experimental_setup": {
    "evaluation_metrics": ["Metric 1", "Metric 2", ...],
    "cross_validation": "Yes/No - was cross-validation used?",
    "num_runs": "Number of experimental runs (for averaging)",
    "hardware_info": "If reported in tables"
  },
  "trends_and_patterns": [
    "Observable trends in the data (e.g., 'performance increases with model size', 'diminishing returns after X')"
  ],
  "data_quality_assessment": {
    "completeness": "Are all necessary comparisons present?",
    "clarity": "Are tables clear and well-organized?",
    "statistical_rigor": "Are results statistically sound?",
    "missing_comparisons": ["Important baselines or comparisons that are missing"]
  },
  "critical_analysis": "Your detailed critical analysis of the tables and results - Are the experiments comprehensive? Are comparisons fair? Are results convincing? Statistical rigor? Be thorough and specific."
}

Be critical and thorough. Look for statistical rigor, fair comparisons, and completeness of evaluation."""

    def get_user_prompt(self, section_text: str, paper_metadata: Dict) -> str:
        """Get user prompt with tables content and metadata"""
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

        return f"""Analyze all tables from the following research paper in depth.

Paper Information:
- Title: {title}
- Authors: {authors_str}
- Year: {year}

Tables Content:
{section_text}

Provide a comprehensive analysis covering all the points specified in your role. Extract every numerical result and provide critical analysis of:
1. What metrics are being measured and why
2. How the proposed method compares to baselines and state-of-the-art
3. Statistical significance of results
4. Completeness and fairness of experimental evaluation
5. Ablation study insights (if present)
6. Dataset characteristics and experimental setup
7. Trends and patterns in the performance data
8. Quality and rigor of the experimental methodology

Pay special attention to:
- Best-performing configurations
- Statistically significant improvements
- Ablation study insights
- Consistency of results across datasets/tasks
- Fair comparisons with strong baselines

Remember to output your response as a JSON object following the specified structure."""


if __name__ == "__main__":
    # Test the TablesAgent
    print("Testing TablesAgent...")

    # Sample table content
    sample_tables = """
    Table 1: Main Results on WMT 2014 English-to-German Translation

    Model                    | BLEU  | Training Cost
    -------------------------|-------|---------------
    ByteNet                  | 23.75 | -
    Deep-Att + PosUnk       | 24.60 | -
    GNMT + RL               | 26.30 | -
    ConvS2S                 | 25.16 | -
    MoE                     | 26.03 | -
    Transformer (base)      | 27.3  | 12 hours (8 P100)
    Transformer (big)       | 28.4  | 3.5 days (8 P100)

    Table 2: Ablation Study - Attention Heads

    Heads | Accuracy | Training Time
    ------|----------|---------------
    1     | 85.2%    | 4.5 hours
    4     | 88.1%    | 5.2 hours
    8     | 89.7%    | 6.1 hours
    16    | 89.3%    | 7.8 hours
    """

    metadata = {
        'title': 'Attention Is All You Need',
        'authors': ['Vaswani', 'Shazeer', 'Parmar'],
        'year': 2017
    }

    agent = TablesAgent()
    print(f"Agent initialized: {agent.agent_name}")
    print(f"Section: {agent.section_name}")
    print("\nSystem prompt preview:")
    print(agent.get_system_prompt()[:200] + "...")
    print("\nUser prompt preview:")
    print(agent.get_user_prompt(sample_tables, metadata)[:300] + "...")
