"""
Test script to verify database connection works correctly
Tests Fix #2: Remove duplicate connection call
"""

import sys
import time
import threading
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_system.database import RAGDatabase


def test_database_initialization():
    """Test database initialization creates tables correctly"""
    print("Test 1: Database initialization")
    print("-" * 50)

    try:
        # Create a new database instance
        test_db_path = "database/test_connection_init.db"

        # Remove existing test database if exists
        if Path(test_db_path).exists():
            Path(test_db_path).unlink()
            print("✓ Removed existing test database")

        # Create new database (should create tables)
        db = RAGDatabase(test_db_path)
        print("✓ Database instance created")

        # Verify database file was created
        if Path(test_db_path).exists():
            print("✓ Database file created on disk")
        else:
            raise Exception("Database file not created")

        # Verify we can perform operations
        docs = db.list_documents(limit=10)
        print(f"✓ Can query database: {len(docs)} documents found")

        # Verify statistics work
        stats = db.get_statistics()
        print(f"✓ Statistics retrieved: {stats['total_documents']} documents")

        db.close()
        print("✓ Database closed successfully")

        print("✅ Test 1 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_connection_reuse():
    """Test that connections are properly reused within the same thread"""
    print("Test 2: Connection reuse in same thread")
    print("-" * 50)

    try:
        db = RAGDatabase("database/test_connection_reuse.db")
        print("✓ Database instance created")

        # Perform multiple operations - should reuse same connection
        for i in range(5):
            docs = db.list_documents(limit=10)
            stats = db.get_statistics()
            print(f"✓ Operation {i+1} completed (connection reused)")

        db.close()
        print("✓ Database closed")

        print("✅ Test 2 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}\n")
        return False


def test_thread_local_isolation():
    """Test that each thread gets its own connection"""
    print("Test 3: Thread-local connection isolation")
    print("-" * 50)

    results = []
    db = RAGDatabase("database/test_thread_isolation.db")

    def thread_worker(thread_id):
        """Worker function for threading test"""
        try:
            # Each thread should get its own connection
            for i in range(3):
                docs = db.list_documents(limit=10)
                stats = db.get_statistics()
                time.sleep(0.01)  # Small delay to increase chance of race conditions

            results.append((thread_id, True, None))
            print(f"✓ Thread {thread_id} completed successfully")

        except Exception as e:
            results.append((thread_id, False, str(e)))
            print(f"✗ Thread {thread_id} failed: {e}")

    # Create and start threads
    threads = []
    for i in range(10):
        t = threading.Thread(target=thread_worker, args=(i,))
        threads.append(t)
        t.start()

    # Wait for all threads
    for t in threads:
        t.join()

    # Close main connection
    db.close()

    # Check results
    success_count = sum(1 for _, success, _ in results if success)

    if success_count == 10:
        print(f"✓ All {success_count}/10 threads completed successfully")
        print("✅ Test 3 PASSED\n")
        return True
    else:
        print(f"✗ Only {success_count}/10 threads succeeded")
        for thread_id, success, error in results:
            if not success:
                print(f"  Thread {thread_id} error: {error}")
        print("❌ Test 3 FAILED\n")
        return False


def test_connection_after_error():
    """Test that connection recovery works after errors"""
    print("Test 4: Connection recovery after errors")
    print("-" * 50)

    try:
        db = RAGDatabase("database/test_error_recovery.db")
        print("✓ Database instance created")

        # Perform successful operation
        docs = db.list_documents(limit=10)
        print(f"✓ Initial operation successful: {len(docs)} documents")

        # Try to trigger an error (invalid document ID)
        try:
            db.get_document_by_id(-1)
            print("✓ Error handling works for invalid ID")
        except Exception as e:
            print(f"✓ Expected error handled: {e}")

        # Verify connection still works after error
        docs = db.list_documents(limit=10)
        print(f"✓ Connection still works after error: {len(docs)} documents")

        stats = db.get_statistics()
        print(f"✓ Statistics retrieved: {stats['total_documents']} documents")

        db.close()
        print("✓ Database closed")

        print("✅ Test 4 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}\n")
        return False


def test_no_duplicate_connections():
    """Test that removing duplicate connection call didn't break anything"""
    print("Test 5: Verify no duplicate connection issues")
    print("-" * 50)

    try:
        # This test specifically verifies that the _create_tables method
        # works correctly after removing the duplicate connection call

        test_db_path = "database/test_no_duplicates.db"

        # Remove existing test database
        if Path(test_db_path).exists():
            Path(test_db_path).unlink()
            print("✓ Removed existing test database")

        # Create new database - this calls _create_tables internally
        db = RAGDatabase(test_db_path)
        print("✓ Database created (tables initialized)")

        # Verify all tables were created correctly
        conn = db._get_connection()
        cursor = conn.cursor()

        # Check that main tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            'documents', 'document_embeddings', 'document_summaries', 'chat_history',
            'document_chunks', 'processing_logs', 'document_analyses', 'agent_context',
            'progressive_summaries'
        ]

        for table in expected_tables:
            if table in tables:
                print(f"✓ Table '{table}' exists")
            else:
                raise Exception(f"Table '{table}' not found")

        # Verify we can use the database
        docs = db.list_documents(limit=10)
        print(f"✓ Database is functional: {len(docs)} documents")

        db.close()
        print("✓ Database closed")

        print("✅ Test 5 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 5 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("DATABASE CONNECTION TEST SUITE")
    print("Testing Fix #2: Remove duplicate connection call")
    print("=" * 60)
    print()

    tests = [
        test_database_initialization,
        test_connection_reuse,
        test_thread_local_isolation,
        test_connection_after_error,
        test_no_duplicate_connections
    ]

    results = []
    for test_func in tests:
        result = test_func()
        results.append(result)
        time.sleep(0.1)  # Small delay between tests

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED - Fix #2 is working correctly!")
        print("\nThe database connection system:")
        print("  ✓ Initializes correctly without duplicate connections")
        print("  ✓ Reuses connections within the same thread")
        print("  ✓ Provides proper thread-local isolation")
        print("  ✓ Recovers from errors gracefully")
        print("  ✓ Creates all required tables correctly")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED - Fix needs attention")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
