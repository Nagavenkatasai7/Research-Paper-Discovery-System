"""
Research Paper Discovery System - Main Streamlit Application
A Google-like search interface for academic papers and research blog posts
"""

# Fix for PyTorch + Streamlit file watcher issue
# This prevents the "Examining the path of torch.classes" error
try:
    import torch
    torch.classes.__path__ = []
except (ImportError, AttributeError):
    pass  # torch not installed or already patched

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional

# Import custom modules
from api_clients import MultiAPISearcher
from quality_scoring import PaperQualityScorer, PaperFilter
from utils import (
    generate_bibtex, format_authors, truncate_text,
    BlogPostSearcher, format_venue, get_paper_age_category
)
import config

# Import LLM features
from llm_client import (
    get_llm_client, PaperAnalyzer, QueryAssistant,
    cached_summarize_paper, cached_extract_insights,
    cached_suggest_queries, cached_expand_keywords
)

# Import Grok features
from grok_client import (
    get_grok_client, GrokPaperAnalyzer, GrokQueryAssistant,
    cached_grok_expand_keywords
)

# Import Multi-Agent Analysis System (Phase 3)
from rag_system.analysis_agents import DocumentAnalysisOrchestrator, SynthesisAgent
from rag_system.pdf_processor import PDFProcessor
from rag_system.pdf_downloader import PDFDownloader

# Import Phase 4 Components (RAG + Chat)
from rag_system.paper_analysis_workflow import PaperAnalysisWorkflow
from rag_system.document_chat import DocumentChatSystem
from rag_system.rag_engine import RAGEngine
from rag_system.database import RAGDatabase

import os


