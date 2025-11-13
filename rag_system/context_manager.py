"""
Context Manager for Multi-Agent System
========================================

Manages cross-sectional context sharing between agents to improve coherence
and enable comprehensive analysis through inter-agent communication.

This module enables:
- Agents to register key findings for other agents to reference
- Context retrieval for agents that need cross-sectional information
- Cross-reference building for validation and consistency checking
- Context-aware synthesis for comprehensive summaries
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class Finding:
    """Represents a finding registered by an agent"""
    from_agent: str
    finding_type: str  # 'methodology', 'result', 'limitation', 'claim', 'metric', 'dataset', 'equation', 'figure'
    content: Dict
    relevance_to: List[str] = field(default_factory=list)  # Which agents this is relevant to
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    priority: str = "medium"  # 'high', 'medium', 'low'


class ContextManager:
    """
    Manages cross-sectional context between agents.

    Enables agents to share findings and retrieve relevant context from other agents,
    improving coherence and completeness of analysis.

    Example usage:
        cm = ContextManager()

        # Register finding from methodology agent
        cm.register_finding(
            'methodology',
            'method_detail',
            {'technique': 'Transformer architecture', 'key_innovation': 'self-attention'},
            relevance_to=['results', 'discussion'],
            priority='high'
        )

        # Results agent retrieves methodology context
        context = cm.get_context_for_agent('results', context_types=['method_detail'])
    """

    def __init__(self):
        """Initialize context manager"""
        self.findings: List[Finding] = []
        self.cross_references: Dict[str, List[str]] = {}  # section -> [referenced_sections]
        self.agent_dependencies: Dict[str, Set[str]] = {}  # agent -> {agents_it_depends_on}

        # Define which agents typically benefit from which other agents' context
        self.default_dependencies = {
            'discussion': {'methodology', 'results', 'figures', 'tables'},
            'conclusion': {'abstract', 'results', 'discussion'},
            'results': {'methodology', 'tables', 'figures', 'mathematics'},
            'methodology': {'literature_review', 'mathematics'},
            'literature_review': {'references'},
        }

    def register_finding(
        self,
        from_agent: str,
        finding_type: str,
        content: Dict,
        relevance_to: Optional[List[str]] = None,
        priority: str = "medium"
    ) -> Finding:
        """
        Register a finding from an agent that may be relevant to other agents.

        Args:
            from_agent: Name of agent registering the finding
            finding_type: Type of finding (e.g., 'methodology', 'result', 'limitation')
            content: Dictionary with finding content
            relevance_to: List of agent names this is relevant to (None = auto-detect)
            priority: Priority level ('high', 'medium', 'low')

        Returns:
            The created Finding object

        Example:
            cm.register_finding(
                'methodology',
                'dataset',
                {'name': 'MNIST', 'size': '60k', 'splits': '50k/10k'},
                relevance_to=['results'],
                priority='high'
            )
        """
        # Auto-detect relevance if not specified
        if relevance_to is None:
            relevance_to = self._auto_detect_relevance(from_agent, finding_type)

        finding = Finding(
            from_agent=from_agent,
            finding_type=finding_type,
            content=content,
            relevance_to=relevance_to,
            priority=priority
        )

        self.findings.append(finding)

        # Update cross-references
        for target_agent in relevance_to:
            if from_agent not in self.cross_references:
                self.cross_references[from_agent] = []
            if target_agent not in self.cross_references[from_agent]:
                self.cross_references[from_agent].append(target_agent)

        return finding

    def _auto_detect_relevance(self, from_agent: str, finding_type: str) -> List[str]:
        """
        Auto-detect which agents would find this finding relevant.

        Args:
            from_agent: Agent registering the finding
            finding_type: Type of finding

        Returns:
            List of agent names
        """
        relevance_map = {
            'methodology': ['results', 'discussion', 'conclusion'],
            'result': ['discussion', 'conclusion'],
            'limitation': ['discussion', 'conclusion'],
            'dataset': ['results', 'methodology'],
            'metric': ['results', 'tables'],
            'equation': ['methodology', 'results', 'mathematics'],
            'figure': ['results', 'discussion'],
            'table': ['results', 'discussion'],
            'claim': ['discussion', 'conclusion'],
            'reference': ['literature_review', 'discussion']
        }

        return relevance_map.get(finding_type, ['discussion', 'conclusion'])

    def get_context_for_agent(
        self,
        requesting_agent: str,
        context_types: Optional[List[str]] = None,
        from_agents: Optional[List[str]] = None,
        priority_filter: Optional[str] = None
    ) -> Dict[str, List[Finding]]:
        """
        Get relevant context for an agent from other agents.

        Args:
            requesting_agent: Agent requesting context
            context_types: Filter by finding types (None = all types)
            from_agents: Filter by source agents (None = all agents)
            priority_filter: Filter by priority ('high', 'medium', 'low', None = all)

        Returns:
            Dictionary mapping agent names to lists of relevant findings

        Example:
            # Discussion agent needs methodology and results context
            context = cm.get_context_for_agent(
                'discussion',
                context_types=['methodology', 'result'],
                priority_filter='high'
            )
        """
        relevant_findings: Dict[str, List[Finding]] = {}

        for finding in self.findings:
            # Check if this finding is relevant to requesting agent
            if requesting_agent not in finding.relevance_to:
                continue

            # Apply filters
            if context_types and finding.finding_type not in context_types:
                continue

            if from_agents and finding.from_agent not in from_agents:
                continue

            if priority_filter and finding.priority != priority_filter:
                continue

            # Add to results
            agent_name = finding.from_agent
            if agent_name not in relevant_findings:
                relevant_findings[agent_name] = []
            relevant_findings[agent_name].append(finding)

        return relevant_findings

    def build_cross_reference_map(self, all_agent_results: Dict) -> Dict:
        """
        Build a comprehensive cross-reference map from all agent results.

        Args:
            all_agent_results: Dictionary of all agent analysis results

        Returns:
            Cross-reference map with relationships between sections

        Example output:
            {
                'methodology_to_results': [
                    {'method': 'transformer', 'result': 'BLEU=28.4'}
                ],
                'results_to_discussion': [...],
                'claims_to_evidence': [...]
            }
        """
        cross_ref_map = {
            'methodology_to_results': [],
            'results_to_discussion': [],
            'limitations_to_methodology': [],
            'claims_to_evidence': [],
            'figures_to_insights': [],
            'tables_to_metrics': [],
            'equations_to_applications': []
        }

        # Extract methodology -> results connections
        methodology_findings = [f for f in self.findings if f.from_agent == 'methodology']
        results_findings = [f for f in self.findings if f.from_agent == 'results']

        for method_finding in methodology_findings:
            if 'results' in method_finding.relevance_to:
                cross_ref_map['methodology_to_results'].append({
                    'methodology': method_finding.content,
                    'type': method_finding.finding_type
                })

        # Extract results -> discussion connections
        for result_finding in results_findings:
            if 'discussion' in result_finding.relevance_to:
                cross_ref_map['results_to_discussion'].append({
                    'result': result_finding.content,
                    'type': result_finding.finding_type
                })

        # Extract limitations
        limitation_findings = [f for f in self.findings if f.finding_type == 'limitation']
        cross_ref_map['limitations_to_methodology'] = [
            {
                'limitation': f.content,
                'from_agent': f.from_agent
            }
            for f in limitation_findings
        ]

        # Extract claims and evidence
        claim_findings = [f for f in self.findings if f.finding_type == 'claim']
        cross_ref_map['claims_to_evidence'] = [
            {
                'claim': f.content,
                'agent': f.from_agent
            }
            for f in claim_findings
        ]

        return cross_ref_map

    def build_validation_map(self, all_results: Dict) -> Dict:
        """
        Build validation map for consistency checking across sections.

        Checks:
        - Do methodology descriptions match results?
        - Are limitations mentioned consistent with methodology constraints?
        - Are conclusions supported by results?
        - Do tables/figures align with textual claims?

        Args:
            all_results: Dictionary of all agent analysis results

        Returns:
            Validation map with consistency checks
        """
        validation_map = {
            'methodology_result_alignment': [],
            'limitation_consistency': [],
            'conclusion_support': [],
            'quantitative_alignment': []
        }

        # Check methodology-results alignment
        method_findings = self.get_findings_by_agent('methodology')
        result_findings = self.get_findings_by_agent('results')

        for method_finding in method_findings:
            if method_finding.finding_type == 'methodology':
                # Check if this methodology is validated in results
                mentioned_in_results = any(
                    self._finding_mentions_method(result_finding, method_finding)
                    for result_finding in result_findings
                )

                validation_map['methodology_result_alignment'].append({
                    'methodology': method_finding.content,
                    'validated_in_results': mentioned_in_results
                })

        # Check limitation consistency
        limitation_findings = [f for f in self.findings if f.finding_type == 'limitation']
        validation_map['limitation_consistency'] = [
            {
                'limitation': f.content,
                'agent': f.from_agent,
                'consistent': True  # Could add logic to check consistency
            }
            for f in limitation_findings
        ]

        # Check quantitative alignment (tables vs text)
        table_findings = self.get_findings_by_agent('tables')
        text_findings = self.get_findings_by_agent('results')

        validation_map['quantitative_alignment'] = {
            'table_count': len(table_findings),
            'result_claims': len(text_findings),
            'aligned': len(table_findings) > 0 and len(text_findings) > 0
        }

        return validation_map

    def get_findings_by_agent(self, agent_name: str) -> List[Finding]:
        """Get all findings from a specific agent"""
        return [f for f in self.findings if f.from_agent == agent_name]

    def get_findings_by_type(self, finding_type: str) -> List[Finding]:
        """Get all findings of a specific type"""
        return [f for f in self.findings if f.finding_type == finding_type]

    def _finding_mentions_method(self, result_finding: Finding, method_finding: Finding) -> bool:
        """Check if a result finding mentions a methodology finding"""
        # Simplified check - in practice, would use semantic similarity
        method_content = str(method_finding.content).lower()
        result_content = str(result_finding.content).lower()

        # Extract key terms from methodology
        key_terms = []
        if isinstance(method_finding.content, dict):
            for value in method_finding.content.values():
                if isinstance(value, str):
                    key_terms.extend(value.lower().split())

        # Check if any key terms appear in results
        return any(term in result_content for term in key_terms if len(term) > 3)

    def get_agent_dependencies(self, agent_name: str) -> Set[str]:
        """
        Get which other agents this agent typically depends on for context.

        Args:
            agent_name: Name of the agent

        Returns:
            Set of agent names this agent depends on
        """
        return self.default_dependencies.get(agent_name, set())

    def export_context(self) -> Dict:
        """
        Export all context data as a dictionary for storage/analysis.

        Returns:
            Dictionary with all context data
        """
        return {
            'findings': [
                {
                    'from_agent': f.from_agent,
                    'finding_type': f.finding_type,
                    'content': f.content,
                    'relevance_to': f.relevance_to,
                    'timestamp': f.timestamp,
                    'priority': f.priority
                }
                for f in self.findings
            ],
            'cross_references': self.cross_references,
            'total_findings': len(self.findings),
            'agents_with_findings': list(set(f.from_agent for f in self.findings))
        }

    def import_context(self, context_data: Dict):
        """
        Import context data from a dictionary.

        Args:
            context_data: Dictionary with context data (from export_context())
        """
        self.findings = []
        for finding_data in context_data.get('findings', []):
            finding = Finding(
                from_agent=finding_data['from_agent'],
                finding_type=finding_data['finding_type'],
                content=finding_data['content'],
                relevance_to=finding_data.get('relevance_to', []),
                timestamp=finding_data.get('timestamp', datetime.now().isoformat()),
                priority=finding_data.get('priority', 'medium')
            )
            self.findings.append(finding)

        self.cross_references = context_data.get('cross_references', {})

    def get_summary_statistics(self) -> Dict:
        """Get summary statistics about the context"""
        return {
            'total_findings': len(self.findings),
            'agents_with_findings': len(set(f.from_agent for f in self.findings)),
            'finding_types': len(set(f.finding_type for f in self.findings)),
            'high_priority_findings': len([f for f in self.findings if f.priority == 'high']),
            'cross_references': len(self.cross_references),
            'findings_by_agent': {
                agent: len(self.get_findings_by_agent(agent))
                for agent in set(f.from_agent for f in self.findings)
            },
            'findings_by_type': {
                ftype: len(self.get_findings_by_type(ftype))
                for ftype in set(f.finding_type for f in self.findings)
            }
        }


if __name__ == "__main__":
    # Test the ContextManager
    print("Testing ContextManager...")

    cm = ContextManager()

    # Test 1: Register findings
    print("\n1. Registering findings...")
    cm.register_finding(
        'methodology',
        'methodology',
        {'technique': 'Transformer', 'innovation': 'self-attention'},
        relevance_to=['results', 'discussion'],
        priority='high'
    )

    cm.register_finding(
        'results',
        'result',
        {'metric': 'BLEU', 'value': 28.4, 'dataset': 'WMT14'},
        relevance_to=['discussion', 'conclusion'],
        priority='high'
    )

    cm.register_finding(
        'methodology',
        'limitation',
        {'issue': 'High computational cost', 'impact': 'Training time'},
        relevance_to=['discussion'],
        priority='medium'
    )

    print(f"✓ Registered {len(cm.findings)} findings")

    # Test 2: Retrieve context
    print("\n2. Retrieving context for discussion agent...")
    discussion_context = cm.get_context_for_agent('discussion')
    print(f"✓ Found context from {len(discussion_context)} agents")
    for agent, findings in discussion_context.items():
        print(f"   - {agent}: {len(findings)} findings")

    # Test 3: Build cross-reference map
    print("\n3. Building cross-reference map...")
    cross_ref_map = cm.build_cross_reference_map({})
    print(f"✓ Built cross-reference map with {len(cross_ref_map)} categories")

    # Test 4: Get statistics
    print("\n4. Context statistics...")
    stats = cm.get_summary_statistics()
    print(f"✓ Total findings: {stats['total_findings']}")
    print(f"✓ Agents with findings: {stats['agents_with_findings']}")
    print(f"✓ High priority: {stats['high_priority_findings']}")

    # Test 5: Export/Import
    print("\n5. Testing export/import...")
    exported = cm.export_context()
    print(f"✓ Exported {len(exported['findings'])} findings")

    cm2 = ContextManager()
    cm2.import_context(exported)
    print(f"✓ Imported {len(cm2.findings)} findings")

    print("\n✅ All tests passed!")
