"""
Multi-Agent Search Interface
Parallel search across multiple academic databases with AI orchestration
"""

import streamlit as st

# Page Configuration - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Multi-Agent Search",
    page_icon="🤖",
    layout="wide"
)

import pandas as pd
from datetime import datetime
import sys
sys.path.append('..')

from multi_agent_system import create_orchestrator
from quality_scoring import PaperFilter
import config

# Import shared analysis functions (avoids circular import issues with app.py)
try:
    from shared_analysis import (
        analyze_paper_comprehensive_shared as analyze_paper_comprehensive,
        generate_comprehensive_summary_paragraphs_shared as generate_comprehensive_summary_paragraphs,
        display_comprehensive_agent_analysis_shared as display_comprehensive_agent_analysis,
        display_document_chat_shared as display_document_chat
    )
    print("✅ Successfully imported shared analysis functions")
except Exception as e:
    print(f"⚠️ Failed to import shared analysis functions: {e}")
    # Fallback: define placeholder functions
    def analyze_paper_comprehensive(paper, rank):
        st.warning("Analysis feature not available. Please use the main 'app' page for full analysis.")
        return None

    def display_document_chat(doc_id):
        st.warning("Chat feature not available. Please use the main 'app' page for document chat.")
        return None

    def generate_comprehensive_summary_paragraphs(analysis_results, synthesis, paper_metadata):
        return {
            'introduction': 'Analysis feature not available.',
            'methodology': 'Analysis feature not available.',
            'results': 'Analysis feature not available.',
            'discussion': 'Analysis feature not available.'
        }

    def display_comprehensive_agent_analysis(agent_name, agent_result):
        st.warning("Detailed analysis not available.")
        return None

# Session State
if 'multi_agent_results' not in st.session_state:
    st.session_state.multi_agent_results = []
if 'multi_agent_metrics' not in st.session_state:
    st.session_state.multi_agent_metrics = None
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = None

