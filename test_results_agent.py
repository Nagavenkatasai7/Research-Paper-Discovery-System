"""
Test ResultsAgent with Transformer Paper
=========================================
"""

import sys
import json
from rag_system.pdf_processor import PDFProcessor
from rag_system.analysis_agents.results_agent import ResultsAgent


def test_results_agent():
    print("=" * 80)
    print("RESULTSAGENT TEST - Transformer Paper")
    print("=" * 80)

    paper_metadata = {
        'title': 'Attention Is All You Need',
        'authors': ['Vaswani et al.'],
        'year': 2017
    }

    pdf_path = "documents/8277bf0bb00823cca9b6ba58b7f42c48.pdf"

    try:
        print("\nExtracting Results section...")
        processor = PDFProcessor()
        extraction_result = processor.extract_text_by_sections(pdf_path)

        sections = extraction_result.get('sections', {})

        # Try to find results section
        results_text = None
        for key in ['results', 'Results', 'RESULTS', 'experiments', 'Experiments',
                    'experimental results', 'Experimental Results']:
            if key in sections:
                results_text = sections[key]
                print(f"✓ Found section: '{key}'")
                break

        # If not found, extract from pages 6-9 (typical results location)
        if not results_text:
            pages = extraction_result.get('pages', [])
            if len(pages) >= 9:
                results_text = '\n'.join([p['text'] for p in pages[5:9]])
                print("✓ Extracted from pages 6-9 (estimated results)")

        if not results_text:
            print("❌ Results section not found")
            return False

        results_text = results_text.strip()[:6000]  # Limit to 6000 chars
        print(f"✓ Results extracted ({len(results_text)} characters)")
        print(f"\nPreview:")
        print("-" * 80)
        print(results_text[:300] + "...")
        print("-" * 80)

        print("\n⏳ Running ResultsAgent with Grok-4...")
        agent = ResultsAgent()
        result = agent.analyze(results_text, paper_metadata)

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

        print("\n📊 MAIN FINDINGS:")
        print("-" * 80)
        findings = analysis.get('main_findings', [])
        if findings:
            for i, finding in enumerate(findings, 1):
                print(f"  {i}. {finding}")
        else:
            print("  None identified")

        print("\n📈 PERFORMANCE METRICS:")
        print("-" * 80)
        metrics = analysis.get('performance_metrics', {})
        if metrics:
            for key, value in list(metrics.items())[:10]:
                print(f"  {key}: {value}")
        else:
            print("  None identified")

        print("\n📉 STATISTICAL TESTS:")
        print("-" * 80)
        tests = analysis.get('statistical_tests', [])
        if tests:
            for i, test in enumerate(tests[:5], 1):
                print(f"  {i}. {test}")
        else:
            print("  None mentioned")

        print("\n🆚 COMPARISONS:")
        print("-" * 80)
        comparisons = analysis.get('comparisons', {})
        baselines = comparisons.get('baseline_models', [])
        if baselines:
            print("  Baseline models:")
            for i, baseline in enumerate(baselines[:5], 1):
                print(f"    {i}. {baseline}")
        comparison_summary = comparisons.get('performance_comparison', 'Not provided')
        if comparison_summary != 'Not provided':
            print(f"\n  Performance comparison:")
            words = comparison_summary.split()
            line = "    "
            for word in words[:50]:
                if len(line) + len(word) + 1 <= 80:
                    line += word + " "
                else:
                    print(line.strip())
                    line = "    " + word + " "
            if line.strip():
                print(line.strip())

        print("\n⚠️  UNEXPECTED RESULTS:")
        print("-" * 80)
        unexpected = analysis.get('unexpected_results', [])
        if unexpected:
            for i, unex in enumerate(unexpected, 1):
                print(f"  {i}. {unex}")
        else:
            print("  None reported")

        print("\n📊 RESULTS QUALITY:")
        print("-" * 80)
        quality = analysis.get('results_quality', {})
        print(f"  Statistical rigor: {quality.get('statistical_rigor', 'N/A')}")
        print(f"  Completeness: {quality.get('completeness', 'N/A')}")

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
        print("✅ RESULTSAGENT TEST PASSED!")
        print("=" * 80)

        with open("test_results_results_agent.json", 'w') as f:
            json.dump(result, f, indent=2)
        print("\n📄 Results saved to: test_results_results_agent.json")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_results_agent()
    sys.exit(0 if success else 1)
