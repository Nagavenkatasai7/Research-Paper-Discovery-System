"""
Mathematical Formulations Analysis Agent
==========================================

Specialized agent for analyzing mathematical equations, formulas, proofs, and theoretical contributions.
Extracts key equations, theoretical insights, and mathematical rigor.
"""

from typing import Dict
from .base_agent import BaseAnalysisAgent


class MathAgent(BaseAnalysisAgent):
    """Agent specialized in analyzing mathematical formulations and equations"""

    def __init__(self):
        super().__init__(
            agent_name="MathAgent",
            section_name="Mathematics"
        )

    def get_system_prompt(self) -> str:
        """Get system prompt for Mathematics analysis"""
        return """You are a specialized Mathematical Analysis Agent with expertise in analyzing mathematical formulations, equations, and theoretical contributions in research papers.

Your role is to provide DEEP, COMPREHENSIVE analysis of all mathematical content, extracting and analyzing:
- Key equations and their meanings
- Mathematical notation and conventions
- Theoretical contributions and novelty
- Proofs and derivations
- Complexity analysis (time/space)
- Mathematical rigor and soundness

You must:
- Identify and catalog all important equations
- Explain what each key equation represents
- Distinguish between novel equations and established formulas
- Analyze theoretical contributions
- Extract complexity analysis (Big-O notation, bounds, etc.)
- Assess mathematical rigor and proof quality
- Identify key mathematical insights or breakthroughs
- Note mathematical assumptions and constraints
- Evaluate clarity of mathematical presentation

Output your analysis as a JSON object with this structure:
{
  "total_equations": "Approximate number of equations/formulas in the paper",
  "key_equations": [
    {
      "equation_reference": "Equation number or description",
      "equation": "The equation itself (in LaTeX or text form)",
      "meaning": "What this equation represents or computes",
      "purpose": "Why this equation is important in the paper",
      "novelty": "novel/modified/standard - is this a new formulation?",
      "variables": ["Variable 1: meaning", "Variable 2: meaning", ...]
    }
  ],
  "mathematical_notation": {
    "notation_used": ["Notation 1", "Notation 2", ...],
    "conventions": "Any special notation conventions used",
    "clarity": "high/medium/low - is notation clear and consistent?"
  },
  "theoretical_contributions": {
    "main_theorems": [
      {
        "theorem": "Statement of theorem",
        "significance": "Why this theorem matters",
        "proof_provided": "yes/sketch/no"
      }
    ],
    "mathematical_novelty": "What is mathematically novel in this work",
    "theoretical_foundations": "What mathematical foundations does this build on",
    "assumptions": ["Mathematical assumption 1", "Assumption 2", ...]
  },
  "core_formulations": {
    "objective_function": "If applicable, the main objective being optimized",
    "loss_function": "If ML paper, the loss function used",
    "update_rules": "If applicable, parameter update or learning rules",
    "key_algorithms": "Mathematical description of key algorithms"
  },
  "complexity_analysis": {
    "time_complexity": "Big-O time complexity if provided",
    "space_complexity": "Big-O space complexity if provided",
    "computational_cost": "Analysis of computational requirements",
    "scalability": "How method scales mathematically",
    "bounds": "Upper/lower bounds provided"
  },
  "proofs_and_derivations": {
    "proofs_provided": "yes/partial/no - are mathematical proofs given?",
    "derivation_steps": "Are equation derivations shown step-by-step?",
    "rigor": "high/medium/low - mathematical rigor level",
    "proof_techniques": ["Technique 1", "Technique 2", ...],
    "gaps_or_issues": ["Any gaps or issues in proofs/derivations"]
  },
  "mathematical_relationships": [
    {
      "relationship": "Description of mathematical relationship",
      "equations_involved": "Which equations show this relationship",
      "insight": "What insight this relationship provides"
    }
  ],
  "novel_formulations": [
    {
      "formulation": "Description of novel mathematical formulation",
      "innovation": "What makes this formulation innovative",
      "benefits": "Mathematical or practical benefits of this formulation"
    }
  ],
  "mathematical_rigor": {
    "rigor_level": "high/medium/low",
    "formal_proofs": "Are formal mathematical proofs provided?",
    "assumptions_stated": "Are all assumptions clearly stated?",
    "edge_cases": "Are edge cases and boundary conditions addressed?",
    "mathematical_soundness": "Assessment of mathematical correctness"
  },
  "practical_implications": [
    "How mathematical formulations translate to practical algorithms or implementations"
  ],
  "mathematical_clarity": {
    "presentation_quality": "high/medium/low - how clearly is math presented?",
    "notation_consistency": "Is notation used consistently?",
    "explanation_completeness": "Are equations well-explained?",
    "accessibility": "Is math accessible to non-specialists?"
  },
  "critical_analysis": "Your detailed critical analysis of the mathematical content - Is it rigorous? Clear? Novel? Well-founded? Are proofs complete? Is complexity analysis thorough? Be thorough and specific."
}

Be critical and thorough. Assess mathematical correctness, novelty, rigor, and clarity."""

    def get_user_prompt(self, section_text: str, paper_metadata: Dict) -> str:
        """Get user prompt with mathematical content and metadata"""
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

        return f"""Analyze all mathematical content (equations, formulas, proofs, complexity analysis) from the following research paper in depth.

Paper Information:
- Title: {title}
- Authors: {authors_str}
- Year: {year}

Mathematical Content:
{section_text}

Provide a comprehensive analysis covering all the points specified in your role. For mathematical content, analyze:
1. What are the key equations and what do they represent?
2. Which formulations are novel vs. standard/established?
3. Theoretical contributions and mathematical insights
4. Complexity analysis (time, space, computational cost)
5. Mathematical rigor (proofs, derivations, assumptions)
6. Clarity and accessibility of mathematical presentation
7. How math translates to practical algorithms

Pay special attention to:
- Novel mathematical formulations and their benefits
- Theoretical soundness and rigor
- Complexity bounds and scalability
- Assumptions and constraints
- Proof completeness and correctness
- Practical implications of mathematical results

If the paper has limited mathematical content, note that and analyze what IS present. If it's heavily mathematical, extract and explain all key formulations.

Remember to output your response as a JSON object following the specified structure."""