# Custom CSS
st.markdown("""
<style>
    .agent-card {
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
    }
    .agent-success {
        background-color: #d4edda;
        border-color: #c3e6cb;
    }
    .agent-running {
        background-color: #fff3cd;
        border-color: #ffeaa7;
    }
    .agent-failed {
        background-color: #f8d7da;
        border-color: #f5c6cb;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🤖 Multi-Agent Research Search")
st.markdown("""
Search across **6 academic databases simultaneously** using an AI orchestrator.
The system uses parallel agents to search, aggregate, deduplicate, and synthesize results.
""")

# Sidebar - Agent Configuration
with st.sidebar:
    st.header("🔧 Agent Configuration")

    # Grok Configuration
    st.subheader("🚀 AI Engine")
    use_grok = st.checkbox(
        "Use Grok-4 (Fast Reasoning)",
        value=config.GROK_SETTINGS.get('enabled', True) and config.GROK_SETTINGS.get('use_for_multi_agent', True),
        help="Use Grok-4 API for faster and more efficient query planning and result synthesis"
    )

    if use_grok:
        st.success("⚡ Grok-4 enabled - Ultra-fast multi-agent orchestration")
    else:
        st.info("🤖 Using local Ollama model")

    # Performance optimizations indicator
    st.info("""
    🚀 **Performance Optimizations Active:**
    - Smart source selection (60% fewer API calls)
    - Exponential backoff (graceful rate limit handling)
    - Field limiting (30% faster responses)
    - Optimized timeouts (15s max per source)
    """)

    st.markdown("---")

    # Source selection
    st.subheader("Data Sources")
    st.caption("Select which databases to search")

    enabled_sources = []

    # Semantic Scholar (always available)
    if st.checkbox(
        "Semantic Scholar",
        value=True,
        help="200M+ papers with rich metadata"
    ):
        enabled_sources.append('semantic_scholar')

    # arXiv (always available)
    if st.checkbox(
        "arXiv",
        value=True,
        help="Latest CS/AI/Physics preprints"
    ):
        enabled_sources.append('arxiv')

    # OpenAlex (always available)
    if st.checkbox(
        "OpenAlex",
        value=True,
        help="240M+ papers, largest coverage"
    ):
        enabled_sources.append('openalex')

    # Crossref (always available)
    if st.checkbox(
        "Crossref",
        value=True,
        help="150M+ DOI records"
    ):
        enabled_sources.append('crossref')

    # CORE (requires API key)
    if st.checkbox(
        "CORE",
        value=False,
        help="Open access papers (requires API key)"
    ):
        enabled_sources.append('core')

    # PubMed (requires email)
    if st.checkbox(
        "PubMed",
        value=False,
        help="Biomedical papers (requires email)"
    ):
        enabled_sources.append('pubmed')

    st.markdown("---")

    # Orchestrator Settings
    st.subheader("🤖 AI Orchestrator")

    enable_planning = st.checkbox(
        "Enable LLM Planning",
        value=True,
        help="Use LLM to optimize search strategy"
    )

    enable_synthesis = st.checkbox(
        "Enable Result Synthesis",
        value=True,
        help="Use LLM to summarize findings"
    )

    orchestrator_model = st.selectbox(
        "LLM Model",
        config.LLM_SETTINGS['available_models'],
        index=0,
        help="Model for planning and synthesis"
    )

    st.markdown("---")

    # Results Configuration
    st.subheader("📊 Results Settings")

    max_per_source = st.slider(
        "Max results per source",
        10, 50, 20,  # Changed: default from 50 to 20, max from 100 to 50
        step=5,
        help="Papers to fetch from each database (20 recommended for speed)"
    )

    min_quality = st.slider(
        "Min quality score",
        0.0, 1.0, 0.3, 0.05,
        help="Filter by quality score"
    )

    # Show optimization info
    if max_per_source <= 20:
        st.caption("✅ Optimal setting - Fast search (8-12 seconds)")
    elif max_per_source <= 30:
        st.caption("⚠️ Moderate setting - May take 15-20 seconds")
    else:
        st.caption("🐌 High setting - May take 25-35 seconds")

# Main Search Interface
col1, col2 = st.columns([4, 1])

with col1:
    search_query = st.text_area(
        "🔍 Enter your research query:",
        height=100,
        placeholder="E.g., 'multi-agent systems for information retrieval' or 'quantum machine learning algorithms'"
    )

with col2:
    st.write("")  # Spacing
    st.write("")
    search_button = st.button(
        "🚀 Multi-Agent Search",
        type="primary",
        use_container_width=True
    )

# Source summary
if enabled_sources:
    st.caption(f"✓ {len(enabled_sources)} sources enabled: {', '.join(enabled_sources)}")
else:
    st.warning("⚠️ Please select at least one data source from the sidebar")

# Perform Search
if search_button and search_query and enabled_sources:
    # Create orchestrator
    orchestrator_config = {
        's2_api_key': st.secrets.get("S2_API_KEY") if hasattr(st, 'secrets') else None,
        'email': st.secrets.get("OPENALEX_EMAIL") if hasattr(st, 'secrets') else None,
        'core_api_key': st.secrets.get("CORE_API_KEY") if hasattr(st, 'secrets') else None,
        'pubmed_api_key': st.secrets.get("PUBMED_API_KEY") if hasattr(st, 'secrets') else None,
        'llm_model': orchestrator_model,
        'use_grok': use_grok
    }

    orchestrator = create_orchestrator(orchestrator_config)
    st.session_state.orchestrator = orchestrator

    # Planning Phase (if enabled)
    if enable_planning:
        with st.spinner("🧠 AI Orchestrator planning search strategy..."):
            plan = orchestrator.plan_search(search_query, enabled_sources)

            with st.expander("📋 Search Plan", expanded=True):
                st.markdown(f"**Original Query:** {plan['original_query']}")
                if plan['refined_query'] != plan['original_query']:
                    st.markdown(f"**Refined Query:** {plan['refined_query']}")
                    st.info(f"💡 Query enhanced by AI orchestrator")

                st.markdown(f"**Source Priority:** {', '.join(plan['source_priority'])}")
                st.markdown(f"**Strategy:**\n{plan['reasoning']}")

    # Execution Phase
    st.markdown("---")
    st.subheader("🔄 Agents Executing Search")

    # Create placeholders for agent status
    agent_status_container = st.container()

    with st.spinner(f"🤖 Executing parallel search across {len(enabled_sources)} sources..."):
        # Execute search
        result_data = orchestrator.search_parallel(
            search_query,
            enabled_sources,
            max_per_source
        )

        st.session_state.multi_agent_results = result_data['results']
        st.session_state.multi_agent_metrics = result_data['metrics']

    # Display Agent Metrics
    with agent_status_container:
        metrics = st.session_state.multi_agent_metrics
        agent_metrics = metrics['agents']

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Results", metrics['total_results'])
        with col2:
            st.metric("Raw Results", metrics['total_raw_results'])
        with col3:
            st.metric("Duration", f"{metrics['duration']:.2f}s")
        with col4:
            success_count = sum(1 for a in agent_metrics if a['status'] == 'completed')
            st.metric("Agents Success", f"{success_count}/{len(agent_metrics)}")

        # Individual agent status
        st.markdown("#### Agent Performance")

        for agent in agent_metrics:
            status_class = {
                'completed': 'agent-success',
                'searching': 'agent-running',
                'failed': 'agent-failed'
            }.get(agent['status'], 'agent-card')

            status_icon = {
                'completed': '✅',
                'searching': '⏳',
                'failed': '❌'
            }.get(agent['status'], '⚪')

            st.markdown(f"""
            <div class="agent-card {status_class}">
                <strong>{status_icon} {agent['name']}</strong> ({agent['source']})<br/>
                Results: {agent['results_count']} | Duration: {agent['duration']:.2f}s
                {f'| Error: {agent["error"]}' if agent.get('error') else ''}
            </div>
            """, unsafe_allow_html=True)

    # Synthesis Phase (if enabled)
    if enable_synthesis and st.session_state.multi_agent_results:
        st.markdown("---")
        st.subheader("🧬 AI Synthesis")

        with st.spinner("🤖 Synthesizing results..."):
            synthesis = orchestrator.synthesize_results(
                st.session_state.multi_agent_results,
                top_n=10,
                query=search_query
            )

        st.info(synthesis)

# Display Results
if st.session_state.multi_agent_results:
    st.markdown("---")
    st.subheader(f"📄 Results ({len(st.session_state.multi_agent_results)} papers)")

    # Filter by quality
    filtered_results = [
        p for p in st.session_state.multi_agent_results
        if p.get('quality_score', 0) >= min_quality
    ]

    st.caption(f"Showing {len(filtered_results)} papers after quality filtering")

    # Display results
    for i, paper in enumerate(filtered_results[:50], 1):  # Limit to 50 for performance
        # Container for each paper
        with st.container():
            st.markdown(f"### {i}. {paper['title']}")

            # Basic metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Year", paper.get('year', 'N/A'))
            with col2:
                st.metric("Citations", paper.get('citations', 'N/A'))
            with col3:
                st.metric("Quality", f"{paper.get('quality_score', 0):.2f}")

            # Multi-Agent Analysis Buttons (ALWAYS VISIBLE)
            st.markdown("---")
            st.markdown("**🤖 AI-Powered Analysis:**")

            analysis_col1, analysis_col2 = st.columns(2)

            with analysis_col1:
                if st.button("🎯 Analyze Paper (7 Agents)", key=f"analyze_multi_{i}", use_container_width=True, type="primary"):
                    st.session_state[f'show_analysis_multi_{i}'] = not st.session_state.get(f'show_analysis_multi_{i}', False)

            with analysis_col2:
                if st.button("💬 Chat with Paper (RAG)", key=f"chat_multi_{i}", use_container_width=True):
                    # Store paper data for chat
                    st.session_state.chat_paper_data = paper

                    # If analysis is available, generate summary for chat
                    if st.session_state.get(f'analysis_result_multi_{i}'):
                        result = st.session_state[f'analysis_result_multi_{i}']
                        analysis_results = result['analysis']['analysis_results']
                        synthesis = result['synthesis']['synthesis']
                        paper_metadata = result['analysis'].get('paper_metadata', {'title': paper.get('title', 'Unknown')})

                        # Generate comprehensive summary paragraphs for chat
                        st.session_state.chat_summary = generate_comprehensive_summary_paragraphs(
                            analysis_results, synthesis, paper_metadata
                        )
                    else:
                        # No analysis available - create basic summary from abstract
                        st.session_state.chat_summary = {
                            'introduction': f"This paper titled '{paper.get('title', 'Unknown')}' was published in {paper.get('year', 'N/A')}. {paper.get('abstract', 'Abstract not available.')}",
                            'methodology': 'Comprehensive analysis not yet performed. Click "Analyze Paper" first for detailed insights.',
                            'results': 'Analysis pending.',
                            'discussion': 'To get detailed analysis, please run the 7-agent analysis first.'
                        }

                    # Initialize chat state
                    st.session_state.chat_messages = []
                    st.session_state.chat_initialized = False

                    # Redirect to chat page
                    st.switch_page("pages/Chat_With_Paper.py")

            # Show Analysis Interface (if button clicked)
            if st.session_state.get(f'show_analysis_multi_{i}', False):
                st.markdown("---")
                st.markdown("### 🎯 Comprehensive Multi-Agent Analysis")
                st.caption("Deep analysis using 7 specialized agents + synthesis")

                if st.button("▶️ Start Analysis", key=f"start_analysis_multi_{i}", type="primary"):
                    result = analyze_paper_comprehensive(paper, i)

                    if result:
                        # Store analysis in session state
                        st.session_state[f'analysis_result_multi_{i}'] = result
                        st.rerun()

            # Display Analysis Results (if available)
            if st.session_state.get(f'analysis_result_multi_{i}'):
                st.markdown("---")
                st.markdown("### 📊 Analysis Results")

                result = st.session_state[f'analysis_result_multi_{i}']
                synthesis = result['synthesis']['synthesis']
                analysis_metrics = result['analysis']['metrics']
                synthesis_metrics = result['synthesis']

                # Performance metrics
                perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)

                with perf_col1:
                    total_time = analysis_metrics['total_time'] + synthesis_metrics['elapsed_time']
                    st.metric("⚡ Total Time", f"{total_time:.1f}s")

                with perf_col2:
                    st.metric("✅ Agents", f"{analysis_metrics['successful_agents']}/7")

                with perf_col3:
                    total_tokens = analysis_metrics['total_tokens'] + synthesis_metrics.get('tokens_used', 0)
                    st.metric("🔤 Tokens", f"{total_tokens:,}")

                with perf_col4:
                    total_cost = (total_tokens * 0.000009)
                    st.metric("💰 Cost", f"${total_cost:.4f}")

                # Overall Assessment
                st.markdown("#### 📈 Overall Assessment")
                assessment = synthesis.get('overall_assessment', {})

                assess_col1, assess_col2, assess_col3, assess_col4 = st.columns(4)

                with assess_col1:
                    quality = assessment.get('quality', 'N/A')
                    emoji = "🟢" if quality == "high" else "🟡" if quality == "medium" else "🔴"
                    st.metric(f"{emoji} Quality", quality.capitalize())

                with assess_col2:
                    novelty = assessment.get('novelty', 'N/A')
                    emoji = "🟢" if novelty == "high" else "🟡" if novelty == "medium" else "🔴"
                    st.metric(f"{emoji} Novelty", novelty.capitalize())

                with assess_col3:
                    impact = assessment.get('impact', 'N/A')
                    emoji = "🟢" if impact == "high" else "🟡" if impact == "medium" else "🔴"
                    st.metric(f"{emoji} Impact", impact.capitalize())

                with assess_col4:
                    rigor = assessment.get('rigor', 'N/A')
                    emoji = "🟢" if rigor == "high" else "🟡" if rigor == "medium" else "🔴"
                    st.metric(f"{emoji} Rigor", rigor.capitalize())

                # === NEW SIMPLIFIED FORMAT: Topic-Based Comprehensive Paragraphs ===
                st.markdown("#### 📄 Comprehensive Paper Summary")
                st.caption("Generated from analysis by all 7 specialized agents")

                # Generate comprehensive paragraphs from real agent data (with LLM synthesis)
                with st.spinner("🔄 Synthesizing detailed comprehensive paragraphs from all 7 agents... (10-15 seconds)"):
                    analysis_results = result['analysis']['analysis_results']
                    paper_metadata = result['analysis'].get('paper_metadata', {'title': paper.get('title', 'Unknown')})
                    paragraphs = generate_comprehensive_summary_paragraphs(analysis_results, synthesis, paper_metadata)

                # Display topic-based paragraphs
                st.markdown("##### 🎯 Introduction & Research Context")
                st.write(paragraphs['introduction'])

                st.markdown("##### 🔬 Methodology & Approach")
                st.write(paragraphs['methodology'])

                st.markdown("##### 📊 Results & Key Findings")
                st.write(paragraphs['results'])

                st.markdown("##### 💭 Discussion, Implications & Conclusions")
                st.write(paragraphs['discussion'])

                # Optional: Keep detailed agent analysis in expandable section for power users
                with st.expander("🔍 View Detailed Agent-by-Agent Analysis", expanded=False):
                    st.caption("💡 **For advanced users**: See detailed breakdown from each of the 7 specialized agents")

                    # Create tabs for each agent
                    agent_names = list(analysis_results.keys())
                    if len(agent_names) > 0:
                        tabs = st.tabs([name.replace('_', ' ').title() for name in agent_names])

                        for tab, agent_name in zip(tabs, agent_names):
                            with tab:
                                agent_result = analysis_results[agent_name]
                                display_comprehensive_agent_analysis(agent_name, agent_result)

                # Clear analysis button
                if st.button("🗑️ Clear Analysis", key=f"clear_analysis_multi_{i}"):
                    del st.session_state[f'analysis_result_multi_{i}']
                    st.rerun()

            # Show Chat Interface (if button clicked)
            if st.session_state.get(f'show_chat_multi_{i}', False):
                st.markdown("---")
                st.markdown("### 💬 Chat with Paper (RAG)")
                st.caption("Ask questions about this paper")

                # Simple chat interface
                user_question = st.text_input(
                    "Your question:",
                    key=f"chat_question_multi_{i}",
                    placeholder="E.g., What is the main contribution of this paper?"
                )

                if st.button("💬 Ask", key=f"ask_multi_{i}"):
                    if user_question:
                        with st.spinner("Thinking..."):
                            # Store paper data in a simple format for chat
                            chat_context = f"""
Paper Title: {paper.get('title', 'Unknown')}
Authors: {', '.join([a['name'] for a in paper.get('authors', [])])}
Year: {paper.get('year', 'N/A')}
Abstract: {paper.get('abstract', 'No abstract available')}
"""
                            st.markdown("**Answer:**")
                            st.info(f"Question: {user_question}\n\n[Chat functionality will be connected to RAG system]")

        # Additional details in expander
        with st.expander("📄 Abstract & Details", expanded=False):

            # Authors and venue
            authors = ', '.join([a['name'] for a in paper.get('authors', [])[:5]])
            st.markdown(f"**Authors:** {authors}")
            st.markdown(f"**Venue:** {paper.get('venue', 'Unknown')}")
            st.markdown(f"**Source:** {paper.get('source', 'Unknown')}")

            # Abstract
            abstract = paper.get('abstract', 'No abstract')
            st.markdown(f"**Abstract:** {abstract[:500]}...")

            # Links
            col1, col2, col3 = st.columns(3)
            with col1:
                if paper.get('pdf_url'):
                    st.link_button("📖 PDF", paper['pdf_url'], use_container_width=True)
            with col2:
                if paper.get('doi'):
                    st.link_button("🔗 DOI", f"https://doi.org/{paper['doi']}", use_container_width=True)
            with col3:
                if paper.get('arxiv_id'):
                    st.link_button("📝 arXiv", f"https://arxiv.org/abs/{paper['arxiv_id']}", use_container_width=True)

elif search_button and search_query:
    st.warning("No results found. Try adjusting your query or enabling more sources.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <p>Multi-Agent System powered by Ollama LLMs</p>
    <p>Sources: Semantic Scholar • arXiv • OpenAlex • Crossref • CORE • PubMed</p>
</div>
""", unsafe_allow_html=True)
