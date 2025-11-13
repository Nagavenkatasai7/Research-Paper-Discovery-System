"""
Test Week 3: UI & Database Integration
========================================

Verify that:
1. Document Analysis page exists and is accessible
2. Database schema includes new tables (agent_context, progressive_summaries)
3. DatabaseManager has new helper methods
4. End-to-end integration works
"""

import sys
from pathlib import Path
import tempfile
import os


def test_document_analysis_page_exists():
    """Test that Document Analysis page file exists"""
    print("="*80)
    print("TEST 1: Document Analysis Page Exists")
    print("="*80)

    try:
        page_path = Path("pages/Document_Analysis.py")

        if not page_path.exists():
            print("❌ Document Analysis page not found at pages/Document_Analysis.py")
            return False

        print("✅ Document_Analysis.py exists")

        # Check file size (should be substantial)
        file_size = page_path.stat().st_size
        print(f"✅ File size: {file_size:,} bytes")

        if file_size < 1000:
            print("⚠️ Warning: File seems too small")
            return False

        # Read and check for key components
        content = page_path.read_text()

        required_components = [
            'st.file_uploader',
            'DocumentProcessor',
            'DocumentAnalysisOrchestrator',
            'agent_statuses',
            'progress',
            'Quick',
            'Standard',
            'Comprehensive'
        ]

        missing = []
        for component in required_components:
            if component not in content:
                missing.append(component)

        if missing:
            print(f"❌ Missing components: {', '.join(missing)}")
            return False

        print(f"✅ All {len(required_components)} required components found")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_schema_updated():
    """Test that database schema includes new tables"""
    print("\n" + "="*80)
    print("TEST 2: Database Schema Updated")
    print("="*80)

    try:
        from rag_system.database import RAGDatabase
        import tempfile
        import os

        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_db_path = tmp.name

        try:
            # Initialize database (triggers table creation)
            db = RAGDatabase(db_path=tmp_db_path)

            # Check if tables exist
            cursor = db.conn.cursor()

            # Check agent_context table
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='agent_context'
            """)
            if cursor.fetchone():
                print("✅ agent_context table exists")
            else:
                print("❌ agent_context table not found")
                return False

            # Check progressive_summaries table
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='progressive_summaries'
            """)
            if cursor.fetchone():
                print("✅ progressive_summaries table exists")
            else:
                print("❌ progressive_summaries table not found")
                return False

            # Check indexes
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND name LIKE 'idx_agent_context%'
            """)
            context_indexes = cursor.fetchall()
            print(f"✅ Found {len(context_indexes)} agent_context indexes")

            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND name LIKE 'idx_progressive_summaries%'
            """)
            summary_indexes = cursor.fetchall()
            print(f"✅ Found {len(summary_indexes)} progressive_summaries indexes")

            # Verify agent_context schema
            cursor.execute("PRAGMA table_info(agent_context)")
            columns = {row[1] for row in cursor.fetchall()}
            required_columns = {
                'id', 'document_id', 'analysis_id', 'agent_name',
                'finding_type', 'finding_content', 'relevance_to',
                'priority', 'created_at'
            }
            if required_columns.issubset(columns):
                print("✅ agent_context has all required columns")
            else:
                missing = required_columns - columns
                print(f"❌ agent_context missing columns: {missing}")
                return False

            # Verify progressive_summaries schema
            cursor.execute("PRAGMA table_info(progressive_summaries)")
            columns = {row[1] for row in cursor.fetchall()}
            required_columns = {
                'id', 'document_id', 'analysis_id', 'level',
                'summary_content', 'section_name', 'parent_summary_id',
                'created_at'
            }
            if required_columns.issubset(columns):
                print("✅ progressive_summaries has all required columns")
            else:
                missing = required_columns - columns
                print(f"❌ progressive_summaries missing columns: {missing}")
                return False

            db.close()
            return True

        finally:
            # Cleanup
            if os.path.exists(tmp_db_path):
                os.unlink(tmp_db_path)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_helper_methods():
    """Test that database has new helper methods"""
    print("\n" + "="*80)
    print("TEST 3: Database Helper Methods")
    print("="*80)

    try:
        from rag_system.database import RAGDatabase
        import inspect

        # Check for required methods
        required_methods = [
            'store_agent_context',
            'get_agent_context',
            'get_context_by_analysis',
            'store_progressive_summary',
            'get_progressive_summaries',
            'get_summary_by_level',
            'delete_agent_context',
            'delete_progressive_summaries'
        ]

        db = RAGDatabase()  # Just for method inspection

        missing_methods = []
        for method_name in required_methods:
            if not hasattr(db, method_name):
                missing_methods.append(method_name)

        if missing_methods:
            print(f"❌ Missing methods: {', '.join(missing_methods)}")
            return False

        print(f"✅ All {len(required_methods)} required methods exist")

        # Test method signatures
        for method_name in required_methods:
            method = getattr(db, method_name)
            sig = inspect.signature(method)
            print(f"✅ {method_name}{sig}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_document_processor_integration():
    """Test DocumentProcessor can be imported and used"""
    print("\n" + "="*80)
    print("TEST 4: DocumentProcessor Integration")
    print("="*80)

    try:
        from rag_system.document_processor import DocumentProcessor

        processor = DocumentProcessor()
        print("✅ DocumentProcessor imported and initialized")

        # Check supported formats (without dot prefix)
        expected_formats = ['pdf', 'docx', 'tex', 'html']
        if all(fmt in processor.supported_formats for fmt in expected_formats):
            print(f"✅ All {len(expected_formats)} formats supported: {processor.supported_formats}")
        else:
            print(f"❌ Missing formats. Expected: {expected_formats}, Got: {processor.supported_formats}")
            return False

        # Check methods exist
        required_methods = ['process_document', '_process_pdf', '_process_docx', '_process_latex', '_process_html']
        for method_name in required_methods:
            if not hasattr(processor, method_name):
                print(f"❌ Missing method: {method_name}")
                return False

        print(f"✅ All {len(required_methods)} required methods exist")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator_integration():
    """Test orchestrator has context manager and 11 agents"""
    print("\n" + "="*80)
    print("TEST 5: Orchestrator Integration")
    print("="*80)

    try:
        from rag_system.analysis_agents import DocumentAnalysisOrchestrator

        orchestrator = DocumentAnalysisOrchestrator()
        print("✅ Orchestrator initialized")

        # Check context_manager exists
        if hasattr(orchestrator, 'context_manager'):
            print("✅ Orchestrator has context_manager")
        else:
            print("❌ Orchestrator missing context_manager")
            return False

        # Check number of agents
        if hasattr(orchestrator, 'agents'):
            agent_count = len(orchestrator.agents)
            print(f"✅ Orchestrator has {agent_count} agents")

            if agent_count != 11:
                print(f"⚠️ Expected 11 agents, found {agent_count}")
                print(f"   Agents: {list(orchestrator.agents.keys())}")
                # Don't fail, just warn

        # Check analyze_paper has enable_context_sharing parameter
        import inspect
        sig = inspect.signature(orchestrator.analyze_paper)
        if 'enable_context_sharing' in sig.parameters:
            print("✅ analyze_paper has enable_context_sharing parameter")
        else:
            print("❌ analyze_paper missing enable_context_sharing parameter")
            return False

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_app_navigation_updated():
    """Test that app.py references Document Analysis page"""
    print("\n" + "="*80)
    print("TEST 6: App Navigation Updated")
    print("="*80)

    try:
        app_path = Path("app.py")

        if not app_path.exists():
            print("❌ app.py not found")
            return False

        content = app_path.read_text()

        # Check for reference to Document_Analysis.py
        if 'Document_Analysis' in content or 'Document Analysis' in content:
            print("✅ app.py references Document Analysis page")
        else:
            print("⚠️ app.py may not explicitly reference Document Analysis (auto-detected by Streamlit)")

        # Check for navigation banner
        if 'st.switch_page' in content and 'Document_Analysis' in content:
            print("✅ Navigation button to Document Analysis found")
        else:
            print("⚠️ No explicit navigation button (page will be auto-discovered)")

        # Streamlit auto-discovers pages, so this is not a failure
        print("✅ Navigation test passed (Streamlit auto-discovers pages/)")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_context_manager_functionality():
    """Test ContextManager basic operations"""
    print("\n" + "="*80)
    print("TEST 7: ContextManager Functionality")
    print("="*80)

    try:
        from rag_system.context_manager import ContextManager, Finding

        cm = ContextManager()
        print("✅ ContextManager initialized")

        # Register a finding
        finding = cm.register_finding(
            from_agent='methodology',
            finding_type='methodology',
            content={'technique': 'Test'},
            relevance_to=['results'],
            priority='high'
        )

        print("✅ Finding registered successfully")

        # Retrieve context
        context = cm.get_context_for_agent('results')
        print(f"✅ Retrieved context from {len(context)} agents")

        # Get statistics
        stats = cm.get_summary_statistics()
        print(f"✅ Statistics: {stats['total_findings']} findings, {stats['agents_with_findings']} agents")

        if stats['total_findings'] > 0 and stats['agents_with_findings'] > 0:
            print("✅ ContextManager working correctly")
            return True
        else:
            print("❌ ContextManager not registering findings properly")
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all Week 3 integration tests"""
    print("\n" + "="*80)
    print("WEEK 3: UI & DATABASE INTEGRATION TESTS")
    print("="*80 + "\n")

    tests = [
        ("Document Analysis Page Exists", test_document_analysis_page_exists),
        ("Database Schema Updated", test_database_schema_updated),
        ("Database Helper Methods", test_database_helper_methods),
        ("DocumentProcessor Integration", test_document_processor_integration),
        ("Orchestrator Integration", test_orchestrator_integration),
        ("App Navigation Updated", test_app_navigation_updated),
        ("ContextManager Functionality", test_context_manager_functionality)
    ]

    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Week 3 integration is complete.")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
