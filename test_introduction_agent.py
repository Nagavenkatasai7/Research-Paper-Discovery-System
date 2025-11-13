"""
Test IntroductionAgent with Transformer Paper
==============================================
"""

import sys
import json
from rag_system.pdf_processor import PDFProcessor
from rag_system.analysis_agents.introduction_agent import IntroductionAgent


def test_introduction_agent():
    print("=" * 80)
    print("INTRODUCTIONAGENT TEST - Transformer Paper")
    print("=" * 80)

    paper_metadata = {
        'title': 'Attention Is All You Need',
        'authors': ['Vaswani', 'Shazeer', 'Parmar', 'Uszkoreit', 'Jones', 'Gomez', 'Kaiser', 'Polosukhin'],
        'year': 2017,
        'doi': '10.48550/arXiv.1706.03762'
    }

    pdf_path = "documents/8277bf0bb00823cca9b6ba58b7f42c48.pdf"

    try:
        # Extract PDF
        print("\nExtracting Introduction section...")
        processor = PDFProcessor()
        extraction_result = processor.extract_text_by_sections(pdf_path)

        if not extraction_result['success']:
            print(f"❌ Extraction failed: {extraction_result['message']}")
            return False

        sections = extraction_result.get('sections', {})

        # Get Introduction - try different possible section names
        intro_text = None
        for key in ['introduction', 'Introduction', 'INTRODUCTION', '1 Introduction', '1. Introduction']:
            if key in sections:
                intro_text = sections[key]
                print(f"✓ Found introduction in section: '{key}'")
                break

        # If not found as separate section, take first part of header
        if not intro_text and 'header' in sections:
            # Take first 3000 chars after abstract (approx introduction)
            full_text = extraction_result['full_text']
            # Find where abstract ends and take next 3000 chars
            intro_text = full_text[2000:5000]  # Rough estimate
            print("✓ Extracted introduction from main text")

        if not intro_text:
            print("❌ Introduction section not found")
            return False

        intro_text = intro_text.strip()[:4000]  # Limit to 4000 chars
        print(f"✓ Introduction extracted ({len(intro_text)} characters)")
        print(f"\nIntroduction preview:")
        print("-" * 80)
        print(intro_text[:300] + "...")
        print("-" * 80)

        # Test agent
        print("\n⏳ Running IntroductionAgent with Grok-4...")
        agent = IntroductionAgent()
        result = agent.analyze(intro_text, paper_metadata)

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
            print(f"\n⚠️  JSON parse failed: {analysis['parse_error']}")
            print("\nRaw response:")
            print(result['raw_response'][:500])
            return False

        # Display results
        print("\n📋 PROBLEM STATEMENT:")
        print("-" * 80)
        print(analysis.get('problem_statement', 'Not found'))

        print("\n⭐ PROBLEM SIGNIFICANCE:")
        print("-" * 80)
        print(analysis.get('problem_significance', 'Not found'))

        print("\n💭 RESEARCH MOTIVATION:")
        print("-" * 80)
        print(analysis.get('research_motivation', 'Not found'))

        print("\n❓ RESEARCH QUESTIONS:")
        print("-" * 80)
        questions = analysis.get('research_questions', [])
        if questions:
            for i, q in enumerate(questions, 1):
                print(f"  {i}. {q}")
        else:
            print("  None explicitly stated")

        print("\n🔬 RESEARCH GAP:")
        print("-" * 80)
        print(analysis.get('research_gap', 'Not found'))

        print("\n✨ NOVELTY CLAIMS:")
        print("-" * 80)
        novelty = analysis.get('novelty_claims', [])
        if isinstance(novelty, list):
            for i, n in enumerate(novelty, 1):
                print(f"  {i}. {n}")
        else:
            print(f"  {novelty}")

        print("\n📈 INTRODUCTION QUALITY:")
        print("-" * 80)
        quality = analysis.get('introduction_quality', {})
        print(f"  Clarity: {quality.get('clarity', 'N/A')}")
        print(f"  Motivation strength: {quality.get('motivation_strength', 'N/A')}")
        print(f"  Problem definition: {quality.get('problem_definition', 'N/A')}")

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
        print("✅ INTRODUCTIONAGENT TEST PASSED!")
        print("=" * 80)

        # Save results
        with open("test_results_introduction_agent.json", 'w') as f:
            json.dump(result, f, indent=2)
        print("\n📄 Results saved to: test_results_introduction_agent.json")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_introduction_agent()
    sys.exit(0 if success else 1)
