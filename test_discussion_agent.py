"""
Test DiscussionAgent with Transformer Paper
============================================
"""

import sys
import json
from rag_system.pdf_processor import PDFProcessor
from rag_system.analysis_agents.discussion_agent import DiscussionAgent


def test_discussion_agent():
    print("=" * 80)
    print("DISCUSSIONAGENT TEST - Transformer Paper")
    print("=" * 80)

    paper_metadata = {
        'title': 'Attention Is All You Need',
        'authors': ['Vaswani et al.'],
        'year': 2017
    }

    pdf_path = "documents/8277bf0bb00823cca9b6ba58b7f42c48.pdf"

    try:
        print("\nExtracting Discussion section...")
        processor = PDFProcessor()
        extraction_result = processor.extract_text_by_sections(pdf_path)

        sections = extraction_result.get('sections', {})

        # Try to find discussion section
        disc_text = None
        for key in ['discussion', 'Discussion', 'DISCUSSION', 'analysis', 'Analysis']:
            if key in sections:
                disc_text = sections[key]
                print(f"✓ Found section: '{key}'")
                break

        # If not found, extract from pages 9-11 (typical discussion location)
        if not disc_text:
            pages = extraction_result.get('pages', [])
            if len(pages) >= 11:
                disc_text = '\n'.join([p['text'] for p in pages[8:11]])
                print("✓ Extracted from pages 9-11 (estimated discussion)")

        if not disc_text:
            print("❌ Discussion section not found")
            return False

        disc_text = disc_text.strip()[:5000]  # Limit to 5000 chars
        print(f"✓ Discussion extracted ({len(disc_text)} characters)")
        print(f"\nPreview:")
        print("-" * 80)
        print(disc_text[:300] + "...")
        print("-" * 80)

        print("\n⏳ Running DiscussionAgent with Grok-4...")
        agent = DiscussionAgent()
        result = agent.analyze(disc_text, paper_metadata)

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

        print("\n💭 RESULTS INTERPRETATION:")
        print("-" * 80)
        interpretation = analysis.get('results_interpretation', 'Not found')
        words = interpretation.split()
        line = ""
        for word in words[:100]:
            if len(line) + len(word) + 1 <= 80:
                line += word + " "
            else:
                print(line.strip())
                line = word + " "
        if line:
            print(line.strip())

        print("\n🔬 THEORETICAL IMPLICATIONS:")
        print("-" * 80)
        theoretical = analysis.get('theoretical_implications', [])
        if theoretical:
            for i, impl in enumerate(theoretical, 1):
                print(f"  {i}. {impl}")
        else:
            print("  None identified")

        print("\n🛠️  PRACTICAL IMPLICATIONS:")
        print("-" * 80)
        practical = analysis.get('practical_implications', [])
        if practical:
            for i, impl in enumerate(practical, 1):
                print(f"  {i}. {impl}")
        else:
            print("  None identified")

        print("\n⚠️  LIMITATIONS:")
        print("-" * 80)
        limitations = analysis.get('limitations', [])
        if limitations:
            for i, lim in enumerate(limitations, 1):
                print(f"  {i}. {lim}")
        else:
            print("  None mentioned")

        print("\n🔍 GENERALIZABILITY:")
        print("-" * 80)
        generalizability = analysis.get('generalizability', 'Not discussed')
        words = generalizability.split()
        line = ""
        for word in words[:100]:
            if len(line) + len(word) + 1 <= 80:
                line += word + " "
            else:
                print(line.strip())
                line = word + " "
        if line:
            print(line.strip())

        print("\n📊 DISCUSSION QUALITY:")
        print("-" * 80)
        quality = analysis.get('discussion_quality', {})
        print(f"  Depth: {quality.get('depth', 'N/A')}")
        print(f"  Balanced: {quality.get('balanced', 'N/A')}")
        print(f"  Limitations honest: {quality.get('limitations_honest', 'N/A')}")

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
        print("✅ DISCUSSIONAGENT TEST PASSED!")
        print("=" * 80)

        with open("test_results_discussion_agent.json", 'w') as f:
            json.dump(result, f, indent=2)
        print("\n📄 Results saved to: test_results_discussion_agent.json")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_discussion_agent()
    sys.exit(0 if success else 1)
