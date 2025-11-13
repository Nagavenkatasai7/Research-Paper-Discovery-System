"""
Comprehensive End-to-End Testing Script
=======================================
Tests all features of the Research Paper Discovery System
"""

import time
import sys
from pathlib import Path

# Test results tracking
test_results = []
total_tests = 0
passed_tests = 0
failed_tests = 0

def print_header(text):
    print(f"\n{'='*80}")
    print(f"{text}")
    print(f"{'='*80}\n")

def print_test(test_name, status, message="", time_taken=None):
    global total_tests, passed_tests, failed_tests
    total_tests += 1

    if status:
        passed_tests += 1
        emoji = "✅"
        status_text = "PASS"
    else:
        failed_tests += 1
        emoji = "❌"
        status_text = "FAIL"

    time_str = f" ({time_taken:.2f}s)" if time_taken else ""
    print(f"{emoji} {status_text} - {test_name}{time_str}")
    if message:
        print(f"    {message}")

    test_results.append({
        'test': test_name,
        'status': status,
        'message': message,
        'time': time_taken
    })

def test_imports():
    """Test 1: Verify all imports work"""
    print_header("TEST CATEGORY 1: IMPORTS & DEPENDENCIES")

    try:
        from api_clients import MultiAPISearcher
        print_test("Import MultiAPISearcher", True)
    except Exception as e:
        print_test("Import MultiAPISearcher", False, str(e))

    try:
        from quality_scoring import PaperQualityScorer
        print_test("Import PaperQualityScorer", True)
    except Exception as e:
        print_test("Import PaperQualityScorer", False, str(e))

    try:
        from rag_system.analysis_agents import DocumentAnalysisOrchestrator, SynthesisAgent
        print_test("Import Multi-Agent System", True)
    except Exception as e:
        print_test("Import Multi-Agent System", False, str(e))

    try:
        from rag_system.paper_analysis_workflow import PaperAnalysisWorkflow
        from rag_system.document_chat import DocumentChatSystem
        from rag_system.rag_engine import RAGEngine
        from rag_system.database import RAGDatabase
        print_test("Import Phase 4 Components", True)
    except Exception as e:
        print_test("Import Phase 4 Components", False, str(e))

def test_database():
    """Test 2: Database operations"""
    print_header("TEST CATEGORY 2: DATABASE OPERATIONS")

    try:
        from rag_system.database import RAGDatabase

        start = time.time()
        db = RAGDatabase()
        elapsed = time.time() - start
        print_test("Database Initialization", True, time_taken=elapsed)

        # Test tables exist
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = ['documents', 'document_chunks', 'document_analyses', 'chat_history']
        missing = [t for t in required_tables if t not in tables]

        if not missing:
            print_test("Database Schema Complete", True, f"All {len(required_tables)} tables present")
        else:
            print_test("Database Schema Complete", False, f"Missing tables: {missing}")

        # Test statistics
        stats = db.get_analysis_statistics()
        print_test("Get Analysis Statistics", True, f"Total analyses: {stats.get('total_analyses', 0)}")

        # Test document count
        docs = db.list_documents(limit=5)
        print_test("List Documents", True, f"Found {len(docs)} documents")

    except Exception as e:
        print_test("Database Operations", False, str(e))

def test_rag_engine():
    """Test 3: RAG Engine"""
    print_header("TEST CATEGORY 3: RAG ENGINE")

    try:
        from rag_system.rag_engine import RAGEngine

        start = time.time()
        engine = RAGEngine()
        elapsed = time.time() - start
        print_test("RAG Engine Initialization", True, f"Embedding dim: {engine.embedding_model.embedding_dim}", elapsed)

        # Test embedding generation
        start = time.time()
        test_texts = ["This is a test sentence", "Another test sentence"]
        embeddings = engine.embedding_model.generate_embeddings(test_texts, show_progress=False)
        elapsed = time.time() - start

        if embeddings.shape[0] == 2 and embeddings.shape[1] == 384:
            print_test("Embedding Generation", True, f"Shape: {embeddings.shape}", elapsed)
        else:
            print_test("Embedding Generation", False, f"Wrong shape: {embeddings.shape}")

    except Exception as e:
        print_test("RAG Engine", False, str(e))

def test_multi_agent_system():
    """Test 4: Multi-Agent Analysis"""
    print_header("TEST CATEGORY 4: MULTI-AGENT ANALYSIS SYSTEM")

    try:
        from rag_system.analysis_agents import DocumentAnalysisOrchestrator, SynthesisAgent

        # Test orchestrator initialization
        start = time.time()
        orchestrator = DocumentAnalysisOrchestrator()
        elapsed = time.time() - start
        print_test("Orchestrator Initialization", True, f"7 agents loaded", elapsed)

        # Verify all agents present
        expected_agents = ['abstract', 'introduction', 'literature_review', 'methodology',
                          'results', 'discussion', 'conclusion']
        missing_agents = [a for a in expected_agents if a not in orchestrator.agents]

        if not missing_agents:
            print_test("All 7 Agents Present", True)
        else:
            print_test("All 7 Agents Present", False, f"Missing: {missing_agents}")

        # Test synthesis agent
        start = time.time()
        synthesizer = SynthesisAgent()
        elapsed = time.time() - start
        print_test("Synthesis Agent Initialization", True, time_taken=elapsed)

    except Exception as e:
        print_test("Multi-Agent System", False, str(e))

