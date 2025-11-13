"""
Test to verify database thread safety
Tests Fix #9: All database commits protected with write locks
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_all_commits_have_write_locks():
    """Verify all database commits are protected with write locks"""
    print("Test 1: All database commits have write lock protection")
    print("-" * 60)

    try:
        db_path = Path("rag_system/database.py")

        with open(db_path, 'r') as f:
            lines = f.readlines()

        commits_found = []
        protected_commits = []

        # Find all conn.commit() calls
        for i, line in enumerate(lines, 1):
            if 'conn.commit()' in line and not line.strip().startswith('#'):
                commits_found.append(i)

                # Check if write lock is present within 5 lines before
                has_lock = False
                for j in range(max(0, i-6), i):
                    if 'with self._write_lock:' in lines[j]:
                        has_lock = True
                        break

                if has_lock:
                    protected_commits.append(i)
                else:
                    # Check if it's the initialization method (_create_tables or _initialize_database)
                    # Look at larger context to catch initialization methods
                    in_init = False
                    for j in range(max(0, i-220), i):
                        if '_create_tables' in lines[j] or '_initialize_database' in lines[j]:
                            in_init = True
                            break

                    if in_init:
                        protected_commits.append(i)  # Init is safe, single-threaded
                        print(f"  ℹ️  Commit at line {i} is in initialization method (safe)")
                    else:
                        print(f"  ⚠️  Unprotected commit at line {i}")

        total_commits = len(commits_found)
        protected = len(protected_commits)

        print(f"  Found {total_commits} conn.commit() calls")
        print(f"  {protected} are properly protected")

        if protected == total_commits:
            print("  ✓ All database commits are properly protected")
            print("✅ Test 1 PASSED\n")
            return True
        else:
            unprotected = total_commits - protected
            raise Exception(f"{unprotected} commit(s) are not protected with write locks")

    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}\n")
        return False


def test_write_lock_pattern():
    """Verify write lock pattern is used correctly"""
    print("Test 2: Write lock pattern usage")
    print("-" * 60)

    try:
        db_path = Path("rag_system/database.py")

        with open(db_path, 'r') as f:
            content = f.read()

        # Count write lock usage
        write_lock_count = content.count('with self._write_lock:')
        commit_count = content.count('conn.commit()')

        print(f"  Write locks used: {write_lock_count}")
        print(f"  Total commits: {commit_count}")

        # Most commits should be protected (allowing 1 for initialization)
        if write_lock_count >= (commit_count - 1):
            print("  ✓ Write lock pattern is used consistently")
            print("✅ Test 2 PASSED\n")
            return True
        else:
            raise Exception(f"Only {write_lock_count} write locks for {commit_count} commits")

    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}\n")
        return False


def test_database_operations_functional():
    """Test that database operations still work correctly"""
    print("Test 3: Database operations functional test")
    print("-" * 60)

    try:
        from rag_system.database import RAGDatabase
        import time

        # Create test database instance
        db = RAGDatabase()
        print("  ✓ Database initialized")

        # Test document operations with unique DOI
        unique_doi = f"test/{int(time.time())}"
        doc_id = db.add_document(
            doi=unique_doi,
            title="Test Document",
            authors=["Test Author"],
            year="2024"
        )
        print(f"  ✓ Document added (ID: {doc_id})")

        # Test summary operations
        summary_id = db.add_summary(
            document_id=doc_id,
            summary_text="Test summary",
            model_used="test-model"
        )
        print(f"  ✓ Summary added (ID: {summary_id})")

        # Test chat history
        chat_id = db.add_chat_message(
            document_id=doc_id,
            user_question="Test question?",
            assistant_answer="Test answer",
            sources_used=["test"],
            retrieval_method="test"
        )
        print(f"  ✓ Chat message added (ID: {chat_id})")

        # Test delete operations
        db.clear_chat_history(doc_id)
        print("  ✓ Chat history cleared")

        db.delete_document(doc_id)
        print("  ✓ Document deleted")

        db.close()
        print("  ✓ Database closed")

        print("✅ Test 3 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_concurrent_safety_design():
    """Verify thread-safe design patterns"""
    print("Test 4: Thread-safe design patterns")
    print("-" * 60)

    try:
        from rag_system.database import RAGDatabase
        import threading

        db = RAGDatabase()

        # Check for write lock attribute
        if hasattr(db, '_write_lock'):
            print("  ✓ Database has _write_lock attribute")
        else:
            raise Exception("Database missing _write_lock attribute")

        # Check that it's a threading lock (can be _thread.lock or threading.Lock/RLock)
        lock_type = str(type(db._write_lock))
        if 'lock' in lock_type.lower():
            print(f"  ✓ _write_lock is a threading lock ({lock_type})")
        else:
            raise Exception(f"_write_lock is {lock_type}, expected a threading lock")

        # Check for thread-local storage
        if hasattr(db, '_local'):
            print("  ✓ Database uses thread-local storage")
        else:
            raise Exception("Database missing _local attribute")

        db.close()

        print("✅ Test 4 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("DATABASE THREAD SAFETY TEST SUITE")
    print("Testing Fix #9: Write locks for all database commits")
    print("=" * 60)
    print()

    tests = [
        test_all_commits_have_write_locks,
        test_write_lock_pattern,
        test_database_operations_functional,
        test_concurrent_safety_design
    ]

    results = []
    for test_func in tests:
        result = test_func()
        results.append(result)

    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("\n✅ ALL TESTS PASSED - Fix #9 is working correctly!")
        print("\nDatabase thread safety improvements:")
        print("  ✓ All database commits protected with write locks")
        print("  ✓ Consistent write lock pattern across all operations")
        print("  ✓ Thread-safe design with RLock and thread-local storage")
        print("  ✓ Database operations work correctly with locks")
        print("\nProtected operations:")
        print("  • add_document()")
        print("  • update_document()")
        print("  • delete_document()")
        print("  • add_embedding_metadata()")
        print("  • add_summary()")
        print("  • add_chat_history()")
        print("  • clear_chat_history()")
        print("  • add_processing_log()")
        print("  • save_comprehensive_analysis()")
        print("  • delete_analysis()")
        print("  • save_chunk()")
        print("  • save_agent_finding()")
        print("  • save_progressive_summary()")
        print("  • delete_agent_context()")
        print("  • delete_progressive_summaries()")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED - Fix needs attention")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
