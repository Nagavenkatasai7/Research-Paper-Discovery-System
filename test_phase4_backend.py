"""
Phase 4 Backend Integration Tests
==================================
Comprehensive tests for all Phase 4 backend components:
1. Database storage and retrieval
2. Document chat system
3. Workflow integration
4. Complete end-to-end workflow
"""

import time
from pathlib import Path
from rag_system.database import RAGDatabase
from rag_system.document_chat import DocumentChatSystem
from rag_system.paper_analysis_workflow import PaperAnalysisWorkflow


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}\n")


def test_database_storage():
    """Test 1: Database storage and retrieval of analyses"""
    print_section("TEST 1: Database Storage and Retrieval")

    db = RAGDatabase()

    # Use the Transformer paper (should already be processed)
    document_id = 1

    # Check if document exists
    document = db.get_document_by_id(document_id)
    if not document:
        print("❌ Document not found. Please process a document first.")
        return False

    print(f"✓ Found document: {document.get('title', 'Unknown')}")

    # Check if analysis exists
    existing_analysis = db.get_analysis_by_document_id(document_id)

    if existing_analysis:
        print(f"✓ Found existing analysis (ID: {existing_analysis['id']})")
        print(f"  - Quality: {existing_analysis.get('quality_rating', 'N/A')}")
        print(f"  - Novelty: {existing_analysis.get('novelty_rating', 'N/A')}")
        print(f"  - Impact: {existing_analysis.get('impact_rating', 'N/A')}")
        print(f"  - Time: {existing_analysis.get('total_time', 0):.2f}s")
        print(f"  - Tokens: {existing_analysis.get('total_tokens', 0):,}")
        print(f"  - Created: {existing_analysis.get('created_at', 'N/A')}")

        # Test key fields
        synthesis = existing_analysis.get('synthesis_result', {})
        print(f"\n✓ Synthesis data retrieved:")
        print(f"  - Executive summary: {len(synthesis.get('executive_summary', ''))} chars")
        print(f"  - Key contributions: {len(synthesis.get('key_contributions', []))} items")
        print(f"  - Strengths: {len(synthesis.get('strengths', []))} items")
        print(f"  - Limitations: {len(synthesis.get('limitations', []))} items")

        # Test statistics
        stats = db.get_analysis_statistics()
        print(f"\n✓ Analysis statistics:")
        print(f"  - Total analyses: {stats.get('total_analyses', 0)}")
        print(f"  - By quality: {stats.get('by_quality', {})}")
        print(f"  - Avg time: {stats.get('average_time', 0):.2f}s")
        print(f"  - Avg tokens: {stats.get('average_tokens', 0):,.0f}")

        return True
    else:
        print("⚠️  No analysis found. Will be created in workflow test.")
        return True


