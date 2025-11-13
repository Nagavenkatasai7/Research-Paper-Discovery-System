"""
Document Analysis - Upload and analyze research papers with AI
Real-time 11-agent analysis with progress tracking
"""

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

# Initialize session state
if 'analysis_status' not in st.session_state:
    st.session_state.analysis_status = None

if 'agent_statuses' not in st.session_state:
    st.session_state.agent_statuses = {}

if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

if 'uploaded_file_info' not in st.session_state:
    st.session_state.uploaded_file_info = None

if 'analysis_in_progress' not in st.session_state:
    st.session_state.analysis_in_progress = False

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
    if st.session_state.analysis_result:
        st.metric("Documents Analyzed", "1")
        if 'metrics' in st.session_state.analysis_result:
            metrics = st.session_state.analysis_result['metrics']
            st.metric("Analysis Time", f"{metrics.get('total_time', 0):.1f}s")
            st.metric("Agents Run", f"{metrics.get('successful_agents', 0)}/11")
    else:
        st.metric("Documents Analyzed", "0")

    st.markdown("---")

    # Clear results
    if st.button("🗑️ Clear Results", use_container_width=True):
        st.session_state.analysis_status = None
        st.session_state.agent_statuses = {}
        st.session_state.analysis_result = None
        st.session_state.uploaded_file_info = None
        st.session_state.analysis_in_progress = False
        st.rerun()

# Main content area
if not st.session_state.analysis_in_progress:
    # File upload section
    st.markdown("### 📤 Upload Document")

    uploaded_file = st.file_uploader(
        "Choose a research paper",
        type=['pdf', 'docx', 'tex', 'html'],
        help="Upload a research paper in PDF, DOCX, LaTeX, or HTML format",
        key="file_uploader"
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

        # Save uploaded file info
        st.session_state.uploaded_file_info = {
            'name': uploaded_file.name,
            'size': file_size_mb,
            'format': file_extension
        }

        st.markdown("---")

        # Start analysis button
        if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
            st.session_state.analysis_in_progress = True
            st.rerun()

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

else:
    # Analysis in progress
    st.markdown("### 🔬 Analysis in Progress")

    # Display file info
    if st.session_state.uploaded_file_info:
        info = st.session_state.uploaded_file_info
        st.info(f"📄 Analyzing: **{info['name']}** ({info['size']:.2f} MB, {info['format'][1:].upper()})")

    # Save uploaded file to temp location
    uploaded_file = st.session_state.get('file_uploader')
    if uploaded_file is not None:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=st.session_state.uploaded_file_info['format']) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
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
                file_format=st.session_state.uploaded_file_info['format']
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

                        for idx, agent_id in enumerate(successful_agents):
                            with tabs[idx]:
                                agent_result = agent_results[agent_id]
                                analysis = agent_result.get('analysis', {})

                                # Display analysis as formatted JSON
                                st.json(analysis)

                                # Show context info if available
                                if enable_context and agent_result.get('context_aware'):
                                    st.info(f"🔗 Context used from: {', '.join(agent_result.get('context_used', []))}")

                # Download results button
                if st.button("💾 Download Analysis Report", type="primary", use_container_width=True):
                    # Create downloadable report
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
                        label="📥 Download JSON Report",
                        data=json.dumps(report, indent=2),
                        file_name=f"analysis_{st.session_state.uploaded_file_info['name']}.json",
                        mime="application/json",
                        use_container_width=True
                    )

            # Cleanup
            os.unlink(tmp_path)

            # Analysis complete
            st.session_state.analysis_in_progress = False

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

            st.session_state.analysis_in_progress = False

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <p>Powered by 11 Specialized AI Agents • Real-time Analysis • Multi-format Support</p>
</div>
""", unsafe_allow_html=True)
