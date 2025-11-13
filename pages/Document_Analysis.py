"""
Document Analysis - Upload and analyze research papers with AI
Real-time 11-agent analysis with progress tracking
"""

# Fix for PyTorch + Streamlit file watcher issue
# This prevents the "Examining the path of torch.classes" error
try:
    import torch
    torch.classes.__path__ = []
except (ImportError, AttributeError):
    pass  # torch not installed or already patched

import streamlit as st

# Page Configuration - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Document Analysis",
    page_icon="📑",
    layout="wide"
)

import sys
sys.path.append('..')

from pathlib import Path
import time
import json
from datetime import datetime
from typing import Dict, Optional
import tempfile
import os

from grok_client import GrokClient
import config
from rag_system.document_processor import DocumentProcessor
from rag_system.analysis_agents import DocumentAnalysisOrchestrator
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import io


def format_analysis_to_document(analysis_result: Dict, document_info: Dict) -> str:
    """
    Convert multi-agent analysis results into a comprehensive, detailed document with flowing paragraphs

    Args:
        analysis_result: The complete analysis result from orchestrator
        document_info: Document metadata

    Returns:
        Formatted document with detailed multi-paragraph content
    """
    document = []
    agent_results = analysis_result.get('analysis_results', {})

    # Header
    document.append(f"COMPREHENSIVE ANALYSIS REPORT")
    document.append(f"\n{document_info.get('name', 'Research Paper')}")
    document.append(f"\nAnalysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    document.append(f"Document Size: {document_info.get('size', 0):.2f} MB")
    document.append(f"Format: {document_info.get('format', 'PDF').lstrip('.').upper()}")
    document.append("\n" + "="*80 + "\n")

    # EXECUTIVE SUMMARY - Detailed narrative
    if 'overview' in agent_results and agent_results['overview'].get('success'):
        overview = agent_results['overview'].get('analysis', {})
        document.append("\nEXECUTIVE SUMMARY\n" + "="*80)

        # Multi-paragraph executive summary
        if overview.get('executive_summary'):
            document.append(f"\n{overview['executive_summary']}")

        if overview.get('key_contributions'):
            document.append("\n\nThis research makes several significant contributions to the field. " +
                          " ".join([f"{contrib}." for contrib in overview['key_contributions'][:3]]))

        if overview.get('significance'):
            document.append(f"\n\n{overview.get('significance')}")

        if overview.get('target_audience'):
            document.append(f"\n\nThe primary audience for this work includes {', '.join(overview.get('target_audience', []))}.")

    # RESEARCH PROBLEM & CONTEXT - Detailed narrative
    if 'introduction' in agent_results and agent_results['introduction'].get('success'):
        intro = agent_results['introduction'].get('analysis', {})
        document.append("\n\n\nRESEARCH PROBLEM & CONTEXT\n" + "="*80)

        if intro.get('research_problem'):
            document.append(f"\n\nThe central research problem addressed in this paper is: {intro['research_problem']}")

        if intro.get('motivation'):
            document.append(f"\n\nMotivation: {intro.get('motivation')}")

        if intro.get('background_context'):
            document.append(f"\n\nBackground Context: {intro.get('background_context')}")

        if intro.get('objectives'):
            document.append("\n\nThe research pursues the following objectives: " +
                          " ".join([f"({i+1}) {obj}." for i, obj in enumerate(intro['objectives'])]))

        if intro.get('research_questions'):
            document.append("\n\nKey research questions guiding this investigation include: " +
                          " ".join([f"{q}?" for q in intro.get('research_questions', [])]))

        if intro.get('hypotheses'):
            document.append("\n\nThe authors hypothesize that: " +
                          " ".join([f"{h}." for h in intro.get('hypotheses', [])]))

    # METHODOLOGY - Comprehensive description
    if 'methodology' in agent_results and agent_results['methodology'].get('success'):
        method = agent_results['methodology'].get('analysis', {})
        document.append("\n\n\nMETHODOLOGY\n" + "="*80)

        # Research design paragraph
        if method.get('research_design'):
            document.append(f"\n\nResearch Design: {method['research_design']}")

        if method.get('approach'):
            document.append(f" The methodological approach employed is {method.get('approach', 'systematic and rigorous')}.")

        # Data collection paragraph
        if method.get('data_collection'):
            document.append(f"\n\nData Collection: {method['data_collection']}")

        if method.get('data_sources'):
            document.append(f" Data was gathered from the following sources: {', '.join(method.get('data_sources', []))}.")

        if method.get('sample_size'):
            document.append(f" The study utilized a sample size of {method.get('sample_size')}.")

        # Analysis techniques paragraph
        if method.get('analysis_techniques'):
            document.append("\n\nAnalytical Framework: The research employs several sophisticated analysis techniques. " +
                          " ".join([f"{tech}." for tech in method['analysis_techniques']]))

        if method.get('tools_used'):
            document.append(f" The computational tools and software utilized include: {', '.join(method.get('tools_used', []))}.")

        if method.get('validation_methods'):
            document.append(f"\n\nValidation: {method.get('validation_methods')}")

    # RESULTS & FINDINGS - Detailed analysis
    if 'results' in agent_results and agent_results['results'].get('success'):
        results = agent_results['results'].get('analysis', {})
        document.append("\n\n\nRESULTS & FINDINGS\n" + "="*80)

        if results.get('main_findings'):
            document.append("\n\nMain Findings: The research yields several key findings. " +
                          " ".join([f"First, {finding}." if i == 0 else f"Additionally, {finding}."
                                   for i, finding in enumerate(results['main_findings'])]))

        if results.get('statistical_significance'):
            document.append(f"\n\nStatistical Significance: {results['statistical_significance']}")

        if results.get('effect_size'):
            document.append(f" The observed effect size is {results.get('effect_size')}, indicating substantial practical significance.")

        if results.get('patterns_identified'):
            document.append("\n\nKey Patterns: The analysis reveals several important patterns: " +
                          " ".join([f"{p}." for p in results.get('patterns_identified', [])]))

        if results.get('unexpected_findings'):
            document.append("\n\nUnexpected Discoveries: Interestingly, the research uncovered unexpected findings: " +
                          " ".join([f"{uf}." for uf in results.get('unexpected_findings', [])]))

    # DISCUSSION & INTERPRETATION - In-depth analysis
    if 'discussion' in agent_results and agent_results['discussion'].get('success'):
        discuss = agent_results['discussion'].get('analysis', {})
        document.append("\n\n\nDISCUSSION & INTERPRETATION\n" + "="*80)

        if discuss.get('results_interpretation'):
            document.append(f"\n\n{discuss['results_interpretation']}")

        # Theoretical implications
        if discuss.get('theoretical_implications'):
            document.append("\n\nTheoretical Implications: The findings have significant implications for theory. " +
                          " ".join([f"{impl}." for impl in discuss['theoretical_implications']]))

        # Practical implications
        if discuss.get('practical_implications'):
            document.append("\n\nPractical Implications: From a practical standpoint, these results suggest several actionable insights. " +
                          " ".join([f"{impl}." for impl in discuss['practical_implications']]))

        if discuss.get('comparison_with_literature'):
            document.append(f"\n\nComparison with Existing Literature: {discuss.get('comparison_with_literature')}")

        if discuss.get('alternative_explanations'):
            document.append(f"\n\nAlternative Explanations: {discuss.get('alternative_explanations')}")

    # LITERATURE CONTEXT - Comprehensive review
    if 'literature_review' in agent_results and agent_results['literature_review'].get('success'):
        lit = agent_results['literature_review'].get('analysis', {})
        document.append("\n\n\nLITERATURE CONTEXT\n" + "="*80)

        if lit.get('key_citations'):
            document.append("\n\nKey Citations: This research builds upon foundational work in the field. " +
                          " ".join([f"{citation}." for citation in lit['key_citations'][:8]]))

        if lit.get('research_gaps'):
            document.append("\n\nResearch Gaps Addressed: The study specifically addresses several gaps in the existing literature. " +
                          " ".join([f"{gap}." for gap in lit['research_gaps']]))

        if lit.get('theoretical_frameworks'):
            document.append(f"\n\nTheoretical Framework: The research is grounded in established theoretical frameworks including {', '.join(lit.get('theoretical_frameworks', []))}.")

        if lit.get('evolution_of_field'):
            document.append(f"\n\n{lit.get('evolution_of_field')}")

    # MATHEMATICAL & TECHNICAL DETAILS
    if 'mathematics' in agent_results and agent_results['mathematics'].get('success'):
        math_analysis = agent_results['mathematics'].get('analysis', {})
        document.append("\n\n\nMATHEMATICAL & TECHNICAL FRAMEWORK\n" + "="*80)

        if math_analysis.get('key_equations'):
            document.append("\n\nKey Equations: The mathematical foundation of this work relies on several important equations and formulas. " +
                          " ".join([f"{eq}." for eq in math_analysis.get('key_equations', [])[:5]]))

        if math_analysis.get('algorithms'):
            document.append("\n\nAlgorithmic Approaches: " +
                          " ".join([f"{algo}." for algo in math_analysis.get('algorithms', [])]))

        if math_analysis.get('complexity_analysis'):
            document.append(f"\n\nComplexity Analysis: {math_analysis.get('complexity_analysis')}")

    # FIGURES & VISUALIZATIONS
    if 'figures' in agent_results and agent_results['figures'].get('success'):
        fig_analysis = agent_results['figures'].get('analysis', {})
        if fig_analysis.get('figure_summaries'):
            document.append("\n\n\nVISUAL ELEMENTS & FIGURES\n" + "="*80)
            document.append("\n\nThe paper includes several key visualizations that support the findings: " +
                          " ".join([f"{fig}." for fig in fig_analysis.get('figure_summaries', [])[:5]]))

    # TABLES & DATA
    if 'tables' in agent_results and agent_results['tables'].get('success'):
        table_analysis = agent_results['tables'].get('analysis', {})
        if table_analysis.get('table_summaries'):
            document.append("\n\n\nTABULAR DATA\n" + "="*80)
            document.append("\n\nThe research presents data in structured tabular format: " +
                          " ".join([f"{tbl}." for tbl in table_analysis.get('table_summaries', [])[:5]]))

    # CRITICAL EVALUATION - Strengths and limitations
    if 'conclusion' in agent_results and agent_results['conclusion'].get('success'):
        concl = agent_results['conclusion'].get('analysis', {})
        document.append("\n\n\nCRITICAL EVALUATION\n" + "="*80)

        # Strengths
        if concl.get('strengths'):
            document.append("\n\nStrengths: This research demonstrates several notable strengths. " +
                          " ".join([f"{strength}." for strength in concl['strengths']]))

        # Limitations
        if concl.get('limitations'):
            document.append("\n\nLimitations: Like all research, this study has certain limitations that should be acknowledged. " +
                          " ".join([f"{limit}." for limit in concl['limitations']]))

        # Future directions
        if concl.get('future_work'):
            document.append("\n\nFuture Research Directions: Building on these findings, several promising avenues for future investigation emerge. " +
                          " ".join([f"{future}." for future in concl['future_work']]))

        if concl.get('final_verdict'):
            document.append(f"\n\nConclusion: {concl.get('final_verdict')}")

    # QUALITY ASSESSMENT & METRICS
    metrics = analysis_result.get('metrics', {})
    document.append("\n\n\nQUALITY ASSESSMENT\n" + "="*80)

    document.append(f"\n\nAnalysis Completion: This comprehensive analysis was performed by {metrics.get('successful_agents', 0)} out of {metrics.get('total_agents', 11)} specialized AI agents, " +
                   f"completing in {metrics.get('total_time', 0):.2f} seconds.")

    if metrics.get('context_findings'):
        context = metrics['context_findings']
        document.append(f" The system identified {context.get('total_findings', 0)} cross-referenced contextual connections across different sections of the document, " +
                       "ensuring comprehensive and coherent analysis.")

    document.append("\n\nEach specialized agent (Abstract Analyzer, Introduction Analyzer, Methodology Analyzer, Results Analyzer, " +
                   "Discussion Analyzer, Conclusion Analyzer, Literature Review Analyzer, References Analyzer, Tables Analyzer, " +
                   "Figures Analyzer, and Mathematics Analyzer) contributed domain-specific insights, providing a holistic understanding " +
                   "of the research paper from multiple analytical perspectives.")

    # Footer
    document.append("\n\n" + "="*80)
    document.append("\nReport generated by Research Paper Discovery System")
    document.append("Multi-Agent Analysis Framework")
    document.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return "\n".join(document)


def generate_pdf_report(formatted_content: str, document_name: str) -> bytes:
    """
    Generate a professional PDF report from formatted analysis content

    Args:
        formatted_content: Formatted text content with sections
        document_name: Name of the analyzed document

    Returns:
        PDF file as bytes
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Add first page
    pdf.add_page()

    # Set up fonts (use Helvetica instead of Arial to avoid substitution warning)
    pdf.set_font('Helvetica', 'B', 20)

    # Title page
    pdf.cell(0, 20, 'COMPREHENSIVE ANALYSIS REPORT', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(10)

    # Document name - handle encoding
    pdf.set_font('Helvetica', 'B', 14)
    safe_doc_name = document_name.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, safe_doc_name, align='C')
    pdf.ln(5)

    # Date
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(10)

    # System info
    pdf.set_font('Helvetica', 'I', 9)
    pdf.multi_cell(0, 5, 'Report generated by Research Paper Discovery System\nMulti-Agent Analysis Framework', align='C')

    # Add new page for content
    pdf.add_page()

    # Process content line by line with better error handling
    lines = formatted_content.split('\n')

    for line in lines:
        try:
            # Skip completely empty lines
            if not line or not line.strip():
                pdf.ln(3)
                continue

            # Skip separator lines (=== lines)
            if line.strip().startswith('='):
                pdf.ln(2)
                continue

            # Check if line is a section header (all uppercase)
            if line.strip() and line.strip().isupper() and not line.strip().startswith('**'):
                # Section header
                pdf.set_font('Helvetica', 'B', 13)
                pdf.set_text_color(0, 51, 102)  # Dark blue
                safe_header = line.strip().encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 8, safe_header, align='L')
                pdf.set_text_color(0, 0, 0)  # Reset to black
                pdf.ln(3)
                continue

            # Regular content
            pdf.set_font('Helvetica', '', 11)

            # Clean and encode the line
            cleaned_line = line.strip()
            if not cleaned_line:
                continue

            # Handle encoding
            try:
                safe_line = cleaned_line.encode('latin-1', 'replace').decode('latin-1')
            except Exception:
                safe_line = cleaned_line.encode('ascii', 'ignore').decode('ascii')

            # Add the line
            if safe_line:
                pdf.multi_cell(0, 6, safe_line)

        except Exception as e:
            # Skip problematic lines but continue processing
            print(f"Warning: Skipped line due to error: {e}")
            continue

    # Get PDF as bytes
    try:
        pdf_bytes = pdf.output()

        # Return as bytes (fpdf2 returns bytes or bytearray)
        if isinstance(pdf_bytes, (bytes, bytearray)):
            return bytes(pdf_bytes)
        else:
            # Fallback for string (older versions)
            return pdf_bytes.encode('latin-1')
    except Exception as e:
        # If PDF generation fails completely, raise with context
        raise Exception(f"Failed to generate PDF: {e}")


from rag_system.database import RAGDatabase

# Custom CSS for modern UI
st.markdown("""
<style>
    /* Upload area styling */
    .upload-area {
        border: 2px dashed #2b5278;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        background-color: #f8f9fa;
        margin: 20px 0;
    }

    /* Agent status card */
    .agent-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
        border-left: 4px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }

    .agent-card.pending {
        border-left-color: #9e9e9e;
        opacity: 0.7;
    }

    .agent-card.running {
        border-left-color: #2196F3;
        animation: pulse 2s infinite;
    }

    .agent-card.completed {
        border-left-color: #4CAF50;
    }

    .agent-card.failed {
        border-left-color: #f44336;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }

    /* Progress bar styling */
    .progress-container {
        background-color: #f0f0f0;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
    }

    /* Result card */
    .result-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 20px;
        margin: 16px 0;
        border-left: 4px solid #2b5278;
    }

    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-left: 8px;
    }

    .status-pending {
        background-color: #e0e0e0;
        color: #666;
    }

    .status-running {
        background-color: #2196F3;
        color: white;
    }

    .status-completed {
        background-color: #4CAF50;
        color: white;
    }

    .status-failed {
        background-color: #f44336;
        color: white;
    }

    /* Metrics */
    .metric-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #2b5278;
    }

    .metric-label {
        font-size: 0.9rem;
        color: #666;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with state machine
if 'analysis_phase' not in st.session_state:
    st.session_state.analysis_phase = 'upload'  # States: upload | analyzing | complete

if 'upload_key' not in st.session_state:
    st.session_state.upload_key = 0  # For widget key rotation

if 'last_file_id' not in st.session_state:
    st.session_state.last_file_id = None  # Track unique file uploads

if 'completed_analyses' not in st.session_state:
    st.session_state.completed_analyses = []  # Persistent results storage

if 'current_analysis_idx' not in st.session_state:
    st.session_state.current_analysis_idx = None

if 'analysis_status' not in st.session_state:
    st.session_state.analysis_status = None

if 'agent_statuses' not in st.session_state:
    st.session_state.agent_statuses = {}

if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

if 'uploaded_file_info' not in st.session_state:
    st.session_state.uploaded_file_info = None

if 'uploaded_file_bytes' not in st.session_state:
    st.session_state.uploaded_file_bytes = None

if 'analysis_start_time' not in st.session_state:
    st.session_state.analysis_start_time = None

# Header
st.title("📑 Document Analysis")
st.caption("Upload research papers for comprehensive AI analysis with 11 specialized agents")

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Analysis Settings")

    # Analysis depth selector
    analysis_depth = st.selectbox(
        "Analysis Depth",
        options=["Quick", "Standard", "Comprehensive"],
        index=1,
        help="""
        - **Quick**: Essential insights only (~30s)
        - **Standard**: Full 11-agent analysis (~2-3 min)
        - **Comprehensive**: Deep analysis with context sharing (~3-5 min)
        """
    )

    # Context sharing toggle (for Comprehensive mode)
    if analysis_depth == "Comprehensive":
        enable_context = st.checkbox(
            "Enable Context Sharing",
            value=True,
            help="Two-pass analysis with cross-agent context for better coherence"
        )
    else:
        enable_context = False

    st.markdown("---")

    # Supported formats info
    st.markdown("**📄 Supported Formats:**")
    st.caption("✓ PDF (.pdf)")
    st.caption("✓ Word (.docx)")
    st.caption("✓ LaTeX (.tex)")
    st.caption("✓ HTML (.html)")

    st.markdown("---")

    # Analysis history
    st.markdown("**📊 Session Stats:**")
    try:
        if st.session_state.get('analysis_result'):
            st.metric("Documents Analyzed", "1")
            if 'metrics' in st.session_state.analysis_result:
                metrics = st.session_state.analysis_result['metrics']
                st.metric("Analysis Time", f"{metrics.get('total_time', 0):.1f}s")
                st.metric("Agents Run", f"{metrics.get('successful_agents', 0)}/11")
        else:
            st.metric("Documents Analyzed", "0")
    except (AttributeError, RuntimeError):
        # Not running in Streamlit context
        st.metric("Documents Analyzed", "0")

    st.markdown("---")

    # Clear results
    if st.button("🗑️ Clear All Results", use_container_width=True):
        # Reset to upload phase
        st.session_state.analysis_phase = 'upload'
        st.session_state.analysis_status = None
        st.session_state.agent_statuses = {}
        st.session_state.analysis_result = None
        st.session_state.uploaded_file_info = None
        st.session_state.uploaded_file_bytes = None
        st.session_state.completed_analyses = []
        st.session_state.current_analysis_idx = None
        st.session_state.upload_key += 1  # Force widget reset
        st.session_state.last_file_id = None
        st.rerun()

# Main content area - State Machine Pattern
if st.session_state.analysis_phase == 'upload':
    # UPLOAD PHASE: File upload section
    st.markdown("### 📤 Upload Document")

    # Use dynamic key for widget reset capability
    uploaded_file = st.file_uploader(
        "Choose a research paper",
        type=['pdf', 'docx', 'tex', 'html'],
        help="Upload a research paper in PDF, DOCX, LaTeX, or HTML format",
        key=f"file_uploader_{st.session_state.upload_key}"  # Dynamic key prevents state conflicts
    )

    if uploaded_file is not None:
        # Display file info
        file_size_mb = uploaded_file.size / (1024 * 1024)
        file_extension = Path(uploaded_file.name).suffix.lower()

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**📄 File:** {uploaded_file.name}")
        with col2:
            st.markdown(f"**📊 Size:** {file_size_mb:.2f} MB")
        with col3:
            st.markdown(f"**📋 Format:** {file_extension[1:].upper()}")

        # Generate unique file ID to prevent duplicate processing
        file_id = f"{uploaded_file.name}_{uploaded_file.size}_{file_extension}"

        # Only process if this is a NEW file (prevents 403 errors on re-uploads)
        if st.session_state.last_file_id != file_id:
            st.session_state.uploaded_file_info = {
                'name': uploaded_file.name,
                'size': file_size_mb,
                'format': file_extension
            }
            st.session_state.uploaded_file_bytes = uploaded_file.getvalue()
            st.session_state.last_file_id = file_id

        st.markdown("---")

        # Start analysis button with proper state transition
        def start_analysis_callback():
            # Validate file data exists
            if not st.session_state.uploaded_file_bytes:
                st.error("File data missing. Please re-upload.")
                return

            # Clear any previous analysis results
            st.session_state.agent_statuses = {}
            st.session_state.analysis_result = None

            # Transition to analyzing phase
            st.session_state.analysis_phase = 'analyzing'
            st.session_state.analysis_start_time = time.time()

        st.button(
            "🚀 Start Analysis",
            type="primary",
            use_container_width=True,
            key="start_analysis_btn",
            on_click=start_analysis_callback
        )

    else:
        # Show upload prompt
        st.markdown("""
        <div class="upload-area">
            <h3>📤 Drop your document here</h3>
            <p>or click to browse</p>
            <p style='color: #666; font-size: 0.9rem; margin-top: 16px;'>
                Supports PDF, DOCX, LaTeX, and HTML formats
            </p>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.analysis_phase == 'analyzing':
    # ANALYZING PHASE: Run analysis with progress tracking
    st.markdown("### 🔬 Analysis in Progress")

    # Display file info
    if st.session_state.uploaded_file_info:
        info = st.session_state.uploaded_file_info
        st.info(f"📄 Analyzing: **{info['name']}** ({info['size']:.2f} MB, {info['format'][1:].upper()})")

    # Save uploaded file to temp location
    uploaded_file_bytes = st.session_state.get('uploaded_file_bytes')
    if uploaded_file_bytes is not None:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=st.session_state.uploaded_file_info['format']) as tmp_file:
            tmp_file.write(uploaded_file_bytes)
            tmp_path = tmp_file.name

        # Initialize components
        try:
            # Overall progress bar
            progress_placeholder = st.empty()
            status_placeholder = st.empty()

            # Agent status container
            st.markdown("### 🤖 Agent Progress")
            agent_container = st.container()

            # Results container (will be filled at the end)
            results_container = st.container()

            # Initialize DocumentProcessor
            with status_placeholder:
                st.info("📄 Processing document...")

            doc_processor = DocumentProcessor()
            processed_doc = doc_processor.process_document(
                tmp_path,
                file_format=st.session_state.uploaded_file_info['format'].lstrip('.')
            )

            if not processed_doc.get('success'):
                st.error(f"❌ Document processing failed: {processed_doc.get('error', 'Unknown error')}")
                st.session_state.analysis_in_progress = False
                os.unlink(tmp_path)
                st.stop()

            # Extract text for analysis
            full_text = processed_doc.get('full_text', '')

            with status_placeholder:
                st.success(f"✅ Document processed: {len(full_text)} characters, {processed_doc['metadata'].get('total_pages', 'N/A')} pages")

            time.sleep(1)

            # Initialize orchestrator
            with status_placeholder:
                st.info("🤖 Initializing 11 specialized agents...")

            orchestrator = DocumentAnalysisOrchestrator()

            # Define agent order and metadata
            agent_metadata = {
                'abstract': {'icon': '📝', 'name': 'Abstract Agent', 'focus': 'Summary & Overview'},
                'introduction': {'icon': '🎯', 'name': 'Introduction Agent', 'focus': 'Context & Motivation'},
                'methodology': {'icon': '🔬', 'name': 'Methodology Agent', 'focus': 'Methods & Approach'},
                'results': {'icon': '📊', 'name': 'Results Agent', 'focus': 'Findings & Outcomes'},
                'discussion': {'icon': '💭', 'name': 'Discussion Agent', 'focus': 'Implications & Insights'},
                'conclusion': {'icon': '🎓', 'name': 'Conclusion Agent', 'focus': 'Summary & Future Work'},
                'literature_review': {'icon': '📚', 'name': 'Literature Agent', 'focus': 'Related Work'},
                'references': {'icon': '🔗', 'name': 'References Agent', 'focus': 'Citations & Sources'},
                'tables': {'icon': '📋', 'name': 'Tables Agent', 'focus': 'Quantitative Data'},
                'figures': {'icon': '🖼️', 'name': 'Figures Agent', 'focus': 'Visual Content'},
                'mathematics': {'icon': '🧮', 'name': 'Math Agent', 'focus': 'Equations & Formulas'}
            }

            # Initialize agent statuses
            for agent_id in agent_metadata.keys():
                st.session_state.agent_statuses[agent_id] = 'pending'

            # Create agent status cards
            with agent_container:
                agent_cols = st.columns(2)
                agent_placeholders = {}

                for idx, (agent_id, metadata) in enumerate(agent_metadata.items()):
                    col_idx = idx % 2
                    with agent_cols[col_idx]:
                        agent_placeholders[agent_id] = st.empty()
                        with agent_placeholders[agent_id]:
                            st.markdown(f"""
                            <div class="agent-card pending">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <strong>{metadata['icon']} {metadata['name']}</strong>
                                        <div style="font-size: 0.85rem; color: #666;">{metadata['focus']}</div>
                                    </div>
                                    <span class="status-badge status-pending">⏳ Pending</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

            time.sleep(1)

            # Determine which agents to run based on depth
            if analysis_depth == "Quick":
                # Only essential agents
                agents_to_run = ['abstract', 'methodology', 'results', 'conclusion']
            elif analysis_depth == "Standard":
                # All 11 agents
                agents_to_run = list(agent_metadata.keys())
            else:  # Comprehensive
                # All agents with context sharing
                agents_to_run = list(agent_metadata.keys())

            # Update overall progress
            total_agents = len(agents_to_run)
            completed_agents = 0

            with progress_placeholder:
                st.progress(0.0, text="Starting analysis...")

            # Run analysis (simulate progress updates)
            # Note: In real implementation, we'd need to modify orchestrator to support callbacks
            with status_placeholder:
                st.info(f"🔄 Running {analysis_depth} analysis with {total_agents} agents...")

            # Update agent statuses to "running" one by one (simulation)
            for agent_id in agents_to_run:
                st.session_state.agent_statuses[agent_id] = 'running'

                # Update UI
                if agent_id in agent_placeholders:
                    with agent_placeholders[agent_id]:
                        metadata = agent_metadata[agent_id]
                        st.markdown(f"""
                        <div class="agent-card running">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>{metadata['icon']} {metadata['name']}</strong>
                                    <div style="font-size: 0.85rem; color: #666;">{metadata['focus']}</div>
                                </div>
                                <span class="status-badge status-running">🔄 Running</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                time.sleep(0.2)  # Brief pause for UI update

            # Actually run the analysis
            start_time = time.time()

            analysis_result = orchestrator.analyze_paper(
                pdf_path=tmp_path,
                paper_metadata={'title': st.session_state.uploaded_file_info['name']},
                parallel=True,
                max_workers=11,
                enable_context_sharing=enable_context
            )

            end_time = time.time()
            analysis_time = end_time - start_time

            # Update agent statuses based on results
            for agent_id in agents_to_run:
                if agent_id in analysis_result.get('analysis_results', {}):
                    agent_result = analysis_result['analysis_results'][agent_id]
                    if agent_result.get('success'):
                        st.session_state.agent_statuses[agent_id] = 'completed'
                        completed_agents += 1
                    else:
                        st.session_state.agent_statuses[agent_id] = 'failed'
                else:
                    st.session_state.agent_statuses[agent_id] = 'failed'

                # Update UI
                if agent_id in agent_placeholders:
                    with agent_placeholders[agent_id]:
                        metadata = agent_metadata[agent_id]
                        status = st.session_state.agent_statuses[agent_id]
                        status_class = f"status-{status}"
                        card_class = status

                        if status == 'completed':
                            status_text = "✅ Completed"
                        elif status == 'failed':
                            status_text = "❌ Failed"
                        else:
                            status_text = "⏳ Pending"

                        st.markdown(f"""
                        <div class="agent-card {card_class}">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong>{metadata['icon']} {metadata['name']}</strong>
                                    <div style="font-size: 0.85rem; color: #666;">{metadata['focus']}</div>
                                </div>
                                <span class="status-badge {status_class}">{status_text}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            # Update progress bar
            progress = completed_agents / total_agents
            with progress_placeholder:
                st.progress(progress, text=f"Completed {completed_agents}/{total_agents} agents")

            # Update status
            with status_placeholder:
                if analysis_result.get('success'):
                    st.success(f"✅ Analysis complete in {analysis_time:.1f}s! {completed_agents}/{total_agents} agents successful.")
                else:
                    st.warning(f"⚠️ Analysis completed with some failures. {completed_agents}/{total_agents} agents successful.")

            # Store result
            st.session_state.analysis_result = analysis_result

            # Display results
            with results_container:
                st.markdown("---")
                st.markdown("### 📊 Analysis Results")

                # Summary metrics
                metrics = analysis_result.get('metrics', {})
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">{}</div>
                        <div class="metric-label">Successful Agents</div>
                    </div>
                    """.format(metrics.get('successful_agents', 0)), unsafe_allow_html=True)

                with col2:
                    st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">{:.1f}s</div>
                        <div class="metric-label">Analysis Time</div>
                    </div>
                    """.format(metrics.get('total_time', 0)), unsafe_allow_html=True)

                with col3:
                    context_findings = metrics.get('context_findings', {})
                    total_findings = context_findings.get('total_findings', 0) if enable_context else 0
                    st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">{}</div>
                        <div class="metric-label">Context Findings</div>
                    </div>
                    """.format(total_findings), unsafe_allow_html=True)

                with col4:
                    st.markdown("""
                    <div class="metric-card">
                        <div class="metric-value">{}</div>
                        <div class="metric-label">Pages Processed</div>
                    </div>
                    """.format(processed_doc['metadata'].get('total_pages', 'N/A')), unsafe_allow_html=True)

                st.markdown("---")

                # Display agent results in tabs
                if analysis_result.get('success'):
                    agent_results = analysis_result.get('analysis_results', {})

                    # Create tabs for each successful agent
                    successful_agents = [aid for aid, res in agent_results.items() if res.get('success')]

                    if successful_agents:
                        tabs = st.tabs([f"{agent_metadata.get(aid, {}).get('icon', '📝')} {aid.title()}" for aid in successful_agents])

                        # Show formatted summary instead of tabs
                        st.markdown("### 📝 Comprehensive Analysis Summary\n")

                        # Generate formatted document
                        formatted_report = format_analysis_to_document(
                            analysis_result,
                            st.session_state.uploaded_file_info
                        )

                        # Display formatted summary
                        st.markdown(formatted_report)

                        # Show raw agent details in expandable sections
                        with st.expander("🔍 View Detailed Agent Results (Raw Data)", expanded=False):
                            for idx, agent_id in enumerate(successful_agents):
                                st.markdown(f"#### {agent_metadata.get(agent_id, {}).get('icon', '📝')} {agent_id.title()}")
                                agent_result = agent_results[agent_id]
                                analysis = agent_result.get('analysis', {})
                                st.json(analysis)

                                # Show context info if available
                                if enable_context and agent_result.get('context_aware'):
                                    st.info(f"🔗 Context used from: {', '.join(agent_result.get('context_used', []))}")

                # Download options
                st.markdown("---")
                st.markdown("### 💾 Download Report")

                col1, col2 = st.columns(2)

                # Generate formatted text report
                formatted_report = format_analysis_to_document(
                    analysis_result,
                    st.session_state.uploaded_file_info
                )

                with col1:
                    st.download_button(
                        label="📄 Download as Text Report",
                        data=formatted_report,
                        file_name=f"analysis_{st.session_state.uploaded_file_info['name'].replace('.pdf', '')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                        type="primary"
                    )

                with col2:
                    # Create JSON report
                    report = {
                        'document': st.session_state.uploaded_file_info,
                        'analysis_settings': {
                            'depth': analysis_depth,
                            'context_sharing': enable_context
                        },
                        'timestamp': datetime.now().isoformat(),
                        'results': analysis_result
                    }

                    st.download_button(
                        label="📥 Download as JSON",
                        data=json.dumps(report, indent=2),
                        file_name=f"analysis_{st.session_state.uploaded_file_info['name'].replace('.pdf', '')}.json",
                        mime="application/json",
                        use_container_width=True
                    )

            # Cleanup
            os.unlink(tmp_path)

            # Store analysis results persistently (fixes Bug #3: download clearing results)
            completed_analysis = {
                'timestamp': datetime.now(),
                'file_info': st.session_state.uploaded_file_info.copy(),
                'result': analysis_result,
                'formatted_report': formatted_report,
                'analysis_settings': {
                    'depth': analysis_depth,
                    'context_sharing': enable_context
                }
            }
            st.session_state.completed_analyses.append(completed_analysis)
            st.session_state.current_analysis_idx = len(st.session_state.completed_analyses) - 1

            # Transition to complete phase
            st.session_state.analysis_phase = 'complete'
            st.rerun()

        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

            # Cleanup
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except OSError as e:
                    # Log cleanup error but don't fail the operation
                    print(f"Warning: Failed to delete temporary file {tmp_path}: {e}")

            # Reset to upload phase on error
            st.session_state.analysis_phase = 'upload'
            st.session_state.upload_key += 1

# COMPLETE PHASE: Display results with "Analyze Another" option
elif st.session_state.analysis_phase == 'complete':
    if st.session_state.current_analysis_idx is not None:
        analysis_data = st.session_state.completed_analyses[st.session_state.current_analysis_idx]

        st.success(f"✅ Analysis Complete for: **{analysis_data['file_info']['name']}**")

        # Display formatted summary (persistent, won't disappear on download)
        st.markdown("### 📝 Comprehensive Analysis Summary")
        st.markdown(analysis_data['formatted_report'])

        # Download section (isolated to prevent state clearing)
        st.markdown("---")
        st.markdown("### 💾 Download Report")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Generate PDF report
            try:
                pdf_bytes = generate_pdf_report(
                    analysis_data['formatted_report'],
                    analysis_data['file_info']['name']
                )

                st.download_button(
                    label="📑 Download Comprehensive PDF Report",
                    data=pdf_bytes,
                    file_name=f"analysis_{analysis_data['file_info']['name'].replace('.pdf', '')}_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
                st.caption("📄 Professional multi-page PDF with detailed analysis from all 11 agents")

            except Exception as e:
                st.error(f"Error generating PDF: {e}")
                # Fallback to text report
                st.download_button(
                    label="📄 Download Text Report (Fallback)",
                    data=analysis_data['formatted_report'],
                    file_name=f"analysis_{analysis_data['file_info']['name'].replace('.pdf', '')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

        with col2:
            # Analyze another document button (fixes Bug #2: re-upload issue)
            if st.button("🔄 Analyze Another Document", use_container_width=True):
                # Reset to upload phase with clean state
                st.session_state.analysis_phase = 'upload'
                st.session_state.uploaded_file_bytes = None
                st.session_state.uploaded_file_info = None
                st.session_state.analysis_result = None
                st.session_state.agent_statuses = {}
                st.session_state.upload_key += 1  # Force widget reset
                st.session_state.last_file_id = None
                st.rerun()

        # Show raw data in expandable section
        with st.expander("🔍 View Detailed Agent Results (Raw Data)", expanded=False):
            agent_results = analysis_data['result'].get('analysis_results', {})
            for agent_id, agent_result in agent_results.items():
                if agent_result.get('success'):
                    st.markdown(f"#### {agent_id.title()}")
                    st.json(agent_result.get('analysis', {}))

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <p>Powered by 11 Specialized AI Agents • Real-time Analysis • Multi-format Support</p>
</div>
""", unsafe_allow_html=True)
