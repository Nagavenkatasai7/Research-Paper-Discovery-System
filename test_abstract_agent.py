"""
Test AbstractAgent with Transformer Paper
==========================================

Tests the AbstractAgent with the already downloaded Transformer paper.
Validates the quality and completeness of the abstract analysis.
"""

import sys
import json
from rag_system.pdf_processor import PDFProcessor
from rag_system.analysis_agents.abstract_agent import AbstractAgent


def test_abstract_agent():
    """Test AbstractAgent with real paper"""

    print("=" * 80)
    print("ABSTRACTAGENT TEST - Transformer Paper")
    print("=" * 80)

    # Paper metadata
    paper_metadata = {
        'title': 'Attention Is All You Need',
        'authors': ['Vaswani', 'Shazeer', 'Parmar', 'Uszkoreit', 'Jones', 'Gomez', 'Kaiser', 'Polosukhin'],
        'year': 2017,
        'doi': '10.48550/arXiv.1706.03762'
    }

    # Path to downloaded PDF
    pdf_path = "documents/8277bf0bb00823cca9b6ba58b7f42c48.pdf"

    try:
        # Step 1: Extract PDF text
        print("\nStep 1: Extracting PDF text...")
        print("-" * 80)

        processor = PDFProcessor()
        extraction_result = processor.extract_text_by_sections(pdf_path)

        if not extraction_result['success']:
            print(f"❌ PDF extraction failed: {extraction_result['message']}")
            return False

        print(f"✓ PDF extracted successfully")
        print(f"  Total pages: {extraction_result['total_pages']}")

        # Step 2: Get Abstract section
        print("\nStep 2: Extracting Abstract section...")
        print("-" * 80)

        sections = extraction_result.get('sections', {})

        # Try different section names for abstract
        abstract_text = None
        for key in ['abstract', 'Abstract', 'ABSTRACT', 'header']:
            if key in sections:
                abstract_text = sections[key]
                print(f"✓ Found abstract in section: '{key}'")
                break

        if not abstract_text:
            print("❌ Abstract section not found in PDF")
            print(f"Available sections: {list(sections.keys())}")
            return False

        # Clean and limit abstract text (first 2000 chars should be enough)
        abstract_text = abstract_text.strip()[:2000]

        print(f"✓ Abstract extracted ({len(abstract_text)} characters)")
        print(f"\nAbstract preview:")
        print("-" * 80)
        print(abstract_text[:500] + "..." if len(abstract_text) > 500 else abstract_text)
        print("-" * 80)

        # Step 3: Test AbstractAgent
        print("\nStep 3: Running AbstractAgent analysis with Grok-4...")
        print("-" * 80)
        print("⏳ Calling Grok-4 API... (this may take 10-30 seconds)")

        agent = AbstractAgent()
        result = agent.analyze(
            section_text=abstract_text,
            paper_metadata=paper_metadata,
            temperature=0.3,
            max_tokens=4000
        )

        # Step 4: Display results
        print("\nStep 4: Analysis Results")
        print("=" * 80)

        if not result['success']:
            print(f"❌ Analysis failed: {result['message']}")
            return False

        print(f"✓ Analysis completed successfully!")
        print(f"  Agent: {result['agent_name']}")
        print(f"  Section: {result['section_name']}")
        print(f"  Time taken: {result['elapsed_time']:.2f}s")
        print(f"  Tokens used: {result.get('tokens_used', 'N/A')}")

        # Display analysis
        analysis = result['analysis']

        print("\n" + "=" * 80)
        print("ABSTRACT ANALYSIS RESULTS")
        print("=" * 80)

        if 'parse_error' in analysis:
            print("\n⚠️  Warning: JSON parsing failed")
            print(f"Error: {analysis['parse_error']}")
            print("\nRaw response:")
            print("-" * 80)
            print(result['raw_response'])
            print("-" * 80)
            return False

        # Display structured analysis
        print("\n📋 RESEARCH OBJECTIVE:")
        print("-" * 80)
        print(analysis.get('research_objective', 'Not found'))

        print("\n❓ RESEARCH QUESTION:")
        print("-" * 80)
        print(analysis.get('research_question', 'Not found'))

        print("\n🔬 METHODOLOGY SUMMARY:")
        print("-" * 80)
        print(analysis.get('methodology_summary', 'Not found'))

        print("\n📊 KEY FINDINGS:")
        print("-" * 80)
        findings = analysis.get('key_findings', [])
        if findings:
            for i, finding in enumerate(findings, 1):
                print(f"  {i}. {finding}")
        else:
            print("  None found")

        print("\n💡 MAIN CONTRIBUTIONS:")
        print("-" * 80)
        contributions = analysis.get('main_contributions', [])
        if contributions:
            for i, contribution in enumerate(contributions, 1):
                print(f"  {i}. {contribution}")
        else:
            print("  None found")

        print("\n🎯 SCOPE:")
        print("-" * 80)
        print(analysis.get('scope', 'Not specified'))

        print("\n⚠️  LIMITATIONS MENTIONED:")
        print("-" * 80)
        limitations = analysis.get('limitations_mentioned', [])
        if limitations:
            for i, limitation in enumerate(limitations, 1):
                print(f"  {i}. {limitation}")
        else:
            print("  None mentioned in abstract")

        print("\n✨ NOVELTY CLAIMS:")
        print("-" * 80)
        print(analysis.get('novelty_claims', 'Not found'))

        print("\n📈 ABSTRACT QUALITY:")
        print("-" * 80)
        quality = analysis.get('abstract_quality', {})
        print(f"  Clarity: {quality.get('clarity', 'N/A')}")
        print(f"  Completeness: {quality.get('completeness', 'N/A')}")
        missing = quality.get('missing_elements', [])
        if missing:
            print(f"  Missing elements: {', '.join(missing)}")
        else:
            print(f"  Missing elements: None")

        print("\n🔍 CRITICAL ANALYSIS:")
        print("-" * 80)
        critical_analysis = analysis.get('critical_analysis', 'Not provided')
        # Wrap text at 80 characters
        words = critical_analysis.split()
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
        print("✅ ABSTRACTAGENT TEST PASSED!")
        print("=" * 80)

        # Save full analysis to file for review
        output_file = "test_results_abstract_agent.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"\n📄 Full results saved to: {output_file}")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_abstract_agent()
    sys.exit(0 if success else 1)
