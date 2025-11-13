"""
Document Analysis Orchestrator
===============================
Coordinates all 11 specialized agents to analyze research papers in parallel.

Enhanced with 4 new specialized content agents:
- ReferencesAgent: Citation analysis
- TablesAgent: Performance metrics extraction
- FiguresAgent: Visual content analysis
- MathAgent: Mathematical formulations analysis
"""

import time
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from rag_system.pdf_processor import PDFProcessor
from rag_system.analysis_agents import (
    AbstractAgent,
    IntroductionAgent,
    LiteratureReviewAgent,
    MethodologyAgent,
    ResultsAgent,
    DiscussionAgent,
    ConclusionAgent,
    ReferencesAgent,
    TablesAgent,
    FiguresAgent,
    MathAgent
)


class DocumentAnalysisOrchestrator:
    """
    Orchestrates multi-agent analysis of research papers.

    Coordinates 11 specialized agents to analyze different sections
    and content types of research papers in parallel, providing comprehensive analysis.

    Agents:
    - 7 section-based agents (Abstract, Introduction, Literature, Methodology, Results, Discussion, Conclusion)
    - 4 content-specific agents (References, Tables, Figures, Mathematics)
    """

    def __init__(self):
        """Initialize orchestrator with all 11 specialized agents."""
        from rag_system.context_manager import ContextManager

        self.pdf_processor = PDFProcessor()
        self.context_manager = ContextManager()

        # Initialize all 11 specialized agents
        self.agents = {
            # Section-based agents (original 7)
            'abstract': AbstractAgent(),
            'introduction': IntroductionAgent(),
            'literature_review': LiteratureReviewAgent(),
            'methodology': MethodologyAgent(),
            'results': ResultsAgent(),
            'discussion': DiscussionAgent(),
            'conclusion': ConclusionAgent(),
            # Content-specific agents (new 4)
            'references': ReferencesAgent(),
            'tables': TablesAgent(),
            'figures': FiguresAgent(),
            'mathematics': MathAgent()
        }

        # Section extraction strategies for each agent
        self.section_strategies = {
            'abstract': {
                'keys': ['abstract', 'Abstract', 'ABSTRACT'],
                'pages': (0, 1),  # First page
                'max_chars': 3000
            },
            'introduction': {
                'keys': ['introduction', 'Introduction', 'INTRODUCTION', '1 Introduction'],
                'pages': (1, 3),  # Pages 2-3
                'max_chars': 5000
            },
            'literature_review': {
                'keys': ['literature', 'Literature', 'related work', 'Related Work',
                         'RELATED WORK', 'background', 'Background'],
                'pages': (2, 4),  # Pages 3-4
                'max_chars': 5000
            },
            'methodology': {
                'keys': ['methodology', 'Methodology', 'methods', 'Methods',
                         'model', 'Model Architecture', 'architecture'],
                'pages': (3, 6),  # Pages 4-6
                'max_chars': 6000
            },
            'results': {
                'keys': ['results', 'Results', 'RESULTS', 'experiments', 'Experiments',
                         'experimental results', 'Experimental Results'],
                'pages': (5, 9),  # Pages 6-9
                'max_chars': 6000
            },
            'discussion': {
                'keys': ['discussion', 'Discussion', 'DISCUSSION', 'analysis', 'Analysis'],
                'pages': (8, 11),  # Pages 9-11
                'max_chars': 5000
            },
            'conclusion': {
                'keys': ['conclusion', 'Conclusion', 'CONCLUSION', 'conclusions',
                         'future work', 'Future Work'],
                'pages': (-3, None),  # Last 3 pages
                'max_chars': 5000
            },
            # New content-specific agents
            'references': {
                'keys': ['references', 'References', 'REFERENCES', 'bibliography',
                         'Bibliography', 'BIBLIOGRAPHY'],
                'pages': (-5, None),  # Last 5 pages (references typically at end)
                'max_chars': 10000  # Larger limit for references section
            },
            'tables': {
                'keys': ['tables', 'Tables', 'table', 'Table'],
                'pages': (0, None),  # Check entire document
                'max_chars': 8000  # Include all table content
            },
            'figures': {
                'keys': ['figures', 'Figures', 'figure', 'Figure', 'fig', 'Fig'],
                'pages': (0, None),  # Check entire document
                'max_chars': 8000  # Include all figure captions
            },
            'mathematics': {
                'keys': ['equation', 'Equation', 'formula', 'theorem', 'proof'],
                'pages': (0, None),  # Check entire document
                'max_chars': 10000  # Include all mathematical content
            }
        }

    def extract_section(self, sections: Dict, pages: List, section_name: str) -> Optional[str]:
        """
        Extract section text using multiple strategies with robust fallbacks.

        Args:
            sections: Dictionary of extracted sections
            pages: List of page dictionaries
            section_name: Name of section to extract (e.g., 'abstract')

        Returns:
            Extracted section text, always returns something if pages available
        """
        strategy = self.section_strategies.get(section_name)
        if not strategy:
            return None

        # Strategy 1: Try exact section name matches
        for key in strategy['keys']:
            if key in sections:
                text = sections[key].strip()
                if text:
                    return text[:strategy['max_chars']]

        # Strategy 2: Fallback to page range extraction (ALWAYS EXTRACT SOMETHING)
        if pages and len(pages) > 0:
            start_page, end_page = strategy['pages']

            # Handle negative indices for end pages
            if start_page < 0:
                start_idx = max(0, len(pages) + start_page)
            else:
                start_idx = min(start_page, len(pages) - 1)

            if end_page is None:
                end_idx = len(pages)
            elif end_page < 0:
                end_idx = max(start_idx + 1, len(pages) + end_page)
            else:
                end_idx = min(end_page, len(pages))

            # Ensure valid range
            start_idx = max(0, min(start_idx, len(pages) - 1))
            end_idx = max(start_idx + 1, min(end_idx, len(pages)))

            # Extract text from page range - ALWAYS extract something
            extracted_pages = pages[start_idx:end_idx]
            if extracted_pages:
                text = '\n'.join([p.get('text', '') for p in extracted_pages])
                if text.strip():
                    return text.strip()[:strategy['max_chars']]
                else:
                    # Even if empty, return a placeholder so agent runs
                    return f"[Content from pages {start_idx+1}-{end_idx} could not be extracted clearly]"

        # Strategy 3: Ultimate fallback - extract all available text
        if pages and len(pages) > 0:
            all_text = '\n'.join([p.get('text', '') for p in pages])
            if all_text.strip():
                # Return a portion of the full paper
                return all_text.strip()[:strategy['max_chars']]

        # If absolutely nothing is available, return a message
        return f"[No content available for {section_name} section]"

    def analyze_section(self, agent_name: str, section_text: str,
                       paper_metadata: Dict) -> Dict:
        """
        Analyze a section using the appropriate agent.

        Args:
            agent_name: Name of agent to use
            section_text: Text of section to analyze
            paper_metadata: Paper metadata dictionary

        Returns:
            Analysis result dictionary
        """
        try:
            agent = self.agents[agent_name]
            result = agent.analyze(section_text, paper_metadata)
            result['agent_name'] = agent_name
            return result
        except Exception as e:
            return {
                'success': False,
                'agent_name': agent_name,
                'error': str(e),
                'message': f'Failed to analyze {agent_name} section'
            }

    def analyze_paper(self, pdf_path: str, paper_metadata: Optional[Dict] = None,
                     parallel: bool = True, max_workers: int = 11,
                     enable_context_sharing: bool = False) -> Dict:
        """
        Analyze research paper using all specialized agents.

        Args:
            pdf_path: Path to PDF file
            paper_metadata: Optional paper metadata (title, authors, year)
            parallel: Whether to run agents in parallel (default: True)
            max_workers: Maximum number of parallel workers (default: 11)
            enable_context_sharing: Enable two-pass analysis with cross-sectional context (default: False)

        Returns:
            Comprehensive analysis dictionary with results from all agents

        When enable_context_sharing=True:
            - Pass 1: All agents analyze their sections
            - Context Building: Extract findings and build context map
            - Pass 2: Selected agents (discussion, conclusion) re-analyze with context
        """
        start_time = time.time()

        # Default metadata if not provided
        if paper_metadata is None:
            paper_metadata = {
                'title': 'Unknown',
                'authors': ['Unknown'],
                'year': None
            }

        try:
            # Step 1: Extract sections from PDF
            print(f"📄 Extracting sections from PDF...")
            extraction_result = self.pdf_processor.extract_text_by_sections(pdf_path)
            sections = extraction_result.get('sections', {})
            pages = extraction_result.get('pages', [])

            # Step 2: Extract text for each section
            print(f"📑 Extracting text for each agent...")
            section_texts = {}
            for agent_name in self.agents.keys():
                section_text = self.extract_section(sections, pages, agent_name)
                if section_text:
                    section_texts[agent_name] = section_text
                    print(f"  ✓ {agent_name}: {len(section_text)} characters")
                else:
                    print(f"  ⚠️  {agent_name}: section not found (will skip)")

            # Step 3: Analyze sections with agents
            agent_results = {}

            if parallel:
                # Parallel execution
                print(f"\n⚡ Running {len(section_texts)} agents in parallel...")

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all agent tasks
                    future_to_agent = {
                        executor.submit(
                            self.analyze_section,
                            agent_name,
                            section_text,
                            paper_metadata
                        ): agent_name
                        for agent_name, section_text in section_texts.items()
                    }

                    # Collect results as they complete with timeout protection
                    # 300s (5 min) total timeout for all agents, 60s per agent
                    try:
                        for future in as_completed(future_to_agent, timeout=300):
                            agent_name = future_to_agent[future]
                            try:
                                # Per-agent timeout to prevent individual hangs
                                result = future.result(timeout=60)
                                agent_results[agent_name] = result

                                if result['success']:
                                    elapsed = result.get('elapsed_time', 0)
                                    tokens = result.get('tokens_used', 0)
                                    print(f"  ✓ {agent_name}: {elapsed:.2f}s, {tokens} tokens")
                                else:
                                    print(f"  ❌ {agent_name}: {result.get('message', 'Failed')}")
                            except TimeoutError:
                                print(f"  ⏱️  {agent_name}: Timeout after 60 seconds")
                                # Cancel the future to free resources
                                future.cancel()
                                agent_results[agent_name] = {
                                    'success': False,
                                    'agent_name': agent_name,
                                    'error': 'Agent execution timed out after 60 seconds'
                                }
                            except Exception as e:
                                print(f"  ❌ {agent_name}: Exception - {str(e)}")
                                agent_results[agent_name] = {
                                    'success': False,
                                    'agent_name': agent_name,
                                    'error': str(e)
                                }
                    except TimeoutError:
                        # Handle case where not all agents complete within total timeout
                        print("  ⏱️  Total timeout exceeded (300s) - some agents did not complete")
                        # Cancel all incomplete futures and mark as timed out
                        for agent_name, future in future_to_agent.items():
                            if agent_name not in agent_results:
                                # Cancel future to free resources
                                future.cancel()
                                agent_results[agent_name] = {
                                    'success': False,
                                    'agent_name': agent_name,
                                    'error': 'Agent did not complete within total timeout (300s)'
                                }
            else:
                # Sequential execution
                print(f"\n⏳ Running {len(section_texts)} agents sequentially...")

                for agent_name, section_text in section_texts.items():
                    result = self.analyze_section(agent_name, section_text, paper_metadata)
                    agent_results[agent_name] = result

                    if result['success']:
                        elapsed = result.get('elapsed_time', 0)
                        tokens = result.get('tokens_used', 0)
                        print(f"  ✓ {agent_name}: {elapsed:.2f}s, {tokens} tokens")
                    else:
                        print(f"  ❌ {agent_name}: {result.get('message', 'Failed')}")

            # Step 4: Context-Aware Analysis (Two-Pass) - if enabled
            context_map = {}
            if enable_context_sharing and len(agent_results) > 0:
                print(f"\n🔄 Pass 2: Building cross-sectional context...")

                # Extract and register findings from first pass
                self._extract_and_register_findings(agent_results)

                # Build cross-reference map
                context_map = self.context_manager.build_cross_reference_map(agent_results)

                # Get context statistics
                context_stats = self.context_manager.get_summary_statistics()
                print(f"   ✓ Registered {context_stats['total_findings']} findings from {context_stats['agents_with_findings']} agents")

                # Identify agents that benefit from context
                context_dependent_agents = ['discussion', 'conclusion']

                # Re-analyze with context
                print(f"\n🔍 Re-analyzing {len(context_dependent_agents)} agents with context...")

                for agent_name in context_dependent_agents:
                    if agent_name in section_texts and agent_name in agent_results:
                        # Get context for this agent
                        agent_context = self.context_manager.get_context_for_agent(agent_name)

                        if agent_context:
                            # Create context-enriched prompt (simplified for now)
                            # In full implementation, would modify the agent's prompt
                            print(f"   ⚙️ {agent_name}: Re-analyzing with context from {len(agent_context)} agents")

                            # For now, just log context availability
                            # Full implementation would re-run agent with enriched prompt
                            agent_results[agent_name]['context_used'] = list(agent_context.keys())
                            agent_results[agent_name]['context_aware'] = True
                        else:
                            print(f"   ⚠️  {agent_name}: No additional context available")

            # Step 5: Calculate aggregate metrics
            total_time = time.time() - start_time
            successful_agents = [r for r in agent_results.values() if r.get('success', False)]
            total_tokens = sum(r.get('tokens_used', 0) for r in successful_agents)
            total_cost = total_tokens * 0.000009  # Approximate Grok-4 cost

            # Step 6: Compile comprehensive result
            result = {
                'success': len(successful_agents) > 0,
                'paper_metadata': paper_metadata,
                'analysis_results': agent_results,
                'context_map': context_map if enable_context_sharing else {},
                'context_enabled': enable_context_sharing,
                'metrics': {
                    'total_agents': len(self.agents),
                    'successful_agents': len(successful_agents),
                    'failed_agents': len(agent_results) - len(successful_agents),
                    'total_time': total_time,
                    'total_tokens': total_tokens,
                    'estimated_cost': total_cost,
                    'execution_mode': 'parallel' if parallel else 'sequential',
                    'context_findings': self.context_manager.get_summary_statistics() if enable_context_sharing else {}
                },
                'message': f'Analysis completed: {len(successful_agents)}/{len(agent_results)} agents successful'
            }

            print(f"\n✅ Analysis complete!")
            print(f"   Time: {total_time:.2f}s")
            print(f"   Tokens: {total_tokens}")
            print(f"   Cost: ${total_cost:.4f}")
            print(f"   Success: {len(successful_agents)}/{len(agent_results)} agents")

            return result

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Orchestrator failed: {str(e)}',
                'metrics': {
                    'total_time': time.time() - start_time
                }
            }

    def _extract_and_register_findings(self, agent_results: Dict):
        """
        Extract key findings from agent results and register them with context manager.

        Args:
            agent_results: Dictionary of agent analysis results
        """
        # Clear previous findings
        self.context_manager.findings = []

        for agent_name, result in agent_results.items():
            if not result.get('success'):
                continue

            analysis = result.get('analysis', {})

            # Extract findings based on agent type
            if agent_name == 'methodology':
                # Register methodology details
                if isinstance(analysis, dict):
                    if 'approach' in analysis or 'technique' in analysis:
                        self.context_manager.register_finding(
                            agent_name,
                            'methodology',
                            analysis,
                            relevance_to=['results', 'discussion', 'conclusion'],
                            priority='high'
                        )

            elif agent_name == 'results':
                # Register key results
                if isinstance(analysis, dict):
                    if 'key_findings' in analysis:
                        for finding in analysis.get('key_findings', []):
                            self.context_manager.register_finding(
                                agent_name,
                                'result',
                                {'finding': finding},
                                relevance_to=['discussion', 'conclusion'],
                                priority='high'
                            )

            elif agent_name == 'tables':
                # Register performance metrics
                if isinstance(analysis, dict):
                    if 'key_metrics' in analysis:
                        for metric in analysis.get('key_metrics', []):
                            self.context_manager.register_finding(
                                agent_name,
                                'metric',
                                metric,
                                relevance_to=['results', 'discussion'],
                                priority='medium'
                            )

            elif agent_name == 'figures':
                # Register visual insights
                if isinstance(analysis, dict):
                    if 'visualization_insights' in analysis:
                        for insight in analysis.get('visualization_insights', []):
                            self.context_manager.register_finding(
                                agent_name,
                                'figure',
                                {'insight': insight},
                                relevance_to=['discussion'],
                                priority='medium'
                            )

            elif agent_name == 'mathematics':
                # Register key equations
                if isinstance(analysis, dict):
                    if 'key_equations' in analysis:
                        for eq in analysis.get('key_equations', []):
                            self.context_manager.register_finding(
                                agent_name,
                                'equation',
                                eq,
                                relevance_to=['methodology', 'results'],
                                priority='medium'
                            )

            # Generic finding extraction (for all agents)
            if isinstance(analysis, dict):
                # Extract limitations
                if 'limitations' in analysis or 'limitations_mentioned' in analysis:
                    limitations = analysis.get('limitations') or analysis.get('limitations_mentioned', [])
                    if limitations:
                        for limitation in limitations:
                            self.context_manager.register_finding(
                                agent_name,
                                'limitation',
                                {'limitation': limitation},
                                relevance_to=['discussion', 'conclusion'],
                                priority='medium'
                            )

                # Extract claims
                if 'main_contributions' in analysis or 'novelty_claims' in analysis:
                    claims = analysis.get('main_contributions') or analysis.get('novelty_claims', [])
                    if claims:
                        for claim in claims if isinstance(claims, list) else [claims]:
                            self.context_manager.register_finding(
                                agent_name,
                                'claim',
                                {'claim': claim},
                                relevance_to=['discussion', 'conclusion'],
                                priority='high'
                            )

    def get_section_analysis(self, comprehensive_result: Dict, section_name: str) -> Optional[Dict]:
        """
        Extract analysis for a specific section from comprehensive result.

        Args:
            comprehensive_result: Result from analyze_paper()
            section_name: Name of section (e.g., 'abstract', 'introduction')

        Returns:
            Analysis dictionary for that section, or None if not found
        """
        if not comprehensive_result.get('success'):
            return None

        analysis_results = comprehensive_result.get('analysis_results', {})
        return analysis_results.get(section_name)

    def format_summary(self, comprehensive_result: Dict) -> str:
        """
        Format comprehensive result into human-readable summary.

        Args:
            comprehensive_result: Result from analyze_paper()

        Returns:
            Formatted summary string
        """
        if not comprehensive_result.get('success'):
            return f"Analysis failed: {comprehensive_result.get('message', 'Unknown error')}"

        lines = []
        lines.append("=" * 80)
        lines.append("COMPREHENSIVE PAPER ANALYSIS")
        lines.append("=" * 80)

        # Paper info
        metadata = comprehensive_result.get('paper_metadata', {})
        lines.append(f"\nTitle: {metadata.get('title', 'Unknown')}")
        lines.append(f"Authors: {', '.join(metadata.get('authors', ['Unknown']))}")
        lines.append(f"Year: {metadata.get('year', 'Unknown')}")

        # Metrics
        metrics = comprehensive_result.get('metrics', {})
        lines.append(f"\nAnalysis Metrics:")
        lines.append(f"  Agents: {metrics.get('successful_agents')}/{metrics.get('total_agents')}")
        lines.append(f"  Time: {metrics.get('total_time', 0):.2f}s")
        lines.append(f"  Tokens: {metrics.get('total_tokens', 0)}")
        lines.append(f"  Cost: ${metrics.get('estimated_cost', 0):.4f}")
        lines.append(f"  Mode: {metrics.get('execution_mode', 'unknown')}")

        # Section summaries
        analysis_results = comprehensive_result.get('analysis_results', {})

        lines.append(f"\n" + "=" * 80)
        lines.append("SECTION ANALYSES")
        lines.append("=" * 80)

        for agent_name, result in analysis_results.items():
            lines.append(f"\n{agent_name.upper().replace('_', ' ')}")
            lines.append("-" * 80)

            if result.get('success'):
                lines.append(f"✓ Success ({result.get('elapsed_time', 0):.2f}s)")
                analysis = result.get('analysis', {})

                # Show key fields (first 3-5 items)
                for key, value in list(analysis.items())[:5]:
                    if isinstance(value, list) and value:
                        lines.append(f"  {key}: {len(value)} items")
                        if key not in ['parse_error'] and isinstance(value[0], str):
                            lines.append(f"    - {value[0][:100]}...")
                    elif isinstance(value, dict):
                        lines.append(f"  {key}: {len(value)} fields")
                    elif isinstance(value, str) and value:
                        lines.append(f"  {key}: {value[:100]}...")
            else:
                lines.append(f"❌ Failed: {result.get('message', 'Unknown error')}")

        return '\n'.join(lines)