# Page Configuration
st.set_page_config(
    page_title="Research Paper Discovery System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .paper-card {
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        background-color: #fafafa;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 0.5rem;
        border-radius: 4px;
        text-align: center;
    }
    .quality-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .quality-high {
        background-color: #d4edda;
        color: #155724;
    }
    .quality-medium {
        background-color: #fff3cd;
        color: #856404;
    }
    .quality-low {
        background-color: #f8d7da;
        color: #721c24;
    }
    .blog-post {
        padding: 1rem;
        border-left: 3px solid #1f77b4;
        background-color: #f8f9fa;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# Session State Initialization
def init_session_state():
    """Initialize all session state variables with user session tracking"""
    # Generate unique session ID if not exists (for multi-user tracking)
    if 'session_id' not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.session_state.session_start = datetime.now()
        # Track concurrent users (for observability)
        if 'active_sessions' not in st.session_state:
            st.session_state.active_sessions = 1

    defaults = {
        'search_results': [],
        'blog_results': [],
        'current_page': 0,
        'search_query': '',
        'last_query': '',
        'filters': {
            'min_citations': 0,
            'year_range': (2020, datetime.now().year),
            'venues': [],
            'domains': [],
            'min_quality': 0.3
        },
        'show_blogs': True,
        'search_sources': ['semantic_scholar', 'arxiv'],
        # LLM settings
        'llm_enabled': config.LLM_SETTINGS['enabled'],
        'selected_model': config.LLM_SETTINGS['default_model'],
        'show_query_suggestions': True,
        'qa_mode': False,
        'selected_papers_for_comparison': [],
        'auto_enhance_query': True,  # Enable automatic query enhancement by default
        'use_grok_for_enhancement': config.GROK_SETTINGS.get('enabled', False),  # Use Grok for faster query enhancement
        # Multi-user support metadata
        'is_multi_user_enabled': True,  # Flag indicating multi-user support is active
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# Cached Resources
@st.cache_resource
def load_orchestrator():
    """Load multi-agent orchestrator (singleton) - uses ALL 6 sources"""
    from multi_agent_system import create_orchestrator
    config_dict = {
        's2_api_key': os.getenv('SEMANTIC_SCHOLAR_API_KEY', ''),
        'email': os.getenv('USER_EMAIL', ''),
        'core_api_key': os.getenv('CORE_API_KEY', ''),
        'pubmed_api_key': os.getenv('PUBMED_API_KEY', '')
    }
    return create_orchestrator(config_dict)


@st.cache_resource
def load_scorer():
    """Load quality scorer (singleton)"""
    return PaperQualityScorer()


@st.cache_resource
def load_blog_searcher():
    """Load blog searcher (singleton)"""
    return BlogPostSearcher()


def load_analysis_orchestrator():
    """
    Load document analysis orchestrator (NON-singleton)

    NOTE: Returns a fresh instance each time to avoid race conditions.
    The orchestrator maintains internal state (context_manager, agent results)
    that could conflict between concurrent users if shared.
    """
    return DocumentAnalysisOrchestrator()


@st.cache_resource
def load_synthesis_agent():
    """Load synthesis agent (singleton)"""
    return SynthesisAgent()


@st.cache_resource
def load_pdf_downloader():
    """Load PDF downloader (singleton)"""
    return PDFDownloader()


# Phase 4 Cached Resources
@st.cache_resource
def load_workflow_manager():
    """Load workflow manager (singleton)"""
    return PaperAnalysisWorkflow()


@st.cache_resource
def load_database():
    """Load database (singleton)"""
    return RAGDatabase()


# Cached Search Functions
@st.cache_data(ttl=config.CACHE_TTL['search_results'], show_spinner=False)
def search_papers(query: str, sources: List[str], max_results: int = 50) -> List[Dict]:
    """
    Search papers using multi-agent orchestrator - coordinates ALL 6 agents in parallel

    NOTE: Creates new orchestrator instance per request to avoid race conditions
    between concurrent users. The orchestrator agents have mutable state that would
    otherwise get mixed between simultaneous searches.
    """
    # Create fresh orchestrator instance to avoid race conditions
    # DO NOT use load_orchestrator() singleton here as it causes state conflicts
    from multi_agent_system import create_orchestrator
    config_dict = {
        's2_api_key': os.getenv('SEMANTIC_SCHOLAR_API_KEY', ''),
        'email': os.getenv('USER_EMAIL', ''),
        'core_api_key': os.getenv('CORE_API_KEY', ''),
        'pubmed_api_key': os.getenv('PUBMED_API_KEY', '')
    }
    orchestrator = create_orchestrator(config_dict)

    # Use parallel search with orchestration
    result = orchestrator.search_parallel(
        query=query,
        enabled_sources=sources,
        max_results_per_source=max_results
    )

    # Return just the papers (orchestrator returns dict with 'results' and 'metrics')
    return result.get('results', [])


@st.cache_data(ttl=config.CACHE_TTL['search_results'], show_spinner=False)
def search_blogs(query: str, max_results: int = 10) -> List[Dict]:
    """Search blog posts with caching"""
    blog_searcher = load_blog_searcher()
    return blog_searcher.search_blogs(query, max_results=max_results)


def analyze_paper_comprehensive(paper: Dict, rank: int):
    """
    Perform comprehensive multi-agent analysis of a research paper.
    2025 Enhancement: Metadata-first approach (TLDR + Abstract) with PDF/scraping fallback
    """
    # Create progress container
    progress_container = st.container()

    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Step 1: Extract content from metadata (FASTEST - no download needed!)
            status_text.text("📊 Extracting content from metadata...")
            progress_bar.progress(10)

            from paper_content_extractor import PaperContentExtractor

            paper_id = paper.get('paper_id') or paper.get('arxiv_id') or f"paper_{rank}"
            extractor = PaperContentExtractor()
            extraction_result = extractor.extract_content(paper, paper_id)

            content_path = None
            content_source = None

            # Check if metadata is sufficient for analysis
            if extraction_result['success'] and extractor.can_analyze(extraction_result):
                # SUCCESS! We have enough content from metadata alone
                content_path = extraction_result['file_path']
                content_source = "metadata"
                st.info(f"✅ {extraction_result['message']}")
                st.caption(extractor.get_content_summary(extraction_result))
                progress_bar.progress(20)

            else:
                # Metadata insufficient, try PDF download
                st.warning("⚠️ Metadata insufficient for analysis, trying PDF download...")

                pdf_url = paper.get('pdf_url')
                if not pdf_url:
                    # No PDF available, try web scraping
                    st.warning("⚠️ No PDF URL available, trying web scraping...")
                    progress_bar.progress(15)

                    from web_scraper import PaperWebScraper, create_text_file_from_scraped_content

                    scraper = PaperWebScraper()

                    # Get paper URL (try Semantic Scholar or arXiv)
                    scrape_url = None
                    if paper.get('paper_id'):
                        scrape_url = f"https://www.semanticscholar.org/paper/{paper['paper_id']}"
                    elif paper.get('arxiv_id'):
                        scrape_url = f"https://arxiv.org/abs/{paper['arxiv_id']}"

                    if not scrape_url:
                        st.error("❌ No content source available (metadata, PDF, or web page)")
                        return None

                    # Scrape paper content
                    scrape_result = scraper.scrape_paper(scrape_url, paper_id)

                    if not scrape_result['success']:
                        st.error(f"❌ All content sources failed: {scrape_result['message']}")
                        return None

                    # Create text file from scraped content
                    content_path = create_text_file_from_scraped_content(
                        scrape_result['content'],
                        paper_id
                    )
                    content_source = "web_scraping"
                    st.success(f"✅ Successfully scraped content from web page!")
                    progress_bar.progress(20)

                else:
                    # Try PDF download
                    downloader = load_pdf_downloader()
                    download_result = downloader.download_pdf(pdf_url, paper_id)

                    if not download_result['success']:
                        # PDF failed, try web scraping as last resort
                        st.warning(f"⚠️ PDF download failed: {download_result['message']}")
                        st.info("🌐 Trying web scraping fallback...")

                        from web_scraper import PaperWebScraper, create_text_file_from_scraped_content

                        scraper = PaperWebScraper()

                        # Get paper URL
                        scrape_url = None
                        if paper.get('paper_id'):
                            scrape_url = f"https://www.semanticscholar.org/paper/{paper['paper_id']}"
                        elif paper.get('arxiv_id'):
                            scrape_url = f"https://arxiv.org/abs/{paper['arxiv_id']}"

                        if not scrape_url:
                            st.error("❌ No fallback content source available")
                            return None

                        scrape_result = scraper.scrape_paper(scrape_url, paper_id)

                        if not scrape_result['success']:
                            st.error(f"❌ All content sources failed: {scrape_result['message']}")
                            return None

                        content_path = create_text_file_from_scraped_content(
                            scrape_result['content'],
                            paper_id
                        )
                        content_source = "web_scraping"
                        st.success(f"✅ Successfully scraped content from web page!")

                    else:
                        content_path = download_result.get('file_path') or download_result.get('path')
                        content_source = "pdf"
                        st.success(f"✅ PDF downloaded successfully!")

                    progress_bar.progress(20)

            # At this point, content_path should be set
            if not content_path:
                st.error("❌ Failed to obtain paper content from any source")
                return None

            pdf_path = content_path  # Use content_path for consistency with rest of code

            # Step 2: Prepare metadata
            status_text.text("📋 Preparing analysis...")
            paper_metadata = {
                'title': paper.get('title', 'Unknown'),
                'authors': [a.get('name', 'Unknown') for a in paper.get('authors', [])][:5],
                'year': paper.get('year', None)
            }
            progress_bar.progress(30)

            # Step 3: Multi-Agent Analysis
            status_text.text("🤖 Running 7 specialized agents in parallel...")
            progress_bar.progress(40)

            # Create fresh orchestrator instance to avoid race conditions
            orchestrator = load_analysis_orchestrator()
            analysis_result = orchestrator.analyze_paper(
                pdf_path=pdf_path,
                paper_metadata=paper_metadata,
                parallel=True,
                max_workers=7
            )

            if not analysis_result['success']:
                st.error(f"❌ Analysis failed: {analysis_result.get('message')}")
                return None

            progress_bar.progress(70)

            # Step 4: Synthesis
            status_text.text("🔬 Synthesizing findings from all agents...")
            progress_bar.progress(80)

            synthesizer = load_synthesis_agent()
            synthesis_result = synthesizer.synthesize(analysis_result)

            if not synthesis_result['success']:
                st.error(f"❌ Synthesis failed: {synthesis_result.get('message')}")
                return None

            progress_bar.progress(100)
            status_text.text("✅ Analysis complete!")

            return {
                'analysis': analysis_result,
                'synthesis': synthesis_result,
                'pdf_path': pdf_path
            }

        except Exception as e:
            st.error(f"❌ Error during analysis: {str(e)}")
            # Show full traceback for debugging
            import traceback
            st.code(traceback.format_exc())
            return None


def display_comprehensive_agent_analysis(agent_name: str, agent_result: Dict):
    """
    Display comprehensive, detailed agent analysis in a structured format.

    Args:
        agent_name: Name of the agent (e.g., 'abstract', 'methodology')
        agent_result: Dictionary containing agent analysis results
    """
    # Agent name mapping with emojis
    agent_emojis = {
        'abstract': '📋',
        'introduction': '🎯',
        'literature_review': '📚',
        'methodology': '🔬',
        'results': '📊',
        'discussion': '💭',
        'conclusion': '🎓'
    }

    emoji = agent_emojis.get(agent_name, '📄')
    display_name = agent_name.upper().replace('_', ' ')

    st.markdown(f"### {emoji} {display_name} ANALYSIS")

    if not agent_result.get('success'):
        st.error(f"❌ Analysis failed: {agent_result.get('message', 'Unknown error')}")
        return

    # Performance metrics
    elapsed = agent_result.get('elapsed_time', 0)
    tokens = agent_result.get('tokens_used', 0)
    cost = tokens * 0.000009  # Grok-4 pricing

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("⚡ Time", f"{elapsed:.2f}s")
    with metric_col2:
        st.metric("🔤 Tokens", f"{tokens:,}")
    with metric_col3:
        st.metric("💰 Cost", f"${cost:.4f}")

    st.markdown("---")

    analysis_data = agent_result.get('analysis', {})

    if not analysis_data or analysis_data.get('parse_error'):
        st.warning("⚠️ Analysis data could not be parsed properly")
        return

    # Display comprehensive analysis based on agent type
    if agent_name == 'abstract':
        display_abstract_analysis(analysis_data)
    elif agent_name == 'introduction':
        display_introduction_analysis(analysis_data)
    elif agent_name == 'literature_review':
        display_literature_analysis(analysis_data)
    elif agent_name == 'methodology':
        display_methodology_analysis(analysis_data)
    elif agent_name == 'results':
        display_results_analysis(analysis_data)
    elif agent_name == 'discussion':
        display_discussion_analysis(analysis_data)
    elif agent_name == 'conclusion':
        display_conclusion_analysis(analysis_data)
    else:
        # Generic display for unknown agent types
        display_generic_analysis(analysis_data)


def display_abstract_analysis(data: Dict):
    """Display Abstract agent analysis"""
    if data.get('problem_statement'):
        st.markdown("#### 🎯 Problem Statement")
        st.write(data['problem_statement'])

    if data.get('main_contribution'):
        st.markdown("#### 💡 Main Contribution")
        st.write(data['main_contribution'])

    if data.get('methodology_summary'):
        st.markdown("#### 🔬 Methodology Summary")
        st.write(data['methodology_summary'])

    if data.get('key_results'):
        st.markdown("#### 📊 Key Results")
        results = data['key_results']
        if isinstance(results, list):
            for i, result in enumerate(results, 1):
                st.markdown(f"{i}. {result}")
        else:
            st.write(results)

    if data.get('significance'):
        st.markdown("#### ⭐ Significance")
        st.write(data['significance'])


def display_introduction_analysis(data: Dict):
    """Display Introduction agent analysis"""
    if data.get('research_context'):
        st.markdown("#### 🌍 Research Context")
        st.write(data['research_context'])

    if data.get('research_gap'):
        st.markdown("#### 🔍 Research Gap")
        st.write(data['research_gap'])

    if data.get('research_questions'):
        st.markdown("#### ❓ Research Questions")
        questions = data['research_questions']
        if isinstance(questions, list):
            for i, q in enumerate(questions, 1):
                st.markdown(f"{i}. {q}")
        else:
            st.write(questions)

    if data.get('objectives'):
        st.markdown("#### 🎯 Objectives")
        objectives = data['objectives']
        if isinstance(objectives, list):
            for i, obj in enumerate(objectives, 1):
                st.markdown(f"{i}. {obj}")
        else:
            st.write(objectives)

    if data.get('contributions'):
        st.markdown("#### 💎 Contributions")
        contributions = data['contributions']
        if isinstance(contributions, list):
            for i, contrib in enumerate(contributions, 1):
                st.markdown(f"{i}. {contrib}")
        else:
            st.write(contributions)


def display_literature_analysis(data: Dict):
    """Display Literature Review agent analysis"""
    if data.get('key_papers'):
        st.markdown("#### 📚 Key Papers Referenced")
        papers = data['key_papers']
        if isinstance(papers, list):
            for i, paper in enumerate(papers, 1):
                if isinstance(paper, dict):
                    st.markdown(f"{i}. **{paper.get('title', 'Unknown')}** - {paper.get('contribution', '')}")
                else:
                    st.markdown(f"{i}. {paper}")
        else:
            st.write(papers)

    if data.get('research_streams'):
        st.markdown("#### 🌊 Research Streams")
        streams = data['research_streams']
        if isinstance(streams, list):
            for i, stream in enumerate(streams, 1):
                st.markdown(f"{i}. {stream}")
        else:
            st.write(streams)

    if data.get('gaps_identified'):
        st.markdown("#### 🔍 Gaps Identified")
        gaps = data['gaps_identified']
        if isinstance(gaps, list):
            for i, gap in enumerate(gaps, 1):
                st.markdown(f"{i}. {gap}")
        else:
            st.write(gaps)

    if data.get('theoretical_foundations'):
        st.markdown("#### 🏛️ Theoretical Foundations")
        st.write(data['theoretical_foundations'])


def display_methodology_analysis(data: Dict):
    """Display Methodology agent analysis"""
    if data.get('research_design'):
        st.markdown("#### 🏗️ Research Design")
        st.write(data['research_design'])

    if data.get('data_sources'):
        st.markdown("#### 📊 Data Sources")
        sources = data['data_sources']
        if isinstance(sources, list):
            for i, source in enumerate(sources, 1):
                st.markdown(f"{i}. {source}")
        else:
            st.write(sources)

    if data.get('data_collection'):
        st.markdown("#### 📥 Data Collection")
        st.write(data['data_collection'])

    if data.get('sample_size'):
        st.markdown("#### 👥 Sample Size")
        st.write(data['sample_size'])

    if data.get('analysis_techniques'):
        st.markdown("#### 🔧 Analysis Techniques")
        techniques = data['analysis_techniques']
        if isinstance(techniques, list):
            for i, tech in enumerate(techniques, 1):
                st.markdown(f"{i}. {tech}")
        else:
            st.write(techniques)

    if data.get('tools_and_frameworks'):
        st.markdown("#### ⚙️ Tools & Frameworks")
        tools = data['tools_and_frameworks']
        if isinstance(tools, list):
            for i, tool in enumerate(tools, 1):
                st.markdown(f"{i}. {tool}")
        else:
            st.write(tools)

    if data.get('experimental_setup'):
        st.markdown("#### 🧪 Experimental Setup")
        st.write(data['experimental_setup'])

    if data.get('parameters'):
        st.markdown("#### ⚙️ Parameters")
        params = data['parameters']
        if isinstance(params, dict):
            for key, value in params.items():
                st.markdown(f"- **{key}**: {value}")
        else:
            st.write(params)

    if data.get('evaluation_metrics'):
        st.markdown("#### 📈 Evaluation Metrics")
        metrics = data['evaluation_metrics']
        if isinstance(metrics, list):
            for i, metric in enumerate(metrics, 1):
                st.markdown(f"{i}. {metric}")
        else:
            st.write(metrics)

    if data.get('reproducibility'):
        st.markdown("#### 🔄 Reproducibility Assessment")
        repro = data['reproducibility']
        if isinstance(repro, dict):
            score = repro.get('score', 'N/A')
            emoji = "🟢" if score == "high" else "🟡" if score == "medium" else "🔴"
            st.markdown(f"**Score**: {emoji} {score.upper()}")

            if repro.get('details_provided'):
                st.markdown("**Details Provided:**")
                for detail in repro['details_provided']:
                    st.markdown(f"✅ {detail}")

            if repro.get('missing_details'):
                st.markdown("**Missing Details:**")
                for missing in repro['missing_details']:
                    st.markdown(f"❌ {missing}")
        else:
            st.write(repro)

    if data.get('critical_analysis'):
        st.markdown("#### 💭 Critical Analysis")
        st.info(data['critical_analysis'])


def display_results_analysis(data: Dict):
    """Display Results agent analysis"""
    if data.get('main_findings'):
        st.markdown("#### 🎯 Main Findings")
        findings = data['main_findings']
        if isinstance(findings, list):
            for i, finding in enumerate(findings, 1):
                st.markdown(f"{i}. {finding}")
        else:
            st.write(findings)

    if data.get('quantitative_results'):
        st.markdown("#### 📊 Quantitative Results")
        results = data['quantitative_results']
        if isinstance(results, list):
            for i, result in enumerate(results, 1):
                st.markdown(f"{i}. {result}")
        else:
            st.write(results)

    if data.get('qualitative_insights'):
        st.markdown("#### 💭 Qualitative Insights")
        insights = data['qualitative_insights']
        if isinstance(insights, list):
            for i, insight in enumerate(insights, 1):
                st.markdown(f"{i}. {insight}")
        else:
            st.write(insights)

    if data.get('comparisons'):
        st.markdown("#### ⚖️ Comparisons")
        st.write(data['comparisons'])

    if data.get('statistical_significance'):
        st.markdown("#### 📈 Statistical Significance")
        st.write(data['statistical_significance'])

    if data.get('visualizations_mentioned'):
        st.markdown("#### 📊 Visualizations Mentioned")
        viz = data['visualizations_mentioned']
        if isinstance(viz, list):
            for i, v in enumerate(viz, 1):
                st.markdown(f"{i}. {v}")
        else:
            st.write(viz)


def display_discussion_analysis(data: Dict):
    """Display Discussion agent analysis"""
    if data.get('interpretation'):
        st.markdown("#### 🔍 Interpretation of Results")
        st.write(data['interpretation'])

    if data.get('implications'):
        st.markdown("#### 💡 Implications")
        implications = data['implications']
        if isinstance(implications, list):
            for i, impl in enumerate(implications, 1):
                st.markdown(f"{i}. {impl}")
        else:
            st.write(implications)

    if data.get('limitations'):
        st.markdown("#### ⚠️ Limitations")
        limitations = data['limitations']
        if isinstance(limitations, list):
            for i, lim in enumerate(limitations, 1):
                st.markdown(f"{i}. {lim}")
        else:
            st.write(limitations)

    if data.get('comparison_with_literature'):
        st.markdown("#### 📚 Comparison with Literature")
        st.write(data['comparison_with_literature'])

    if data.get('theoretical_contributions'):
        st.markdown("#### 🏛️ Theoretical Contributions")
        st.write(data['theoretical_contributions'])

    if data.get('practical_applications'):
        st.markdown("#### 🛠️ Practical Applications")
        apps = data['practical_applications']
        if isinstance(apps, list):
            for i, app in enumerate(apps, 1):
                st.markdown(f"{i}. {app}")
        else:
            st.write(apps)


def display_conclusion_analysis(data: Dict):
    """Display Conclusion agent analysis"""
    if data.get('main_conclusions'):
        st.markdown("#### 🎯 Main Conclusions")
        conclusions = data['main_conclusions']
        if isinstance(conclusions, list):
            for i, conc in enumerate(conclusions, 1):
                st.markdown(f"{i}. {conc}")
        else:
            st.write(conclusions)

    if data.get('contributions_summary'):
        st.markdown("#### 💎 Contributions Summary")
        st.write(data['contributions_summary'])

    if data.get('future_work'):
        st.markdown("#### 🔮 Future Work")
        future = data['future_work']
        if isinstance(future, list):
            for i, work in enumerate(future, 1):
                st.markdown(f"{i}. {work}")
        else:
            st.write(future)

    if data.get('recommendations'):
        st.markdown("#### 📝 Recommendations")
        recs = data['recommendations']
        if isinstance(recs, list):
            for i, rec in enumerate(recs, 1):
                st.markdown(f"{i}. {rec}")
        else:
            st.write(recs)

    if data.get('impact_statement'):
        st.markdown("#### 💫 Impact Statement")
        st.info(data['impact_statement'])


def display_generic_analysis(data: Dict):
    """Generic display for any agent analysis"""
    for key, value in data.items():
        if key == 'parse_error':
            continue

        # Format the key nicely
        display_key = key.replace('_', ' ').title()

        st.markdown(f"#### {display_key}")

        if isinstance(value, list):
            if value:
                for i, item in enumerate(value, 1):
                    if isinstance(item, dict):
                        st.json(item)
                    else:
                        st.markdown(f"{i}. {item}")
            else:
                st.caption("_No data available_")
        elif isinstance(value, dict):
            if value:
                for sub_key, sub_value in value.items():
                    st.markdown(f"**{sub_key.replace('_', ' ').title()}**: {sub_value}")
            else:
                st.caption("_No data available_")
        elif isinstance(value, str):
            if value:
                st.write(value)
            else:
                st.caption("_No data available_")
        else:
            st.write(value)


def generate_comprehensive_summary_paragraphs(analysis_results: Dict, synthesis: Dict, paper_metadata: Dict = None) -> Dict:
    """
    Generate DETAILED comprehensive topic-based paragraphs from all 7 agents' real analysis data.
    Uses Grok-4 to synthesize comprehensive, flowing narratives (not just concatenated bullet points).

    Args:
        analysis_results: Dictionary containing all agent analysis results
        synthesis: Synthesis results from the synthesis agent
        paper_metadata: Optional paper metadata (title, authors, year)

    Returns:
        Dictionary with detailed topic-based paragraphs (5-8 sentences each)
    """
    import json
    from grok_client import GrokClient

    # Initialize Grok client for paragraph synthesis
    grok = GrokClient(
        api_key=config.GROK_SETTINGS['api_key'],
        model="grok-4-fast-reasoning",
        validate=False
    )

    paragraphs = {}

    # Extract ALL available data from each agent (comprehensive extraction)
    abstract_data = analysis_results.get('abstract', {}).get('analysis', {})
    intro_data = analysis_results.get('introduction', {}).get('analysis', {})
    lit_data = analysis_results.get('literature_review', {}).get('analysis', {})
    method_data = analysis_results.get('methodology', {}).get('analysis', {})
    results_data = analysis_results.get('results', {}).get('analysis', {})
    discussion_data = analysis_results.get('discussion', {}).get('analysis', {})
    conclusion_data = analysis_results.get('conclusion', {}).get('analysis', {})

    # Paper title for context
    paper_title = paper_metadata.get('title', 'the research paper') if paper_metadata else 'the research paper'

    # === PARAGRAPH 1: Introduction & Research Context ===
    intro_context = {
        'paper_title': paper_title,
        'problem_statement': abstract_data.get('problem_statement', ''),
        'research_context': intro_data.get('research_context', ''),
        'research_gap': intro_data.get('research_gap', ''),
        'main_contribution': abstract_data.get('main_contribution', ''),
        'research_objectives': intro_data.get('research_objectives', []),
        'motivation': intro_data.get('motivation', ''),
        'theoretical_foundations': lit_data.get('theoretical_foundations', ''),
        'key_papers_reviewed': lit_data.get('key_papers_reviewed', [])
    }

    intro_prompt = f"""Based on the following research paper analysis data, write a DETAILED, COMPREHENSIVE paragraph (6-8 sentences) about the Introduction & Research Context.

The paragraph should flow naturally and cover:
- The problem being addressed and its importance
- The research context and background
- The identified research gap
- The paper's main contribution
- How it builds on existing work

Analysis Data:
{json.dumps(intro_context, indent=2)}

Write a detailed, flowing paragraph that synthesizes all this information into a comprehensive narrative. Make it detailed and informative, not just bullet points joined together."""

    try:
        paragraphs['introduction'] = grok.generate(
            prompt=intro_prompt,
            max_tokens=500,
            temperature=0.3
        ).strip()
    except Exception as e:
        print(f"Error generating introduction paragraph: {e}")
        paragraphs['introduction'] = "The paper addresses important research questions in its domain, introducing novel contributions to advance the field."

    # === PARAGRAPH 2: Methodology & Approach ===
    method_context = {
        'paper_title': paper_title,
        'research_design': method_data.get('research_design', ''),
        'methodology_summary': abstract_data.get('methodology_summary', ''),
        'data_sources': method_data.get('data_sources', []),
        'data_collection': method_data.get('data_collection', ''),
        'analysis_techniques': method_data.get('analysis_techniques', []),
        'tools_and_frameworks': method_data.get('tools_and_frameworks', []),
        'experimental_setup': method_data.get('experimental_setup', ''),
        'reproducibility': method_data.get('reproducibility', {}),
        'validation_methods': method_data.get('validation_methods', [])
    }

    method_prompt = f"""Based on the following research paper analysis data, write a DETAILED, COMPREHENSIVE paragraph (6-8 sentences) about the Methodology & Approach.

The paragraph should flow naturally and cover:
- The research design and approach
- Data sources and collection methods
- Analysis techniques and tools used
- Experimental setup (if applicable)
- Reproducibility and validation

Analysis Data:
{json.dumps(method_context, indent=2)}

Write a detailed, flowing paragraph that synthesizes all this information into a comprehensive narrative. Make it detailed and technical where appropriate."""

    try:
        paragraphs['methodology'] = grok.generate(
            prompt=method_prompt,
            max_tokens=500,
            temperature=0.3
        ).strip()
    except Exception as e:
        print(f"Error generating methodology paragraph: {e}")
        paragraphs['methodology'] = "The paper employs rigorous research methodologies appropriate for addressing the stated research questions."

    # === PARAGRAPH 3: Results & Key Findings ===
    results_context = {
        'paper_title': paper_title,
        'key_results': abstract_data.get('key_results', []),
        'main_findings': results_data.get('main_findings', []),
        'quantitative_results': results_data.get('quantitative_results', []),
        'qualitative_findings': results_data.get('qualitative_findings', []),
        'statistical_significance': results_data.get('statistical_significance', ''),
        'performance_metrics': results_data.get('performance_metrics', []),
        'comparison_with_baselines': results_data.get('comparison_with_baselines', ''),
        'significance': abstract_data.get('significance', '')
    }

    results_prompt = f"""Based on the following research paper analysis data, write a DETAILED, COMPREHENSIVE paragraph (6-8 sentences) about the Results & Key Findings.

The paragraph should flow naturally and cover:
- The key results and main findings
- Quantitative and qualitative results
- Statistical significance and performance metrics
- How results compare to baselines or previous work
- The significance of the findings

Analysis Data:
{json.dumps(results_context, indent=2)}

Write a detailed, flowing paragraph that synthesizes all this information into a comprehensive narrative. Include specific numbers and metrics where available."""

    try:
        paragraphs['results'] = grok.generate(
            prompt=results_prompt,
            max_tokens=500,
            temperature=0.3
        ).strip()
    except Exception as e:
        print(f"Error generating results paragraph: {e}")
        paragraphs['results'] = "The paper presents comprehensive results that validate the proposed approach and demonstrate its effectiveness."

    # === PARAGRAPH 4: Discussion, Implications & Conclusions ===
    discussion_context = {
        'paper_title': paper_title,
        'interpretation': discussion_data.get('interpretation', ''),
        'implications': discussion_data.get('implications', []),
        'theoretical_implications': discussion_data.get('theoretical_implications', []),
        'practical_implications': discussion_data.get('practical_implications', []),
        'main_conclusions': conclusion_data.get('main_conclusions', []),
        'limitations': discussion_data.get('limitations', []),
        'future_work': conclusion_data.get('future_work', []),
        'impact_statement': conclusion_data.get('impact_statement', ''),
        'recommendations': conclusion_data.get('recommendations', [])
    }

    discussion_prompt = f"""Based on the following research paper analysis data, write a DETAILED, COMPREHENSIVE paragraph (6-8 sentences) about the Discussion, Implications & Conclusions.

The paragraph should flow naturally and cover:
- Interpretation of the results
- Theoretical and practical implications
- Main conclusions drawn by the authors
- Acknowledged limitations
- Future research directions
- Overall impact of the work

Analysis Data:
{json.dumps(discussion_context, indent=2)}

Write a detailed, flowing paragraph that synthesizes all this information into a comprehensive narrative. Be balanced in discussing both strengths and limitations."""

    try:
        paragraphs['discussion'] = grok.generate(
            prompt=discussion_prompt,
            max_tokens=500,
            temperature=0.3
        ).strip()
    except Exception as e:
        print(f"Error generating discussion paragraph: {e}")
        paragraphs['discussion'] = "The discussion contextualizes the findings within existing literature, addresses limitations, and outlines future research directions."

    return paragraphs


def display_paper_card(paper: Dict, rank: int):
    """Display a single paper card"""
    with st.container():
        # Header with title and rank
        col1, col2 = st.columns([0.95, 0.05])

        with col1:
            st.markdown(f"### {rank}. {paper['title']}")

        with col2:
            quality_score = paper.get('quality_score', 0)
            if quality_score >= 0.7:
                badge_class = "quality-high"
                badge_text = "High"
            elif quality_score >= 0.5:
                badge_class = "quality-medium"
                badge_text = "Med"
            else:
                badge_class = "quality-low"
                badge_text = "Low"

            st.markdown(
                f'<span class="quality-badge {badge_class}">{badge_text}</span>',
                unsafe_allow_html=True
            )

        # Authors and year
        authors_str = format_authors(paper.get('authors', []), max_authors=5)
        year = paper.get('year', 'N/A')
        venue = format_venue(paper.get('venue', 'Unknown'))

        st.markdown(f"**Authors:** {authors_str}")
        st.markdown(f"**Year:** {year} | **Venue:** {venue}")

        # Metrics row
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            citations = paper.get('citations', 0) or 0
            st.metric("Citations", f"{citations:,}")

        with col2:
            inf_cit = paper.get('influential_citations', 0) or 0
            st.metric("Influential", inf_cit)

        with col3:
            quality = paper.get('quality_score', 0)
            st.metric("Quality Score", f"{quality:.2f}")

        with col4:
            age = get_paper_age_category(year) if isinstance(year, int) else 'N/A'
            st.metric("Age", age)

        with col5:
            source = paper.get('source', 'Unknown')
            st.metric("Source", source)

        # Multi-Agent Analysis (ALWAYS VISIBLE - Phase 3+4 Primary Features)
        st.markdown("---")
        st.markdown("**🤖 AI-Powered Analysis:**")

        analysis_col1, analysis_col2 = st.columns(2)

        with analysis_col1:
            if st.button("🎯 Analyze Paper (7 Agents)", key=f"analyze_{rank}", use_container_width=True, type="primary"):
                st.session_state[f'show_analysis_{rank}'] = not st.session_state.get(f'show_analysis_{rank}', False)

        with analysis_col2:
            if st.button("💬 Chat with Paper (RAG)", key=f"chat_{rank}", use_container_width=True):
                # Store paper data for chat
                st.session_state.chat_paper_data = paper

                # If analysis is available, generate summary for chat
                if st.session_state.get(f'analysis_result_{rank}'):
                    result = st.session_state[f'analysis_result_{rank}']
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

        # Abstract & Additional Details (expandable for secondary information)
        with st.expander("📄 Abstract & Details", expanded=False):
            abstract = paper.get('abstract', 'No abstract available')
            st.markdown(f"**Abstract:** {truncate_text(abstract, 800)}")

            # Links row
            st.markdown("---")
            link_cols = st.columns(5)

            with link_cols[0]:
                if paper.get('pdf_url'):
                    st.link_button("📖 PDF", paper['pdf_url'], use_container_width=True)

            with link_cols[1]:
                if paper.get('paper_id'):
                    paper_url = f"https://www.semanticscholar.org/paper/{paper['paper_id']}"
                    st.link_button("🔗 Details", paper_url, use_container_width=True)

            with link_cols[2]:
                if paper.get('arxiv_id'):
                    arxiv_url = f"https://arxiv.org/abs/{paper['arxiv_id']}"
                    st.link_button("📝 arXiv", arxiv_url, use_container_width=True)

            with link_cols[3]:
                implementations = paper.get('implementations')
                if implementations and implementations.get('repositories'):
                    repo = implementations['repositories'][0]
                    st.link_button("💻 Code", repo['url'], use_container_width=True)

            with link_cols[4]:
                if st.button("📋 Cite", key=f"cite_{rank}", use_container_width=True):
                    bibtex = generate_bibtex(paper)
                    st.code(bibtex, language='bibtex')

            # Display implementations if available
            implementations = paper.get('implementations')
            if implementations and implementations.get('repositories'):
                st.markdown("---")
                st.markdown("**💻 Implementations:**")
                for repo in implementations['repositories'][:3]:
                    stars = repo.get('stars', 0)
                    is_official = repo.get('is_official', False)
                    official_badge = "✅ Official" if is_official else ""

                    st.markdown(
                        f"- [{repo['owner']}/{repo['name']}]({repo['url']}) "
                        f"⭐ {stars:,} {official_badge}"
                    )

        # Phase 3: Comprehensive Analysis Interface (Uses Grok-4)
        if st.session_state.get(f'show_analysis_{rank}', False):
            st.markdown("---")
            st.markdown("### 🎯 Comprehensive Multi-Agent Analysis")
            st.caption("Deep analysis using 7 specialized agents + synthesis")

            if st.button("▶️ Start Analysis", key=f"start_analysis_{rank}", type="primary"):
                result = analyze_paper_comprehensive(paper, rank)

                if result:
                    # Store analysis in session state
                    st.session_state[f'analysis_result_{rank}'] = result
                    st.rerun()

        # Display comprehensive analysis if available
        if st.session_state.get(f'analysis_result_{rank}'):
            st.markdown("---")
            st.markdown("### 📊 Analysis Results")

            result = st.session_state[f'analysis_result_{rank}']
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
            if st.button("🗑️ Clear Analysis", key=f"clear_analysis_{rank}"):
                del st.session_state[f'analysis_result_{rank}']
                st.rerun()

        # Phase 4: Chat with Paper Interface (Metadata-Based - 2025 Enhancement)
        if st.session_state.get(f'show_chat_{rank}', False):
                st.markdown("---")
                st.markdown("### 💬 Chat with Paper (Instant Metadata-Based Q&A)")
                st.caption("Ask questions about the paper using TLDR + Abstract + Metadata (no PDF processing needed!)")

                # Paper is instantly ready for chat using metadata
                st.success("✅ Paper ready for chat (using TLDR + Abstract + Metadata)")

                # Chat settings
                chat_col1, chat_col2 = st.columns(2)

                with chat_col1:
                    temperature = st.slider("Temperature", 0.0, 1.0, 0.3, key=f"temp_{rank}",
                                           help="Lower = more focused, Higher = more creative")

                with chat_col2:
                    max_tokens = st.slider("Max Response Length", 100, 1000, 500, key=f"max_tokens_{rank}",
                                          help="Maximum length of the answer")

                # Show chat history
                if f'chat_history_{rank}' not in st.session_state:
                    st.session_state[f'chat_history_{rank}'] = []

                if st.session_state[f'chat_history_{rank}']:
                    with st.expander(f"📜 Chat History ({len(st.session_state[f'chat_history_{rank}'])} questions)"):
                        for i, msg in enumerate(reversed(st.session_state[f'chat_history_{rank}'][-5:]), 1):
                            st.markdown(f"**Q{i}:** {msg['question']}")
                            st.markdown(f"**A{i}:** {msg['answer']}")
                            st.caption(f"⏱️ Time: {msg['elapsed_time']:.2f}s")
                            st.markdown("---")

                # Question input
                question = st.text_area(
                    "Ask a question about this paper:",
                    key=f"chat_question_{rank}",
                    placeholder="e.g., What is the main contribution? How does the methodology work? What are the limitations?",
                    height=100
                )

                if st.button("🚀 Ask Question", key=f"submit_chat_{rank}", type="primary"):
                    if question:
                        with st.spinner("Generating answer..."):
                            try:
                                import time
                                from grok_client import GrokClient
                                import config

                                start_time = time.time()

                                # Build context from metadata
                                title = paper.get('title', 'Unknown Title')
                                authors = ', '.join([a.get('name', 'Unknown') for a in paper.get('authors', [])[:5]])
                                year = paper.get('year', 'N/A')
                                venue = paper.get('venue', 'Unknown')
                                citations = paper.get('citations', 0)
                                tldr = paper.get('tldr', None)
                                abstract = paper.get('abstract', 'No abstract available')
                                fields = ', '.join(paper.get('fields_of_study', [])[:5]) or 'Not specified'

                                # Build rich context
                                context_parts = [
                                    f"Title: {title}",
                                    f"Authors: {authors}",
                                    f"Year: {year}",
                                    f"Venue: {venue}",
                                    f"Citations: {citations:,}",
                                    f"Fields of Study: {fields}"
                                ]

                                if tldr:
                                    context_parts.append(f"\nTL;DR (AI-Generated Summary):\n{tldr}")

                                if abstract and abstract != 'No abstract available':
                                    context_parts.append(f"\nAbstract:\n{abstract}")

                                context = '\n'.join(context_parts)

                                # Create prompt for LLM
                                prompt = f"""You are a research assistant helping answer questions about an academic paper.

Paper Information:
{context}

Question: {question}

Instructions:
- Answer the question based ONLY on the information provided above
- Be specific and reference relevant details from the paper
- If the information isn't available in the abstract/summary, clearly state that
- Keep your answer concise but informative (2-4 paragraphs)
- Use academic tone

Answer:"""

                                # Use Grok client to generate answer
                                grok_client = GrokClient(
                                    api_key=config.GROK_SETTINGS['api_key'],
                                    model="grok-4-fast-reasoning",
                                    validate=False  # Skip validation for faster response
                                )

                                answer = grok_client.generate(
                                    prompt=prompt,
                                    max_tokens=max_tokens,
                                    temperature=temperature
                                )

                                elapsed_time = time.time() - start_time

                                # Display answer
                                st.markdown("#### 🤖 Answer:")
                                st.markdown(answer)

                                # Show metadata
                                meta_col1, meta_col2 = st.columns(2)
                                with meta_col1:
                                    st.caption(f"⏱️ Time: {elapsed_time:.2f}s")
                                with meta_col2:
                                    sources = "TLDR + Abstract" if tldr else "Abstract + Metadata"
                                    st.caption(f"📚 Sources: {sources}")

                                # Save to chat history
                                st.session_state[f'chat_history_{rank}'].append({
                                    'question': question,
                                    'answer': answer,
                                    'elapsed_time': elapsed_time
                                })

                            except Exception as e:
                                st.error(f"❌ Error generating answer: {str(e)}")
                                import traceback
                                with st.expander("🔍 Error Details"):
                                    st.code(traceback.format_exc())
                    else:
                        st.warning("Please enter a question")

        st.markdown("---")


def display_blog_post(post: Dict, rank: int):
    """Display a blog post result"""
    st.markdown(f"""
    <div class="blog-post">
        <h4>{rank}. {post['title']}</h4>
        <p><strong>Source:</strong> {post['source']} | <strong>Date:</strong> {post.get('date', 'N/A')}</p>
        <p>{post['snippet']}</p>
        <a href="{post['url']}" target="_blank">Read more →</a>
    </div>
    """, unsafe_allow_html=True)


def display_paginated_results(results: List[Dict], page_size: int = 10, result_type: str = 'papers'):
    """Display paginated results"""
    if not results:
        st.info(f"No {result_type} found. Try adjusting your search query or filters.")
        return

    total_results = len(results)
    total_pages = max(1, (total_results - 1) // page_size + 1)

    # Reset page if it exceeds total pages (fixes pagination error)
    if st.session_state.current_page >= total_pages:
        st.session_state.current_page = total_pages - 1

    # Pagination controls
    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        if st.button('← Previous', disabled=st.session_state.current_page == 0, key=f'prev_{result_type}'):
            st.session_state.current_page -= 1
            st.rerun()

    with col2:
        page = st.number_input(
            f'Page (1-{total_pages})',
            min_value=1,
            max_value=total_pages,
            value=min(st.session_state.current_page + 1, total_pages),  # Ensure value doesn't exceed max
            key=f'page_selector_{result_type}'
        )
        if page - 1 != st.session_state.current_page:
            st.session_state.current_page = page - 1
            st.rerun()

    with col3:
        if st.button('Next →', disabled=st.session_state.current_page >= total_pages - 1, key=f'next_{result_type}'):
            st.session_state.current_page += 1
            st.rerun()

    # Display results info
    start_idx = st.session_state.current_page * page_size
    end_idx = min(start_idx + page_size, total_results)

    st.markdown(f"**Showing {start_idx + 1}-{end_idx} of {total_results} {result_type}**")

    # Display current page results
    for i, item in enumerate(results[start_idx:end_idx], start=start_idx + 1):
        if result_type == 'papers':
            display_paper_card(item, i)
        else:
            display_blog_post(item, i)


# Phase 4 UI Functions
def display_analysis_browser():
    """Display Analysis Browser page with list of analyzed papers"""
    st.markdown("## 📊 Analysis Browser")
    st.markdown("Browse and explore papers with comprehensive multi-agent analysis")

    workflow = load_workflow_manager()

    # Get statistics
    stats = workflow.get_analysis_statistics()

    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Analyses", stats.get('total_analyses', 0))
    with col2:
        st.metric("Avg Time", f"{stats.get('average_time', 0):.1f}s")
    with col3:
        st.metric("Avg Tokens", f"{stats.get('average_tokens', 0):,.0f}")
    with col4:
        st.metric("Avg Cost", f"${stats.get('average_cost', 0):.4f}")

    st.markdown("---")

    # Quality filter
    quality_filter = st.selectbox(
        "Filter by Quality",
        options=["All", "High", "Medium", "Low"],
        index=0
    )

    filter_value = None if quality_filter == "All" else quality_filter.lower()

    # Get analyzed papers
    analyses = workflow.list_analyzed_papers(quality_filter=filter_value, limit=50)

    if not analyses:
        st.info("No analyses found. Process a paper first to see it here!")
        return

    st.markdown(f"### Found {len(analyses)} analyzed papers")

    # Display each analysis
    for analysis in analyses:
        doc = analysis.get('document', {})
        with st.expander(f"📄 {doc.get('title', 'Unknown')[:80]}...", expanded=False):
            # Basic info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Quality:** {analysis.get('quality_rating', 'N/A').title()}")
            with col2:
                st.markdown(f"**Novelty:** {analysis.get('novelty_rating', 'N/A').title()}")
            with col3:
                st.markdown(f"**Time:** {analysis.get('total_time', 0):.1f}s")

            # Executive summary
            exec_summary = analysis.get('executive_summary', '')
            if exec_summary:
                st.markdown("**Executive Summary:**")
                st.info(exec_summary[:300] + "..." if len(exec_summary) > 300 else exec_summary)

            # Action buttons
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button(f"💬 Chat with Paper", key=f"chat_{analysis['id']}"):
                    st.session_state['selected_doc_id'] = analysis['document_id']
                    st.session_state['show_chat'] = True
                    st.rerun()
            with btn_col2:
                if st.button(f"📊 View Full Analysis", key=f"view_{analysis['id']}"):
                    st.session_state['selected_analysis_id'] = analysis['id']
                    st.session_state['show_full_analysis'] = True
                    st.rerun()


def display_document_chat(document_id: int):
    """Display chat interface for a document"""
    workflow = load_workflow_manager()
    db = load_database()

    # Get document info
    document = db.get_document_by_id(document_id)

    if not document:
        st.error("Document not found!")
        return

    st.markdown(f"## 💬 Chat: {document.get('title', 'Unknown')[:60]}...")

    # Back button
    if st.button("← Back to Analysis Browser"):
        st.session_state['show_chat'] = False
        st.rerun()

    st.markdown("---")

    # Context settings
    with st.expander("⚙️ Chat Settings", expanded=False):
        use_analysis = st.checkbox("Use comprehensive analysis", value=True,
                                   help="Include insights from multi-agent analysis")
        use_rag = st.checkbox("Use RAG excerpts", value=True,
                             help="Include relevant text excerpts from the paper")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.3, 0.1,
                               help="Lower = more focused, Higher = more creative")

    # Chat history
    st.markdown("### 📜 Chat History")
    history = workflow.get_chat_history(document_id, limit=10)

    if history:
        for msg in reversed(history[-5:]):  # Show last 5
            with st.container():
                st.markdown(f"**Q:** {msg.get('user_question', '')}")
                st.markdown(f"**A:** {msg.get('assistant_answer', '')}")
                st.caption(f"Sources: {msg.get('sources_used', 'N/A')} | Time: {msg.get('response_time', 0):.2f}s")
                st.markdown("---")
    else:
        st.info("No chat history yet. Ask a question below!")

    # Chat input
    st.markdown("### ❓ Ask a Question")
    question = st.text_input("Your question:", placeholder="What is the main contribution of this paper?")

    if st.button("Send", type="primary", disabled=not question):
        with st.spinner("Generating answer..."):
            result = workflow.chat_with_paper(
                document_id=document_id,
                question=question,
                use_analysis=use_analysis,
                use_rag=use_rag,
                temperature=temperature
            )

            if result['success']:
                st.success("Answer generated!")
                st.markdown(f"**Q:** {result['question']}")
                st.markdown(f"**A:** {result['answer']}")
                st.caption(f"Sources: {', '.join(result.get('sources_used', []))} | "
                          f"Time: {result.get('elapsed_time', 0):.2f}s | "
                          f"Tokens: {result.get('tokens_used', 0):,}")
                st.rerun()
            else:
                st.error(f"Failed: {result.get('message', 'Unknown error')}")


def display_stored_analysis(analysis_id: int):
    """Display full stored analysis"""
    db = load_database()

    # Get analysis
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM document_analyses WHERE id = ?", (analysis_id,))
    row = cursor.fetchone()

    if not row:
        st.error("Analysis not found!")
        return

    analysis = dict(row)

    # Get document info
    document = db.get_document_by_id(analysis['document_id'])

    st.markdown(f"## 📊 Full Analysis: {document.get('title', 'Unknown')[:60]}...")

    # Back button
    if st.button("← Back to Analysis Browser"):
        st.session_state['show_full_analysis'] = False
        st.rerun()

    st.markdown("---")

    # Import json to parse stored data
    import json
    synthesis = json.loads(analysis['synthesis_result'])

    # Overall Assessment
    st.markdown("### 🎯 Overall Assessment")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        quality = analysis.get('quality_rating', 'N/A').title()
        emoji = "🟢" if quality == "High" else "🟡" if quality == "Medium" else "🔴"
        st.metric(f"{emoji} Quality", quality)
    with col2:
        novelty = analysis.get('novelty_rating', 'N/A').title()
        emoji = "🟢" if novelty == "High" else "🟡" if novelty == "Medium" else "🔴"
        st.metric(f"{emoji} Novelty", novelty)
    with col3:
        impact = analysis.get('impact_rating', 'N/A').title()
        emoji = "🟢" if impact == "High" else "🟡" if impact == "Medium" else "🔴"
        st.metric(f"{emoji} Impact", impact)
    with col4:
        rigor = analysis.get('rigor_rating', 'N/A').title()
        emoji = "🟢" if rigor == "High" else "🟡" if rigor == "Medium" else "🔴"
        st.metric(f"{emoji} Rigor", rigor)

    st.markdown("---")

    # Executive Summary
    st.markdown("### 📝 Executive Summary")
    exec_summary = synthesis.get('executive_summary', 'N/A')
    st.info(exec_summary)

    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["💪 Strengths", "⚠️ Limitations", "🔮 Future Work", "💡 Key Takeaways"])

    with tab1:
        strengths = synthesis.get('strengths', [])
        if strengths:
            for i, strength in enumerate(strengths, 1):
                st.markdown(f"{i}. {strength}")
        else:
            st.info("No strengths listed")

    with tab2:
        limitations = synthesis.get('limitations', [])
        if limitations:
            for i, limitation in enumerate(limitations, 1):
                st.markdown(f"{i}. {limitation}")
        else:
            st.info("No limitations listed")

    with tab3:
        future_dirs = synthesis.get('future_directions', [])
        if future_dirs:
            for i, direction in enumerate(future_dirs, 1):
                st.markdown(f"{i}. {direction}")
        else:
            st.info("No future directions listed")

    with tab4:
        takeaways = synthesis.get('key_takeaways', [])
        if takeaways:
            for i, takeaway in enumerate(takeaways, 1):
                st.markdown(f"{i}. {takeaway}")
        else:
            st.info("No key takeaways listed")

    # Key Contributions
    st.markdown("### 🎯 Key Contributions")
    contributions = synthesis.get('key_contributions', [])
    if contributions:
        for i, contrib in enumerate(contributions, 1):
            st.markdown(f"{i}. {contrib}")
    else:
        st.info("No contributions listed")

    # Metrics
    st.markdown("### 📈 Analysis Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Time", f"{analysis.get('total_time', 0):.1f}s")
    with col2:
        st.metric("Total Tokens", f"{analysis.get('total_tokens', 0):,}")
    with col3:
        st.metric("Estimated Cost", f"${analysis.get('estimated_cost', 0):.4f}")


# Main UI
def main():
    # Header
    st.markdown('<h1 class="main-header">📚 Research Paper Discovery System</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Discover high-quality research papers and blog posts in LLMs, AI Agents, Quantum Computing & more</p>',
        unsafe_allow_html=True
    )

    # New Feature Banner
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("🆕 **NEW:** Upload and analyze your own research papers with 11 AI agents! Get comprehensive insights with real-time progress tracking.")
    with col2:
        if st.button("📑 Try Document Analysis", type="primary", use_container_width=True):
            st.switch_page("pages/Document_Analysis.py")

    st.markdown("---")

    # Sidebar Filters
    with st.sidebar:
        # Navigation
        st.header("📑 Navigation")
        page = st.radio(
            "Select View",
            options=["🔍 Paper Search", "📊 Analysis Browser"],
            index=0,
            help="Switch between paper search and analysis management"
        )
        st.markdown("---")

        st.header("🔍 Search Settings")

        # Search sources - ALL 6 SOURCES with comprehensive orchestration
        st.subheader("Data Sources (Multi-Agent System)")
        st.caption("Select sources - orchestrator coordinates all agents in parallel")

        use_semantic_scholar = st.checkbox("📚 Semantic Scholar (200M+ papers)", value=True,
                                          help="Rich metadata, citations, h-index")
        use_arxiv = st.checkbox("📄 arXiv (CS/Physics preprints)", value=True,
                               help="Latest preprints in Computer Science, AI, Physics, Math")
        use_openalex = st.checkbox("🌐 OpenAlex (240M+ papers)", value=True,
                                   help="Largest coverage, completely free, comprehensive")
        use_crossref = st.checkbox("🔗 Crossref (150M+ DOIs)", value=True,
                                  help="DOI metadata, journal articles, conference papers")
        use_core = st.checkbox("📖 CORE (Open Access)", value=True,
                              help="Open access focus, full-text available")
        use_pubmed = st.checkbox("🧬 PubMed (35M+ biomedical)", value=True,
                                help="Biomedical and life sciences research")

        sources = []
        if use_semantic_scholar:
            sources.append('semantic_scholar')
        if use_arxiv:
            sources.append('arxiv')
        if use_openalex:
            sources.append('openalex')
        if use_crossref:
            sources.append('crossref')
        if use_core:
            sources.append('core')
        if use_pubmed:
            sources.append('pubmed')

        st.session_state.search_sources = sources

        # Show selected sources count
        st.info(f"✅ {len(sources)} of 6 sources active")

        st.markdown("---")

        # LLM Settings
        if config.LLM_SETTINGS['enabled']:
            st.header("🤖 AI Assistant")

            llm_enabled = st.checkbox(
                "Enable AI Features",
                value=st.session_state.get('llm_enabled', True),
                help="Enable AI-powered summarization, insights, and Q&A"
            )
            st.session_state.llm_enabled = llm_enabled

            if llm_enabled:
                selected_model = st.selectbox(
                    "Select Model",
                    options=config.LLM_SETTINGS['available_models'],
                    index=config.LLM_SETTINGS['available_models'].index(
                        st.session_state.get('selected_model', config.LLM_SETTINGS['default_model'])
                    ),
                    help="Choose which local LLM to use"
                )
                st.session_state.selected_model = selected_model

                # Model info
                if 'deepseek' in selected_model.lower():
                    st.caption("💡 DeepSeek-R1: Best for research analysis")
                elif 'gpt-oss' in selected_model.lower():
                    st.caption("💡 GPT-OSS 20B: Most capable, slower")
                elif 'llama3.1' in selected_model.lower():
                    st.caption("💡 Llama 3.1: Fast and balanced")

                st.markdown("---")

                # Automatic query enhancement toggle
                auto_enhance = st.checkbox(
                    "Auto-enhance queries",
                    value=st.session_state.get('auto_enhance_query', True),
                    help="Automatically expand your search with AI-suggested keywords for better semantic search"
                )
                st.session_state.auto_enhance_query = auto_enhance

                if auto_enhance:
                    # Grok option for query enhancement
                    if config.GROK_SETTINGS.get('enabled', False):
                        use_grok = st.checkbox(
                            "⚡ Use Grok-4 for enhancement",
                            value=st.session_state.get('use_grok_for_enhancement', True),
                            help="Use Grok-4 API for faster and more efficient query enhancement"
                        )
                        st.session_state.use_grok_for_enhancement = use_grok

                        if use_grok:
                            st.caption("🚀 Using Grok-4 for ultra-fast query enhancement")
                        else:
                            st.caption("✨ Using local LLM for query enhancement")
                    else:
                        st.caption("✨ Your queries will be automatically enhanced with related technical terms")

        st.markdown("---")

        # Filters
        st.header("📊 Filters")

        st.subheader("Citations")
        min_citations = st.number_input(
            "Minimum citations",
            min_value=0,
            value=st.session_state.filters['min_citations'],
            step=5,
            help="Filter papers by minimum citation count"
        )

        st.subheader("Publication Date")
        year_range = st.slider(
            "Year range",
            2000,
            datetime.now().year,
            st.session_state.filters['year_range'],
            help="Filter papers by publication year"
        )

        st.subheader("Venue Type")
        venues = st.multiselect(
            "Select venues",
            ['NeurIPS', 'ICML', 'ICLR', 'ACL', 'EMNLP', 'CVPR', 'ICCV',
             'AAAI', 'IJCAI', 'arXiv', 'Nature', 'Science'],
            default=st.session_state.filters.get('venues', []),
            help="Filter by specific conferences or journals"
        )

        st.subheader("Research Domain")
        domains = st.multiselect(
            "Select domains",
            list(config.DOMAIN_KEYWORDS.keys()),
            default=st.session_state.filters.get('domains', []),
            help="Filter by research area"
        )

        st.subheader("Quality Threshold")
        min_quality = st.slider(
            "Minimum quality score",
            0.0,
            1.0,
            st.session_state.filters.get('min_quality', 0.3),
            0.05,
            help="Filter papers by quality score"
        )

        # Update filters
        st.session_state.filters = {
            'min_citations': min_citations,
            'year_range': year_range,
            'venues': venues,
            'domains': domains,
            'min_quality': min_quality
        }

        st.markdown("---")

        # Blog posts toggle
        st.subheader("Content Types")
        st.session_state.show_blogs = st.checkbox("Show blog posts", value=True)

        st.markdown("---")

        if st.button("🔄 Reset All Filters", use_container_width=True):
            st.session_state.filters = {
                'min_citations': 0,
                'year_range': (2020, datetime.now().year),
                'venues': [],
                'domains': [],
                'min_quality': 0.3
            }
            st.session_state.current_page = 0
            st.rerun()

    # Route based on selected page
    if page == "📊 Analysis Browser":
        # Check for sub-views (chat or full analysis)
        if st.session_state.get('show_chat', False):
            display_document_chat(st.session_state['selected_doc_id'])
        elif st.session_state.get('show_full_analysis', False):
            display_stored_analysis(st.session_state['selected_analysis_id'])
        else:
            display_analysis_browser()
    else:
        # Main Search Interface (existing functionality)
        search_query = st.text_area(
        "🔎 Search for research papers:",
        value=st.session_state.search_query,
        height=100,
        placeholder='Enter keywords like "chain of thought reasoning", "quantum neural networks", or "autonomous AI agents"',
        help="Enter your research topic or keywords. Use specific terms for better results."
    )

    # Query suggestions (LLM-powered)
    if st.session_state.get('llm_enabled', False) and search_query and len(search_query) > 10:
        if st.button("💡 Suggest Better Queries", key="suggest_queries_btn"):
            with st.spinner("Generating query suggestions..."):
                llm_client = get_llm_client(st.session_state.get('selected_model'))
                suggestions = cached_suggest_queries(llm_client, search_query)

                if suggestions:
                    st.markdown("**🎯 Suggested queries:**")
                    for i, suggestion in enumerate(suggestions, 1):
                        if st.button(f"{i}. {suggestion}", key=f"suggestion_{i}", use_container_width=True):
                            st.session_state.search_query = suggestion
                            st.rerun()

    col1, col2, col3 = st.columns([1, 1, 3])

    with col1:
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)

    with col2:
        max_results = st.selectbox("Max results", [20, 50, 100], index=1)

    # Perform search
    if search_button and search_query:
        st.session_state.search_query = search_query
        st.session_state.last_query = search_query
        st.session_state.current_page = 0

        # Check if sources are selected
        if not st.session_state.search_sources:
            st.error("Please select at least one data source from the sidebar!")
            return

        # Automatic query enhancement with LLM or Grok
        enhanced_query = search_query
        if st.session_state.get('llm_enabled', False) and st.session_state.get('auto_enhance_query', True):
            use_grok = st.session_state.get('use_grok_for_enhancement', False)

            with st.spinner("🚀 Enhancing your query with Grok-4..."):
                try:
                    # Always use Grok-4 for query enhancement (Ollama removed)
                    grok_client = get_grok_client(
                        config.GROK_SETTINGS['api_key'],
                        config.GROK_SETTINGS['model']
                    )

                    if grok_client is None:
                        # Grok validation failed - skip enhancement
                        st.warning("⚠️ Grok API unavailable, continuing without query enhancement")
                        enhanced_query = search_query
                    else:
                        keywords = cached_grok_expand_keywords(grok_client, search_query)
                        enhancement_source = "Grok-4 Fast Reasoning"

                    if keywords:
                        # Combine original query with top 3-5 keywords
                        additional_terms = ' '.join(keywords[:3])
                        enhanced_query = f"{search_query} {additional_terms}"
                        st.info(f"🎯 Enhanced with {enhancement_source}: {additional_terms}")
                except Exception as e:
                    st.warning(f"Could not enhance query, using original. ({str(e)[:50]})")
                    enhanced_query = search_query

        with st.spinner("🔍 Searching across academic databases..."):
            # Search papers with enhanced query
            raw_results = search_papers(
                enhanced_query,
                st.session_state.search_sources,
                max_results=max_results
            )

            # Apply filters
            filtered_results = PaperFilter.apply_filters(
                raw_results,
                min_year=st.session_state.filters['year_range'][0],
                max_year=st.session_state.filters['year_range'][1],
                min_citations=st.session_state.filters['min_citations'],
                venues=st.session_state.filters['venues'],
                domains=st.session_state.filters['domains']
            )

            # Score and rank
            scorer = load_scorer()
            ranked_results = scorer.rank_papers(filtered_results)

            # Filter by quality
            quality_filtered = scorer.filter_by_quality(
                ranked_results,
                min_score=st.session_state.filters['min_quality']
            )

            st.session_state.search_results = quality_filtered

            # Search blogs if enabled
            if st.session_state.show_blogs:
                blog_results = search_blogs(search_query, max_results=10)
                st.session_state.blog_results = blog_results

        st.success(f"✅ Found {len(st.session_state.search_results)} papers" +
                   (f" and {len(st.session_state.blog_results)} blog posts" if st.session_state.show_blogs else ""))

    # Display Results
    if st.session_state.search_results or st.session_state.blog_results:
        # Tabs for papers and blogs
        if st.session_state.show_blogs and st.session_state.blog_results:
            tab1, tab2 = st.tabs([
                f"📄 Papers ({len(st.session_state.search_results)})",
                f"📝 Blog Posts ({len(st.session_state.blog_results)})"
            ])

            with tab1:
                display_paginated_results(
                    st.session_state.search_results,
                    page_size=config.RESULTS_PER_PAGE,
                    result_type='papers'
                )

            with tab2:
                display_paginated_results(
                    st.session_state.blog_results,
                    page_size=10,
                    result_type='blog posts'
                )
        else:
            st.subheader(f"📄 Research Papers ({len(st.session_state.search_results)})")
            display_paginated_results(
                st.session_state.search_results,
                page_size=config.RESULTS_PER_PAGE,
                result_type='papers'
            )

    else:
        # Show example queries and recommended papers
        st.markdown("---")
        st.subheader("💡 Example Searches")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            **LLMs & NLP:**
            - Chain of thought reasoning
            - In-context learning
            - Instruction tuning
            - RLHF
            """)

        with col2:
            st.markdown("""
            **AI Agents:**
            - ReAct agent architecture
            - Multi-agent systems
            - Tool use in LLMs
            - Agent planning
            """)

        with col3:
            st.markdown("""
            **Quantum Computing:**
            - Quantum neural networks
            - NISQ algorithms
            - Quantum machine learning
            - Variational quantum
            """)

        st.markdown("---")

        st.subheader("📚 Recommended Foundational Papers")

        recommended = [
            {
                'title': 'Attention Is All You Need',
                'authors': [{'name': 'Vaswani et al.'}],
                'year': 2017,
                'citations': 100000,
                'venue': 'NeurIPS',
                'abstract': 'Introduced the transformer architecture with self-attention mechanisms...',
                'pdf_url': 'https://arxiv.org/pdf/1706.03762.pdf',
                'quality_score': 1.0,
                'source': 'Recommendation'
            }
        ]

        for i, paper in enumerate(recommended, 1):
            display_paper_card(paper, i)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p>Data sources: Semantic Scholar • arXiv • Papers With Code</p>
        <p>Built with Streamlit | Quality scoring based on citations, authors, venues, and recency</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