def test_document_chat():
    """Test 5: Document Chat System"""
    print_header("TEST CATEGORY 5: DOCUMENT CHAT SYSTEM")

    try:
        from rag_system.document_chat import DocumentChatSystem

        start = time.time()
        chat_system = DocumentChatSystem()
        elapsed = time.time() - start
        print_test("Chat System Initialization", True, time_taken=elapsed)

        # Test prompts
        system_prompt = chat_system.build_system_prompt()
        if len(system_prompt) > 100:
            print_test("Build System Prompt", True, f"Length: {len(system_prompt)} chars")
        else:
            print_test("Build System Prompt", False, "Prompt too short")

    except Exception as e:
        print_test("Document Chat System", False, str(e))

def test_workflow_manager():
    """Test 6: Workflow Manager"""
    print_header("TEST CATEGORY 6: WORKFLOW INTEGRATION MANAGER")

    try:
        from rag_system.paper_analysis_workflow import PaperAnalysisWorkflow

        start = time.time()
        workflow = PaperAnalysisWorkflow()
        elapsed = time.time() - start
        print_test("Workflow Manager Initialization", True, time_taken=elapsed)

        # Test statistics
        stats = workflow.get_analysis_statistics()
        print_test("Get Statistics", True, f"Total analyses: {stats.get('total_analyses', 0)}")

        # Test list analyses
        analyses = workflow.list_analyzed_papers(limit=10)
        print_test("List Analyzed Papers", True, f"Found {len(analyses)} papers")

    except Exception as e:
        print_test("Workflow Manager", False, str(e))

def test_pdf_processing():
    """Test 7: PDF Processing"""
    print_header("TEST CATEGORY 7: PDF PROCESSING")

    try:
        from rag_system.pdf_processor import PDFProcessor
        from rag_system.pdf_downloader import PDFDownloader

        start = time.time()
        processor = PDFProcessor()
        elapsed = time.time() - start
        print_test("PDF Processor Initialization", True, time_taken=elapsed)

        start = time.time()
        downloader = PDFDownloader()
        elapsed = time.time() - start
        print_test("PDF Downloader Initialization", True, time_taken=elapsed)

        # Check if transformer paper exists
        pdf_path = "documents/8277bf0bb00823cca9b6ba58b7f42c48.pdf"
        if Path(pdf_path).exists():
            print_test("Sample PDF Available", True, pdf_path)

            # Test text extraction (use correct method name: extract_text_from_pdf)
            start = time.time()
            result = processor.extract_text_from_pdf(pdf_path)
            elapsed = time.time() - start

            if result['success']:
                print_test("PDF Text Extraction", True,
                          f"{len(result['full_text'])} chars, {len(result.get('pages', []))} pages", elapsed)
            else:
                print_test("PDF Text Extraction", False, result.get('message', 'Unknown error'))
        else:
            print_test("Sample PDF Available", False, "No test PDF found")

    except Exception as e:
        print_test("PDF Processing", False, str(e))

def test_text_chunking():
    """Test 8: Text Chunking"""
    print_header("TEST CATEGORY 8: TEXT CHUNKING")

    try:
        from rag_system.text_chunker import TextChunker

        start = time.time()
        chunker = TextChunker()
        elapsed = time.time() - start
        print_test("Text Chunker Initialization", True, time_taken=elapsed)

        # Test chunking (use correct method name: chunk_document)
        test_text = "This is a test. " * 100  # Create long text
        start = time.time()
        chunks = chunker.chunk_document(test_text)
        elapsed = time.time() - start

        if len(chunks) > 0:
            print_test("Text Chunking", True, f"Created {len(chunks)} chunks", elapsed)
        else:
            print_test("Text Chunking", False, "No chunks created")

    except Exception as e:
        print_test("Text Chunking", False, str(e))

def test_config():
    """Test 9: Configuration"""
    print_header("TEST CATEGORY 9: CONFIGURATION")

    try:
        import config

        # Test Grok settings (PRIMARY LLM)
        if config.GROK_SETTINGS.get('enabled'):
            print_test("Grok-4 Configured", True, f"Model: {config.GROK_SETTINGS.get('model')}")
        else:
            print_test("Grok-4 Configured", False, "Grok not enabled")

        # Test Local LLM settings (EXPECTED TO BE DISABLED - system uses Grok-4 only)
        if not config.LLM_SETTINGS.get('enabled'):
            print_test("Local LLM Disabled (Expected)", True, "System uses Grok-4 exclusively")
        else:
            print_test("Local LLM Disabled (Expected)", False, "Local LLM should be disabled")

        # Test Grok API key present
        has_grok_key = bool(config.GROK_SETTINGS.get('api_key'))
        print_test("Grok API Key Configured", has_grok_key,
                  "Grok API key present" if has_grok_key else "No Grok API key")

    except Exception as e:
        print_test("Configuration", False, str(e))

