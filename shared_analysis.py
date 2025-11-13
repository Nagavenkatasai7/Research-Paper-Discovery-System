"""
Shared Analysis Functions
Used by both app.py and Multi_Agent_Search.py to avoid circular import issues
"""

import streamlit as st
from typing import Dict, Any, Optional
import time


def analyze_paper_comprehensive_shared(paper: Dict, rank: int) -> Optional[Dict]:
    """
    Comprehensive paper analysis using 7 specialized agents.
    This is a wrapper that can be used by multiple pages.
    """
    try:
        # Import here to avoid circular dependencies
        from rag_system.analysis_agents import run_comprehensive_analysis
        from rag_system.pdf_processor import extract_content_from_paper
        from grok_client import GrokClient
        import config

        # Initialize Grok client
        llm = GrokClient(
            api_key=config.GROK_SETTINGS['api_key'],
            model=config.GROK_SETTINGS['model'],
            validate=False
        )

        # Extract content
        with st.spinner("📄 Extracting paper content..."):
            content = extract_content_from_paper(paper)

            if not content or content.get('error'):
                st.error(f"Failed to extract paper content: {content.get('error', 'Unknown error')}")
                return None

        # Run analysis
        with st.spinner("🤖 Running 7-agent comprehensive analysis..."):
            start_time = time.time()

            analysis_results, synthesis = run_comprehensive_analysis(
                paper=content,
                llm_client=llm
            )

            duration = time.time() - start_time

        if not analysis_results:
            st.error("Analysis failed. Please try again.")
            return None

        return {
            'paper': paper,
            'content': content,
            'analysis_results': analysis_results,
            'synthesis': synthesis,
            'duration': duration,
            'rank': rank
        }

    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None


def generate_comprehensive_summary_paragraphs_shared(
    analysis_results: Dict,
    synthesis: str,
    paper_metadata: Dict
) -> Dict[str, str]:
    """
    Generate comprehensive summary paragraphs from analysis results.
    """
    try:
        from grok_client import GrokClient
        import config

        llm = GrokClient(
            api_key=config.GROK_SETTINGS['api_key'],
            model=config.GROK_SETTINGS['model'],
            validate=False
        )

        # Generate summaries for each section
        summaries = {}

        sections = ['introduction', 'methodology', 'results', 'discussion']

        for section in sections:
            if section in analysis_results:
                agent_analysis = analysis_results[section]

                prompt = f"""Based on the following analysis of a research paper's {section}, create a concise 2-3 sentence summary:

Analysis:
{agent_analysis.get('summary', '')}

Summary:"""

                try:
                    summary = llm.generate(
                        prompt=prompt,
                        max_tokens=200,
                        temperature=0.5
                    ).strip()

                    summaries[section] = summary
                except Exception as e:
                    summaries[section] = agent_analysis.get('summary', f'Analysis available for {section}.')

        return summaries

    except Exception as e:
        return {
            'introduction': 'Summary generation failed.',
            'methodology': 'Summary generation failed.',
            'results': 'Summary generation failed.',
            'discussion': 'Summary generation failed.'
        }


def display_comprehensive_agent_analysis_shared(agent_name: str, agent_result: Dict) -> None:
    """
    Display comprehensive analysis results from a specific agent.
    """
    if not agent_result:
        st.warning(f"No analysis available for {agent_name}")
        return

    st.markdown(f"### {agent_name.replace('_', ' ').title()} Analysis")

    # Display summary
    if 'summary' in agent_result:
        st.markdown("#### Summary")
        st.write(agent_result['summary'])

    # Display key findings
    if 'key_findings' in agent_result and agent_result['key_findings']:
        st.markdown("#### Key Findings")
        for i, finding in enumerate(agent_result['key_findings'], 1):
            st.markdown(f"{i}. {finding}")

    # Display strengths
    if 'strengths' in agent_result and agent_result['strengths']:
        st.markdown("#### Strengths")
        for strength in agent_result['strengths']:
            st.markdown(f"- ✅ {strength}")

    # Display limitations
    if 'limitations' in agent_result and agent_result['limitations']:
        st.markdown("#### Limitations")
        for limitation in agent_result['limitations']:
            st.markdown(f"- ⚠️ {limitation}")

    # Display recommendations
    if 'recommendations' in agent_result and agent_result['recommendations']:
        st.markdown("#### Recommendations")
        for rec in agent_result['recommendations']:
            st.markdown(f"- 💡 {rec}")


def display_document_chat_shared(doc_id: str) -> None:
    """
    Display document chat interface.
    """
    st.info("💬 Chat feature: Please use the 'Chat with Paper' page for interactive Q&A.")
    st.markdown("""
    To chat with this paper:
    1. Go to the **Chat with Paper** page from the sidebar
    2. The paper will be automatically loaded
    3. Ask questions and get AI-powered answers!
    """)
