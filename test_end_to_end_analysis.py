"""
End-to-End Integration Test for Document Analysis
Tests the complete workflow from document upload to PDF generation
"""

import sys
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import required modules
from rag_system.analysis_agents import DocumentAnalysisOrchestrator
from report_utils.report_generator import format_analysis_to_document, generate_pdf_report

def test_end_to_end_workflow():
    """Test complete document analysis workflow"""
    print("="*60)
    print("END-TO-END DOCUMENT ANALYSIS TEST")
    print("="*60)
    print()

    # Step 1: Load a sample PDF
    print("Step 1: Loading sample PDF...")
    test_pdf = Path("documents/6ed73c0a06e295e45222ae5a451d4d5d.pdf")

    if not test_pdf.exists():
        print(f"❌ Test PDF not found at {test_pdf}")
        print("Looking for alternative PDFs...")
        # Try to find any PDF
        pdf_files = list(Path("documents").glob("*.pdf"))
        if not pdf_files:
            print("❌ No PDFs found in documents folder")
            return False
        test_pdf = pdf_files[0]
        print(f"✅ Using alternative PDF: {test_pdf}")
    else:
        print(f"✅ Found test PDF: {test_pdf}")

    print()

    # Step 2: Run 11-agent analysis (orchestrator handles PDF extraction internally)
    print("Step 2: Running 11-agent comprehensive analysis...")
    print("   This may take 1-2 minutes...")
    print()

    try:
        orchestrator = DocumentAnalysisOrchestrator()

        start_time = time.time()
        analysis_result = orchestrator.analyze_paper(
            pdf_path=str(test_pdf),
            paper_metadata={
                'title': test_pdf.name,
                'source': 'local'
            }
        )
        end_time = time.time()

        if not analysis_result.get('success'):
            print(f"❌ Analysis failed: {analysis_result.get('message', 'Unknown error')}")
            return False

        print(f"✅ Analysis completed in {end_time - start_time:.2f} seconds")

        # Check agent results
        agent_results = analysis_result.get('analysis_results', {})
        successful_agents = sum(1 for r in agent_results.values() if r.get('success'))
        total_agents = len(agent_results)

        print(f"   Successful agents: {successful_agents}/{total_agents}")

        # List agent statuses
        print()
        print("   Agent Status:")
        for agent_name, result in agent_results.items():
            status = "✅" if result.get('success') else "❌"
            print(f"   {status} {agent_name}")

        if successful_agents < 5:
            print(f"❌ Too many agent failures ({total_agents - successful_agents} failed)")
            return False

    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()

    # Step 3: Format analysis to document
    print("Step 3: Formatting analysis to document...")
    try:
        document_info = {
            'name': test_pdf.name,
            'size': test_pdf.stat().st_size / (1024 * 1024),  # MB
            'format': 'pdf'
        }

        formatted_content = format_analysis_to_document(analysis_result, document_info)

        if len(formatted_content) < 100:
            print(f"❌ Formatted content too short: {len(formatted_content)} characters")
            return False

        print(f"✅ Formatted content: {len(formatted_content)} characters")
        print(f"   Lines: {len(formatted_content.split(chr(10)))}")

    except Exception as e:
        print(f"❌ Formatting error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()

    # Step 4: Generate PDF report
    print("Step 4: Generating PDF report...")
    try:
        pdf_bytes = generate_pdf_report(formatted_content, test_pdf.name)

        if not isinstance(pdf_bytes, bytes) or len(pdf_bytes) == 0:
            print(f"❌ PDF generation failed: Invalid output")
            return False

        print(f"✅ PDF generated: {len(pdf_bytes)} bytes")

        # Save to file for manual verification
        output_path = Path("test_end_to_end_report.pdf")
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)

        print(f"✅ PDF saved to: {output_path}")
        print(f"   File size: {output_path.stat().st_size} bytes")

    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()

    # Step 5: Verify PDF structure
    print("Step 5: Verifying PDF structure...")
    try:
        import subprocess
        result = subprocess.run(['file', str(output_path)], capture_output=True, text=True)

        if 'PDF document' in result.stdout:
            print(f"✅ Valid PDF document")
            print(f"   {result.stdout.strip()}")
        else:
            print(f"❌ Invalid PDF: {result.stdout}")
            return False

    except Exception as e:
        print(f"⚠️  Could not verify PDF structure: {e}")
        print("   (This is not critical - PDF was still generated)")

    print()
    print("="*60)
    print("✅ END-TO-END TEST PASSED")
    print("="*60)
    print()
    print("Summary:")
    print(f"  • PDF analyzed: {test_pdf.name}")
    print(f"  • Agents run: {successful_agents}/{total_agents} successful")
    print(f"  • Analysis time: {end_time - start_time:.2f} seconds")
    print(f"  • Content formatted: {len(formatted_content)} characters")
    print(f"  • PDF generated: {len(pdf_bytes)} bytes")
    print(f"  • Output file: {output_path}")
    print()
    print("Next steps:")
    print("  1. Open test_end_to_end_report.pdf to verify formatting")
    print("  2. Check that all sections are present and readable")
    print("  3. Verify that agent analysis content is included")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_end_to_end_workflow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
