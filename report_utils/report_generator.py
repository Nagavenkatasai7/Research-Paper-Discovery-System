"""
Report Generator Utility
Standalone functions for generating analysis reports without Streamlit dependencies
"""

from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from typing import Dict


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
        # Skip completely empty lines
        if not line or not line.strip():
            pdf.ln(3)
            continue

        # Skip separator lines (=== lines) - don't render them at all
        if line.strip() and all(c == '=' for c in line.strip()):
            continue  # Just skip completely, no ln() call

        # Check if line is a section header (all uppercase)
        if line.strip() and line.strip().isupper() and not line.strip().startswith('**'):
            try:
                # Section header
                pdf.set_font('Helvetica', 'B', 13)
                pdf.set_text_color(0, 51, 102)  # Dark blue
                safe_header = line.strip().encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 8, safe_header, align='L')
                pdf.set_text_color(0, 0, 0)  # Reset to black
                pdf.ln(3)
            except Exception:
                # Skip problematic headers silently
                pass
            continue

        # Regular content
        try:
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

            # Add the line only if it's not empty and not too long
            if safe_line and len(safe_line) > 0:
                pdf.multi_cell(0, 6, safe_line)

        except Exception:
            # Skip problematic lines silently - no warning output
            pass

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
