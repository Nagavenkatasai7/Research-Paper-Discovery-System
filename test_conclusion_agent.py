"""
Test ConclusionAgent with Transformer Paper
============================================
"""

import sys
import json
from rag_system.pdf_processor import PDFProcessor
from rag_system.analysis_agents.conclusion_agent import ConclusionAgent


def test_conclusion_agent():
    print("=" * 80)
    print("CONCLUSIONAGENT TEST - Transformer Paper")
    print("=" * 80)

    paper_metadata = {
        'title': 'Attention Is All You Need',
        'authors': ['Vaswani et al.'],
        'year': 2017
    }

    pdf_path = "documents/8277bf0bb00823cca9b6ba58b7f42c48.pdf"

    try:
        print("\nExtracting Conclusion section...")
        processor = PDFProcessor()
        extraction_result = processor.extract_text_by_sections(pdf_path)

        sections = extraction_result.get('sections', {})

        # Try to find conclusion section
        conclusion_text = None
        for key in ['conclusion', 'Conclusion', 'CONCLUSION', 'conclusions', 'Conclusions',
                    'summary', 'Summary', 'future work', 'Future Work']:
            if key in sections:
                conclusion_text = sections[key]
                print(f"✓ Found section: '{key}'")
                break

        # If not found, extract from last pages (typical conclusion location)
        if not conclusion_text:
            pages = extraction_result.get('pages', [])
            if len(pages) >= 12:
                # Try last 2-3 pages for conclusion
                conclusion_text = '\n'.join([p['text'] for p in pages[-3:]])
                print("✓ Extracted from last 3 pages (estimated conclusion)")

        if not conclusion_text:
            print("❌ Conclusion section not found")
            return False

        conclusion_text = conclusion_text.strip()[:5000]  # Limit to 5000 chars
        print(f"✓ Conclusion extracted ({len(conclusion_text)} characters)")
        print(f"\nPreview:")
        print("-" * 80)
        print(conclusion_text[:300] + "...")
        print("-" * 80)

        print("\n⏳ Running ConclusionAgent with Grok-4...")
        agent = ConclusionAgent()
        result = agent.analyze(conclusion_text, paper_metadata)

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

        print("\n🎯 MAIN CONTRIBUTIONS:")
        print("-" * 80)
        contributions = analysis.get('main_contributions', [])
        if contributions:
            for i, contrib in enumerate(contributions, 1):
                print(f"  {i}. {contrib}")
        else:
            print("  None identified")

        print("\n💡 KEY TAKEAWAYS:")
        print("-" * 80)
        takeaways = analysis.get('key_takeaways', [])
        if takeaways:
            for i, takeaway in enumerate(takeaways, 1):
                print(f"  {i}. {takeaway}")
        else:
            print("  None identified")

        print("\n⚠️  LIMITATIONS STATED:")
        print("-" * 80)
        limitations = analysis.get('limitations_stated', [])
        if limitations:
            for i, lim in enumerate(limitations, 1):
                print(f"  {i}. {lim}")
        else:
            print("  None mentioned")

        print("\n🔮 FUTURE DIRECTIONS:")
        print("-" * 80)
        future = analysis.get('future_directions', [])
        if future:
            for i, direction in enumerate(future, 1):
                print(f"  {i}. {direction}")
        else:
            print("  None mentioned")

        print("\n🌍 BROADER IMPACT:")
        print("-" * 80)
        impact = analysis.get('broader_impact', 'Not discussed')
        words = impact.split()
        line = ""
        for word in words[:100]:
            if len(line) + len(word) + 1 <= 80:
                line += word + " "
            else:
                print(line.strip())
                line = word + " "
        if line:
            print(line.strip())

        print("\n📊 CONCLUSION QUALITY:")
        print("-" * 80)
        quality = analysis.get('conclusion_quality', {})
        print(f"  Comprehensive: {quality.get('comprehensive', 'N/A')}")
        print(f"  Forward-looking: {quality.get('forward_looking', 'N/A')}")
        print(f"  Actionable: {quality.get('actionable', 'N/A')}")

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
        print("✅ CONCLUSIONAGENT TEST PASSED!")
        print("=" * 80)

        with open("test_results_conclusion_agent.json", 'w') as f:
            json.dump(result, f, indent=2)
        print("\n📄 Results saved to: test_results_conclusion_agent.json")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_conclusion_agent()
    sys.exit(0 if success else 1)
