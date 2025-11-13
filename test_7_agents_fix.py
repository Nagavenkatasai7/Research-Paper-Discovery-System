"""
Test Script: Verify All 7 Agents Execute Successfully
Tests the fixed orchestrator with robust section extraction
"""

import sys
sys.path.append('.')

import time
from rag_system.analysis_agents.orchestrator import DocumentAnalysisOrchestrator

def test_7_agents():
    """Test that all 7 agents run successfully on a sample paper"""

    print("="*80)
    print("Testing 7-Agent System with Fixed Orchestrator")
    print("="*80)

    # Initialize orchestrator
    orchestrator = DocumentAnalysisOrchestrator()

    # Test with a sample PDF (using the quantum computing paper from previous tests)
    pdf_path = "test_papers/quantum_paper.pdf"  # This should exist from previous tests

    # If test PDF doesn't exist, we'll use any available PDF
    import os
    if not os.path.exists(pdf_path):
        print(f"⚠️  Test PDF not found at {pdf_path}")
        print("Looking for any available PDF...")

        # Try to find any PDF in common locations
        search_paths = [
            "test_papers/",
            "papers/",
            "downloads/",
            "."
        ]

        found = False
        for search_path in search_paths:
            if os.path.exists(search_path):
                for file in os.listdir(search_path):
                    if file.endswith('.pdf'):
                        pdf_path = os.path.join(search_path, file)
                        print(f"✅ Found PDF: {pdf_path}")
                        found = True
                        break
            if found:
                break

        if not found:
            print("❌ No PDF files found. Creating a simple test without PDF...")
            print("\nTesting section extraction logic with mock data instead...")
            test_section_extraction_logic(orchestrator)
            return

    print(f"\n📄 Testing with PDF: {pdf_path}")

    # Run analysis
    paper_metadata = {
        'title': 'Test Paper - Quantum Computing',
        'authors': ['Test Author'],
        'year': 2024
    }

    print("\n⚡ Starting multi-agent analysis...")
    start_time = time.time()

    result = orchestrator.analyze_paper(
        pdf_path=pdf_path,
        paper_metadata=paper_metadata,
        parallel=True,
        max_workers=7
    )

    duration = time.time() - start_time

    # Check results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    if result['success']:
        metrics = result['metrics']
        print(f"\n✅ Analysis completed successfully!")
        print(f"   Total agents: {metrics['total_agents']}")
        print(f"   Successful agents: {metrics['successful_agents']}")
        print(f"   Failed agents: {metrics['failed_agents']}")
        print(f"   Total time: {metrics['total_time']:.2f}s")
        print(f"   Total tokens: {metrics['total_tokens']}")
        print(f"   Estimated cost: ${metrics['estimated_cost']:.4f}")

        # Show which agents succeeded
        print("\n📊 Agent Status:")
        analysis_results = result['analysis_results']
        for agent_name, agent_result in analysis_results.items():
            status = "✅" if agent_result.get('success') else "❌"
            elapsed = agent_result.get('elapsed_time', 0)
            tokens = agent_result.get('tokens_used', 0)
            print(f"   {status} {agent_name}: {elapsed:.2f}s, {tokens} tokens")

        # Final verdict
        print("\n" + "="*80)
        if metrics['successful_agents'] == 7:
            print("🎉 SUCCESS: All 7 agents executed successfully!")
            print("="*80)
            return True
        elif metrics['successful_agents'] >= 5:
            print(f"⚠️  PARTIAL SUCCESS: {metrics['successful_agents']}/7 agents executed")
            print("="*80)
            return False
        else:
            print(f"❌ FAILURE: Only {metrics['successful_agents']}/7 agents executed")
            print("="*80)
            return False
    else:
        print(f"\n❌ Analysis failed: {result.get('message', 'Unknown error')}")
        print(f"   Error: {result.get('error', 'N/A')}")
        return False


def test_section_extraction_logic(orchestrator):
    """Test the section extraction logic with mock page data"""
    print("\n" + "="*80)
    print("Testing Section Extraction Logic")
    print("="*80)

    # Create mock page data (simulating a research paper)
    mock_pages = [
        {'text': 'Abstract: This paper presents a novel approach to quantum computing...', 'page': 1},
        {'text': 'Introduction: Quantum computing has emerged as a promising technology...', 'page': 2},
        {'text': 'Related Work: Previous studies have explored various quantum algorithms...', 'page': 3},
        {'text': 'Methodology: Our approach uses a hybrid quantum-classical framework...', 'page': 4},
        {'text': 'We implement the algorithm using Qiskit and test on IBM quantum computers...', 'page': 5},
        {'text': 'Results: Our experiments show a 30% improvement in gate fidelity...', 'page': 6},
        {'text': 'The results demonstrate significant advantages over classical methods...', 'page': 7},
        {'text': 'Discussion: These findings have important implications for NISQ devices...', 'page': 8},
        {'text': 'Conclusion: We have presented a novel approach that advances the field...', 'page': 9},
    ]

    mock_sections = {
        'Abstract': 'This paper presents a novel approach to quantum computing...',
        'Introduction': 'Quantum computing has emerged as a promising technology...',
        'Related Work': 'Previous studies have explored various quantum algorithms...',
    }

    # Test extraction for each agent
    print("\n📝 Testing section extraction for each agent:")
    for agent_name in orchestrator.agents.keys():
        extracted = orchestrator.extract_section(mock_sections, mock_pages, agent_name)

        if extracted:
            status = "✅"
            preview = extracted[:80] + "..." if len(extracted) > 80 else extracted
        else:
            status = "❌"
            preview = "No content extracted"

        print(f"   {status} {agent_name}: {preview}")

    print("\n" + "="*80)
    print("✅ Section extraction logic test complete!")
    print("="*80)


if __name__ == "__main__":
    success = test_7_agents()
    sys.exit(0 if success else 1)