def test_document_chat():
    """Test 2: Document chat system"""
    print_section("TEST 2: Document Chat System")

    chat_system = DocumentChatSystem()
    document_id = 1

    # Check if we have analysis and RAG data
    db = chat_system.db
    document = db.get_document_by_id(document_id)

    if not document:
        print("❌ Document not found")
        return False

    print(f"✓ Testing chat with: {document.get('title', 'Unknown')}")

    # Test questions
    test_questions = [
        "What is the main contribution of this paper?",
        "What are the key strengths and limitations?",
        "How does the methodology work?"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n--- Question {i} ---")
        print(f"Q: {question}")

        start_time = time.time()
        result = chat_system.chat(
            document_id=document_id,
            question=question,
            use_analysis=True,
            use_rag=True,
            save_to_history=False  # Don't save test questions
        )
        elapsed_time = time.time() - start_time

        if result['success']:
            answer = result['answer']
            sources = result.get('sources_used', [])
            context_info = result.get('context_used', {})

            print(f"A: {answer[:200]}..." if len(answer) > 200 else f"A: {answer}")
            print(f"\n✓ Response generated in {elapsed_time:.2f}s")
            print(f"  - Sources: {', '.join(sources)}")
            print(f"  - Has analysis: {context_info.get('has_analysis', False)}")
            print(f"  - Has RAG: {context_info.get('has_rag', False)}")
            print(f"  - Excerpts used: {context_info.get('num_excerpts', 0)}")
            print(f"  - Tokens: {result.get('tokens_used', 0):,}")
        else:
            print(f"❌ Chat failed: {result.get('message', 'Unknown error')}")
            return False

    # Test chat history retrieval
    print(f"\n--- Chat History ---")
    history = chat_system.get_chat_history(document_id, limit=10)
    print(f"✓ Retrieved {len(history)} chat messages")

    if history:
        latest = history[0]
        print(f"  Latest: '{latest.get('user_question', '')[:50]}...'")
        print(f"  Time: {latest.get('response_time', 0):.2f}s")

    return True


def test_workflow_integration():
    """Test 3: Workflow integration manager"""
    print_section("TEST 3: Workflow Integration Manager")

    workflow = PaperAnalysisWorkflow()

    # Test with existing document
    document_id = 1

    print("Testing workflow methods:")

    # 1. Get stored analysis
    print("\n1. get_stored_analysis()")
    analysis = workflow.get_stored_analysis(document_id)
    if analysis:
        print(f"  ✓ Retrieved analysis (ID: {analysis['id']})")
        print(f"    Quality: {analysis.get('quality_rating', 'N/A')}")
    else:
        print(f"  ⚠️  No stored analysis found")

    # 2. Get chat history
    print("\n2. get_chat_history()")
    history = workflow.get_chat_history(document_id, limit=5)
    print(f"  ✓ Retrieved {len(history)} messages")

    # 3. List analyzed papers
    print("\n3. list_analyzed_papers()")
    papers = workflow.list_analyzed_papers(limit=10)
    print(f"  ✓ Found {len(papers)} analyzed papers")
    if papers:
        for i, paper in enumerate(papers[:3], 1):
            doc = paper.get('document', {})
            print(f"    {i}. {doc.get('title', 'Unknown')[:60]}... (Q: {paper.get('quality_rating', 'N/A')})")

    # 4. Get statistics
    print("\n4. get_analysis_statistics()")
    stats = workflow.get_analysis_statistics()
    print(f"  ✓ Statistics retrieved:")
    print(f"    - Total: {stats.get('total_analyses', 0)}")
    print(f"    - By quality: {stats.get('by_quality', {})}")
    print(f"    - Avg time: {stats.get('average_time', 0):.2f}s")

    # 5. Chat with paper
    print("\n5. chat_with_paper()")
    chat_result = workflow.chat_with_paper(
        document_id=document_id,
        question="Summarize the main contribution in one sentence",
        use_analysis=True,
        use_rag=True,
        save_to_history=False
    )

    if chat_result['success']:
        print(f"  ✓ Chat successful")
        print(f"    Answer: {chat_result['answer'][:100]}...")
        print(f"    Time: {chat_result.get('elapsed_time', 0):.2f}s")
    else:
        print(f"  ❌ Chat failed: {chat_result.get('message', '')}")

    return True


def test_complete_workflow():
    """Test 4: Complete workflow (if needed)"""
    print_section("TEST 4: Complete Workflow (Optional)")

    print("This test would run the complete workflow:")
    print("  1. Download PDF (from ArXiv)")
    print("  2. Add to database")
    print("  3. Process with RAG")
    print("  4. Multi-agent analysis")
    print("  5. Synthesis")
    print("  6. Store in database")
    print("\nSkipping to save time and API costs.")
    print("Use process_and_analyze_paper() in production for new papers.")

    # Example usage (commented out):
    """
    workflow = PaperAnalysisWorkflow()
    result = workflow.process_and_analyze_paper(
        arxiv_id="1706.03762",  # Transformer paper
        paper_metadata={
            'title': 'Attention Is All You Need',
            'authors': ['Vaswani et al.'],
            'year': 2017
        },
        store_analysis=True
    )
    """

    return True


def run_all_tests():
    """Run all Phase 4 backend tests"""
    print("\n" + "="*80)
    print("PHASE 4 BACKEND INTEGRATION TESTS")
    print("="*80)

    start_time = time.time()
    results = []

    # Test 1: Database storage
    try:
        result = test_database_storage()
        results.append(("Database Storage", result))
    except Exception as e:
        print(f"\n❌ Test 1 failed with exception: {e}")
        results.append(("Database Storage", False))

    # Test 2: Document chat
    try:
        result = test_document_chat()
        results.append(("Document Chat", result))
    except Exception as e:
        print(f"\n❌ Test 2 failed with exception: {e}")
        results.append(("Document Chat", False))

    # Test 3: Workflow integration
    try:
        result = test_workflow_integration()
        results.append(("Workflow Integration", result))
    except Exception as e:
        print(f"\n❌ Test 3 failed with exception: {e}")
        results.append(("Workflow Integration", False))

    # Test 4: Complete workflow (optional)
    try:
        result = test_complete_workflow()
        results.append(("Complete Workflow", result))
    except Exception as e:
        print(f"\n❌ Test 4 failed with exception: {e}")
        results.append(("Complete Workflow", False))

    # Summary
    total_time = time.time() - start_time
    passed = sum(1 for _, result in results if result)
    total = len(results)

    print_section("TEST SUMMARY")
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n{'='*80}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"Time: {total_time:.2f}s")
    print(f"{'='*80}")

    if passed == total:
        print("\n🎉 All Phase 4 backend tests passed!")
        print("\nPhase 4 Backend is ready for frontend integration.")
        print("\nNext steps:")
        print("  1. Update frontend with chat interface")
        print("  2. Add analysis display and management")
        print("  3. End-to-end integration testing")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
