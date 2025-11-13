"""
Test MethodologyAgent with Transformer Paper
==============================================
"""

import sys
import json
from rag_system.pdf_processor import PDFProcessor
from rag_system.analysis_agents.methodology_agent import MethodologyAgent


def test_methodology_agent():
    print("=" * 80)
    print("METHODOLOGYAGENT TEST - Transformer Paper")
    print("=" * 80)

    paper_metadata = {
        'title': 'Attention Is All You Need',
        'authors': ['Vaswani et al.'],
        'year': 2017
    }

    pdf_path = "documents/8277bf0bb00823cca9b6ba58b7f42c48.pdf"

    try:
        print("\nExtracting Methodology/Model Architecture section...")
        processor = PDFProcessor()
        extraction_result = processor.extract_text_by_sections(pdf_path)

        sections = extraction_result.get('sections', {})

        # Try to find methodology section
        method_text = None
        for key in ['methodology', 'Methodology', 'METHODOLOGY', 'methods', 'Methods',
                    'model', 'Model Architecture', 'architecture']:
            if key in sections:
                method_text = sections[key]
                print(f"✓ Found section: '{key}'")
                break

        # If not found, extract from pages 2-4 (typical methodology location)
        if not method_text:
            pages = extraction_result.get('pages', [])
            if len(pages) >= 4:
                method_text = '\n'.join([p['text'] for p in pages[1:4]])
                print("✓ Extracted from pages 2-4 (estimated methodology)")

        if not method_text:
            print("❌ Methodology section not found")
            return False

        method_text = method_text.strip()[:6000]  # Limit to 6000 chars
        print(f"✓ Methodology extracted ({len(method_text)} characters)")
        print(f"\nPreview:")
        print("-" * 80)
        print(method_text[:300] + "...")
        print("-" * 80)

        print("\n⏳ Running MethodologyAgent with Grok-4...")
        agent = MethodologyAgent()
        result = agent.analyze(method_text, paper_metadata)

        print("\n" + "=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)

        if not result['success']:
            print(f"❌ Failed: {result['message']}")
            return False

        print(f"✓ Completed!")
        print(f"  Time: {result['elapsed_time']:.2f}s")
        print(f"  Tokens: {result.get('tokens_used', 'N/A')}")

        analysis = result['analysis']

        if 'parse_error' in analysis:
            print(f"\n⚠️  JSON parse failed")
            print("\nRaw response:")
            print(result['raw_response'][:500])
            return False

        print("\n🔬 RESEARCH DESIGN:")
        print("-" * 80)
        print(analysis.get('research_design', 'Not found'))

        print("\n📊 DATA SOURCES:")
        print("-" * 80)
        sources = analysis.get('data_sources', [])
        if sources:
            for i, src in enumerate(sources, 1):
                print(f"  {i}. {src}")
        else:
            print("  None identified")

        print("\n🔧 ANALYSIS TECHNIQUES:")
        print("-" * 80)
        techniques = analysis.get('analysis_techniques', [])
        if techniques:
            for i, tech in enumerate(techniques[:5], 1):
                print(f"  {i}. {tech}")
        else:
            print("  None identified")

        print("\n🛠️  TOOLS AND FRAMEWORKS:")
        print("-" * 80)
        tools = analysis.get('tools_and_frameworks', [])
        if tools:
            for i, tool in enumerate(tools[:5], 1):
                print(f"  {i}. {tool}")
        else:
            print("  None identified")

        print("\n⚙️  EXPERIMENTAL SETUP:")
        print("-" * 80)
        setup = analysis.get('experimental_setup', 'Not described')
        words = setup.split()
        line = ""
        for word in words[:100]:  # Limit to first 100 words
            if len(line) + len(word) + 1 <= 80:
                line += word + " "
            else:
                print(line.strip())
                line = word + " "
        if line:
            print(line.strip())

        print("\n📏 EVALUATION METRICS:")
        print("-" * 80)
        metrics = analysis.get('evaluation_metrics', [])
        if metrics:
            for i, metric in enumerate(metrics, 1):
                print(f"  {i}. {metric}")
        else:
            print("  None identified")

        print("\n♻️  REPRODUCIBILITY:")
        print("-" * 80)
        repro = analysis.get('reproducibility', {})
        print(f"  Score: {repro.get('score', 'N/A')}")
        details = repro.get('details_provided', [])
        if details:
            print(f"  Details provided:")
            for i, detail in enumerate(details[:3], 1):
                print(f"    {i}. {detail}")
        missing = repro.get('missing_details', [])
        if missing:
            print(f"  Missing details:")
            for i, miss in enumerate(missing[:3], 1):
                print(f"    {i}. {miss}")

        print("\n🔍 CRITICAL ANALYSIS:")
        print("-" * 80)
        critical = analysis.get('critical_analysis', 'Not provided')
        words = critical.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 <= 80:
                line += word + " "
            else:
                print(line.strip())
                line = word + " "
        if line:
            print(line.strip())

        print("\n" + "=" * 80)
        print("✅ METHODOLOGYAGENT TEST PASSED!")
        print("=" * 80)

        with open("test_results_methodology_agent.json", 'w') as f:
            json.dump(result, f, indent=2)
        print("\n📄 Results saved to: test_results_methodology_agent.json")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_methodology_agent()
    sys.exit(0 if success else 1)
