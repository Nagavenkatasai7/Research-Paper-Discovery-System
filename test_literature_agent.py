"""
Test LiteratureReviewAgent with Transformer Paper
==================================================
"""

import sys
import json
from rag_system.pdf_processor import PDFProcessor
from rag_system.analysis_agents.literature_review_agent import LiteratureReviewAgent


def test_literature_agent():
    print("=" * 80)
    print("LITERATUREREVIEWAGENT TEST - Transformer Paper")
    print("=" * 80)

    paper_metadata = {
        'title': 'Attention Is All You Need',
        'authors': ['Vaswani et al.'],
        'year': 2017
    }

    pdf_path = "documents/8277bf0bb00823cca9b6ba58b7f42c48.pdf"

    try:
        print("\nExtracting Related Work/Literature Review section...")
        processor = PDFProcessor()
        extraction_result = processor.extract_text_by_sections(pdf_path)

        sections = extraction_result.get('sections', {})

        # Try to find literature review section
        lit_text = None
        for key in ['related_work', 'Related Work', 'RELATED WORK', 'related work',
                    'literature', 'Literature', 'background', 'Background']:
            if key in sections:
                lit_text = sections[key]
                print(f"✓ Found section: '{key}'")
                break

        # If not found, extract from specific page range (related work is usually early)
        if not lit_text:
            # Get pages 4-6 which typically contain related work
            pages = extraction_result.get('pages', [])
            if len(pages) >= 6:
                lit_text = '\n'.join([p['text'] for p in pages[3:6]])
                print("✓ Extracted from pages 4-6 (estimated related work)")

        if not lit_text:
            print("❌ Literature review section not found")
            return False

        lit_text = lit_text.strip()[:5000]  # Limit to 5000 chars
        print(f"✓ Literature review extracted ({len(lit_text)} characters)")
        print(f"\nPreview:")
        print("-" * 80)
        print(lit_text[:300] + "...")
        print("-" * 80)

        print("\n⏳ Running LiteratureReviewAgent with Grok-4...")
        agent = LiteratureReviewAgent()
        result = agent.analyze(lit_text, paper_metadata)

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

        print("\n📚 PRIOR WORK CATEGORIES:")
        print("-" * 80)
        categories = analysis.get('prior_work_categories', [])
        if categories:
            for i, cat in enumerate(categories, 1):
                print(f"  {i}. {cat}")
        else:
            print("  None identified")

        print("\n📄 KEY PAPERS CITED:")
        print("-" * 80)
        papers = analysis.get('key_papers_cited', [])
        if papers:
            for i, paper in enumerate(papers[:5], 1):  # Show first 5
                if isinstance(paper, dict):
                    print(f"  {i}. {paper.get('title', 'Unknown')}")
                    print(f"     → {paper.get('contribution', 'N/A')}")
                else:
                    print(f"  {i}. {paper}")
        else:
            print("  None identified")

        print("\n🔬 THEORETICAL FRAMEWORKS:")
        print("-" * 80)
        frameworks = analysis.get('theoretical_frameworks', [])
        if frameworks:
            for i, fw in enumerate(frameworks, 1):
                print(f"  {i}. {fw}")
        else:
            print("  None identified")

        print("\n🔍 RESEARCH GAPS:")
        print("-" * 80)
        gaps = analysis.get('research_gaps', [])
        if gaps:
            for i, gap in enumerate(gaps, 1):
                print(f"  {i}. {gap}")
        else:
            print("  None identified")

        print("\n🆚 COMPARISON WITH PRIOR WORK:")
        print("-" * 80)
        comparison = analysis.get('comparison_with_prior', 'Not found')
        words = comparison.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 <= 80:
                line += word + " "
            else:
                print(line.strip())
                line = word + " "
        if line:
            print(line.strip())

        print("\n📈 LITERATURE QUALITY:")
        print("-" * 80)
        quality = analysis.get('literature_quality', {})
        print(f"  Comprehensiveness: {quality.get('comprehensiveness', 'N/A')}")
        print(f"  Critical analysis: {quality.get('critical_analysis', 'N/A')}")
        print(f"  Clear gap identification: {quality.get('clear_gap_identification', 'N/A')}")

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
        print("✅ LITERATUREREVIEWAGENT TEST PASSED!")
        print("=" * 80)

        with open("test_results_literature_agent.json", 'w') as f:
            json.dump(result, f, indent=2)
        print("\n📄 Results saved to: test_results_literature_agent.json")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_literature_agent()
    sys.exit(0 if success else 1)