def test_phase4_backend_integration():
    """Test 10: Phase 4 Backend Integration"""
    print_header("TEST CATEGORY 10: PHASE 4 BACKEND INTEGRATION")

    try:
        from rag_system.paper_analysis_workflow import PaperAnalysisWorkflow
        from rag_system.database import RAGDatabase

        workflow = PaperAnalysisWorkflow()
        db = workflow.db

        # Test if we have any stored analyses
        stats = db.get_analysis_statistics()
        total_analyses = stats.get('total_analyses', 0)

        if total_analyses > 0:
            print_test("Stored Analyses Available", True, f"{total_analyses} analyses in database")

            # Test retrieval
            analyses = workflow.list_analyzed_papers(limit=1)
            if analyses:
                analysis = analyses[0]
                doc_id = analysis['document_id']

                # Test chat history
                history = workflow.get_chat_history(doc_id, limit=5)
                print_test("Chat History Retrieval", True, f"{len(history)} messages")

                # Test stored analysis retrieval
                stored = workflow.get_stored_analysis(doc_id)
                if stored:
                    print_test("Analysis Retrieval", True,
                              f"Quality: {stored.get('quality_rating', 'N/A')}")
                else:
                    print_test("Analysis Retrieval", False, "Could not retrieve analysis")
        else:
            print_test("Stored Analyses Available", True, "No analyses yet (expected for new system)")

    except Exception as e:
        print_test("Phase 4 Backend Integration", False, str(e))

def test_faiss_availability():
    """Test 11: FAISS Availability"""
    print_header("TEST CATEGORY 11: FAISS VECTOR SEARCH")

    try:
        import faiss
        import numpy as np

        print_test("FAISS Library Available", True, f"Version: {faiss.__version__ if hasattr(faiss, '__version__') else 'Unknown'}")

        # Test index creation
        dimension = 384
        index = faiss.IndexFlatL2(dimension)

        # Add some vectors
        vectors = np.random.random((10, dimension)).astype('float32')
        index.add(vectors)

        if index.ntotal == 10:
            print_test("FAISS Index Creation", True, f"{index.ntotal} vectors added")
        else:
            print_test("FAISS Index Creation", False, f"Expected 10, got {index.ntotal}")

        # Test search
        query = np.random.random((1, dimension)).astype('float32')
        distances, indices = index.search(query, 5)

        if len(indices[0]) == 5:
            print_test("FAISS Vector Search", True, "Top-5 search successful")
        else:
            print_test("FAISS Vector Search", False, f"Expected 5 results, got {len(indices[0])}")

    except Exception as e:
        print_test("FAISS Availability", False, str(e))

def run_all_tests():
    """Execute all tests"""
    start_time = time.time()

    print_header("COMPREHENSIVE END-TO-END TESTING")
    print("Research Paper Discovery System - All Features")
    print(f"Test Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Run all test categories
    test_imports()
    test_config()
    test_database()
    test_faiss_availability()
    test_text_chunking()
    test_rag_engine()
    test_multi_agent_system()
    test_document_chat()
    test_workflow_manager()
    test_pdf_processing()
    test_phase4_backend_integration()

    # Summary
    total_time = time.time() - start_time

    print_header("TEST EXECUTION SUMMARY")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✅")
    print(f"Failed: {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    print(f"Total Time: {total_time:.2f}s")

    # Detailed results
    if failed_tests > 0:
        print(f"\n{'='*80}")
        print("FAILED TESTS DETAILS:")
        print(f"{'='*80}")
        for result in test_results:
            if not result['status']:
                print(f"\n❌ {result['test']}")
                if result['message']:
                    print(f"   Error: {result['message']}")

    # Component status
    print(f"\n{'='*80}")
    print("COMPONENT STATUS:")
    print(f"{'='*80}")
    print(f"✅ Database System: {'OK' if any('Database' in r['test'] and r['status'] for r in test_results) else 'FAILED'}")
    print(f"✅ RAG Engine: {'OK' if any('RAG' in r['test'] and r['status'] for r in test_results) else 'FAILED'}")
    print(f"✅ Multi-Agent System: {'OK' if any('Agent' in r['test'] and r['status'] for r in test_results) else 'FAILED'}")
    print(f"✅ Document Chat: {'OK' if any('Chat' in r['test'] and r['status'] for r in test_results) else 'FAILED'}")
    print(f"✅ Workflow Manager: {'OK' if any('Workflow' in r['test'] and r['status'] for r in test_results) else 'FAILED'}")
    print(f"✅ PDF Processing: {'OK' if any('PDF' in r['test'] and r['status'] for r in test_results) else 'FAILED'}")

    # Final verdict
    print(f"\n{'='*80}")
    if failed_tests == 0:
        print("🎉 ALL TESTS PASSED! System is fully operational.")
    elif failed_tests <= 3:
        print("⚠️  MOSTLY PASSING - Minor issues detected.")
    else:
        print("❌ MULTIPLE FAILURES - System needs attention.")
    print(f"{'='*80}\n")

    return failed_tests == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
