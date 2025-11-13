"""
Test script to verify database close() method works correctly
Tests Fix #1: Database close() method error
"""

import sys
import threading
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_system.database import RAGDatabase


def test_basic_close():
    """Test basic close() functionality"""
    print("Test 1: Basic close() functionality")
    print("-" * 50)

    try:
        # Create database instance
        db = RAGDatabase("database/test_close.db")
        print("✓ Database instance created")

        # Perform a simple operation
        documents = db.list_documents(limit=10)
        print(f"✓ Listed documents: {len(documents)} found")

        # Close the database
        db.close()
        print("✓ Database closed without errors")

        print("✅ Test 1 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}\n")
        return False


def test_multiple_close():
    """Test calling close() multiple times"""
    print("Test 2: Multiple close() calls")
    print("-" * 50)

    try:
        db = RAGDatabase("database/test_close.db")
        print("✓ Database instance created")

        # Close multiple times - should not error
        db.close()
        print("✓ First close() successful")

        db.close()
        print("✓ Second close() successful (idempotent)")

        db.close()
        print("✓ Third close() successful (idempotent)")

        print("✅ Test 2 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}\n")
        return False


def test_thread_local_close():
    """Test close() with thread-local connections"""
    print("Test 3: Thread-local close() functionality")
    print("-" * 50)

    results = []

    def thread_worker(thread_id):
        """Worker function for threading test"""
        try:
            db = RAGDatabase("database/test_close.db")

            # Perform operation
            documents = db.list_documents(limit=10)

            # Close connection
            db.close()

            results.append((thread_id, True, None))
            print(f"✓ Thread {thread_id} completed successfully")

        except Exception as e:
            results.append((thread_id, False, str(e)))
            print(f"✗ Thread {thread_id} failed: {e}")

    # Create and start threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=thread_worker, args=(i,))
        threads.append(t)
        t.start()

    # Wait for all threads
    for t in threads:
        t.join()

    # Check results
    success_count = sum(1 for _, success, _ in results if success)

    if success_count == 5:
        print(f"✓ All {success_count}/5 threads closed successfully")
        print("✅ Test 3 PASSED\n")
        return True
    else:
        print(f"✗ Only {success_count}/5 threads succeeded")
        for thread_id, success, error in results:
            if not success:
                print(f"  Thread {thread_id} error: {error}")
        print("❌ Test 3 FAILED\n")
        return False


def test_close_and_reopen():
    """Test that database can be reopened after close"""
    print("Test 4: Close and reopen database")
    print("-" * 50)

    try:
        db = RAGDatabase("database/test_close.db")
        print("✓ Database opened first time")

        # Perform operation
        documents = db.list_documents(limit=10)
        print(f"✓ Listed documents: {len(documents)}")

        # Close
        db.close()
        print("✓ Database closed")

        # Try to perform operation after close (should create new connection)
        documents = db.list_documents(limit=10)
        print(f"✓ Listed documents after close: {len(documents)}")

        # Close again
        db.close()
        print("✓ Database closed again")

        print("✅ Test 4 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}\n")
        return False


def test_close_without_operations():
    """Test close() immediately after creation"""
    print("Test 5: Close without any operations")
    print("-" * 50)

    try:
        db = RAGDatabase("database/test_close.db")
        print("✓ Database instance created")

        # Close immediately without any operations
        db.close()
        print("✓ Database closed without prior operations")

        print("✅ Test 5 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 5 FAILED: {e}\n")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("DATABASE CLOSE() METHOD TEST SUITE")
    print("Testing Fix #1: Database close() method error")
    print("=" * 60)
    print()

    tests = [
        test_basic_close,
        test_multiple_close,
        test_thread_local_close,
        test_close_and_reopen,
        test_close_without_operations
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
        print("\n✅ ALL TESTS PASSED - Fix #1 is working correctly!")
        print("\nThe database close() method:")
        print("  ✓ Works without errors")
        print("  ✓ Is idempotent (can be called multiple times)")
        print("  ✓ Handles thread-local connections properly")
        print("  ✓ Allows database to be reopened after close")
        print("  ✓ Works even without prior operations")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED - Fix needs attention")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