if __name__ == "__main__":
    # Test the MathAgent
    print("Testing MathAgent...")

    # Sample mathematical content
    sample_math = """
    The core of our model is the scaled dot-product attention:

    Attention(Q, K, V) = softmax(QK^T / sqrt(d_k))V

    where Q, K, V are queries, keys, and values respectively, and d_k is the dimension of the keys.
    The scaling factor 1/sqrt(d_k) prevents the dot products from growing too large.

    Multi-head attention allows the model to attend to information from different representation subspaces:

    MultiHead(Q, K, V) = Concat(head_1, ..., head_h)W^O
    where head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)

    The position-wise feed-forward network is defined as:

    FFN(x) = max(0, xW_1 + b_1)W_2 + b_2

    Time complexity: The self-attention layer has O(n^2 · d) complexity where n is the sequence length
    and d is the model dimension. This is compared to O(n · d^2) for recurrent layers.

    Space complexity: O(n^2) for storing attention weights.
    """

    metadata = {
        'title': 'Attention Is All You Need',
        'authors': ['Vaswani', 'Shazeer', 'Parmar'],
        'year': 2017
    }

    agent = MathAgent()
    print(f"Agent initialized: {agent.agent_name}")
    print(f"Section: {agent.section_name}")
    print("\nSystem prompt preview:")
    print(agent.get_system_prompt()[:200] + "...")
    print("\nUser prompt preview:")
    print(agent.get_user_prompt(sample_math, metadata)[:300] + "...")
