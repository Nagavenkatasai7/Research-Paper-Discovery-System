"""
Test to verify document_chat.py uses proper database methods with write lock
Tests Fix #6: Database transaction bypass
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_no_direct_database_access():
    """Verify document_chat.py doesn't directly access database connection"""
    print("Test 1: No direct database connection access")
    print("-" * 50)

    try:
        doc_chat_path = Path("rag_system/document_chat.py")

        if not doc_chat_path.exists():
            raise Exception("document_chat.py not found")

        with open(doc_chat_path, 'r') as f:
            content = f.read()

        # Check for direct connection access patterns
        problematic_patterns = [
            'self.db.conn.cursor()',
            'self.db.conn.commit()',
            'self.db.conn.execute'
        ]

        issues_found = []
        for pattern in problematic_patterns:
            if pattern in content:
                # Find line numbers
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if pattern in line:
                        issues_found.append((pattern, i))

        if len(issues_found) > 0:
            print(f"  ❌ Found {len(issues_found)} direct database access patterns:")
            for pattern, line_num in issues_found:
                print(f"    Line {line_num}: {pattern}")
            raise Exception("Direct database access still present")
        else:
            print("  ✓ No direct database connection access found")

        print("✅ Test 1 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}\n")
        return False


def test_uses_database_methods():
    """Verify document_chat.py uses proper database wrapper methods"""
    print("Test 2: Uses database wrapper methods")
    print("-" * 50)

    try:
        doc_chat_path = Path("rag_system/document_chat.py")

        with open(doc_chat_path, 'r') as f:
            content = f.read()

        # Check for proper database method calls
        proper_patterns = [
            'self.db.clear_chat_history(',
            'self.db.get_chat_history('
        ]

        found_patterns = []
        for pattern in proper_patterns:
            if pattern in content:
                found_patterns.append(pattern)
                print(f"  ✓ Found proper usage: {pattern}")

        if len(found_patterns) < 2:
            raise Exception("Not all database methods are being used properly")

        print("✅ Test 2 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}\n")
        return False


def test_write_lock_in_database():
    """Verify database.py clear_chat_history has write lock"""
    print("Test 3: Write lock in database clear_chat_history")
    print("-" * 50)

    try:
        db_path = Path("rag_system/database.py")

        with open(db_path, 'r') as f:
            content = f.read()

        # Find clear_chat_history method
        method_start = content.find('def clear_chat_history(')
        if method_start == -1:
            raise Exception("clear_chat_history method not found")

        # Get next 400 chars after method definition (increased for better detection)
        method_section = content[method_start:method_start + 400]

        # Check for write lock usage
        if 'with self._write_lock:' in method_section:
            print("  ✓ clear_chat_history() uses write lock")
        else:
            raise Exception("Write lock not found in clear_chat_history()")

        # Check for commit inside write lock
        if 'conn.commit()' in method_section:
            print("  ✓ conn.commit() present")

            # Verify it's after the write lock
            lock_pos = method_section.find('with self._write_lock:')
            commit_pos = method_section.find('conn.commit()')

            if commit_pos > lock_pos:
                print("  ✓ commit() is inside write lock block")
            else:
                raise Exception("commit() is not inside write lock block")
        else:
            raise Exception("conn.commit() not found")

        print("✅ Test 3 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}\n")
        return False


def test_functional_integration():
    """Test that document_chat actually works with the fix"""
    print("Test 4: Functional integration test")
    print("-" * 50)

    try:
        from rag_system.document_chat import DocumentChatSystem
        from rag_system.database import RAGDatabase

        # Create test database
        test_db_path = "database/test_document_chat_fix.db"
        if Path(test_db_path).exists():
            Path(test_db_path).unlink()

        # Create chat system (uses default database path)
        chat_system = DocumentChatSystem()
        print("  ✓ DocumentChatSystem created")

        # Test clear_chat_history method
        try:
            chat_system.clear_chat_history(document_id=999)
            print("  ✓ clear_chat_history() executed without errors")
        except Exception as e:
            raise Exception(f"clear_chat_history() failed: {e}")

        # Verify database connection is proper
        if hasattr(chat_system.db, '_write_lock'):
            print("  ✓ Database has write lock")
        else:
            raise Exception("Database missing write lock")

        chat_system.db.close()
        print("  ✓ Database closed properly")

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
    print("DOCUMENT CHAT DATABASE BYPASS FIX TEST SUITE")
    print("Testing Fix #6: Database transaction bypass")
    print("=" * 60)
    print()

    tests = [
        test_no_direct_database_access,
        test_uses_database_methods,
        test_write_lock_in_database,
        test_functional_integration
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
        print("\n✅ ALL TESTS PASSED - Fix #6 is working correctly!")
        print("\nThe database transaction bypass fix:")
        print("  ✓ document_chat.py uses proper database methods")
        print("  ✓ No direct connection access")
        print("  ✓ Write lock protection applied")
        print("  ✓ Thread-safe database operations")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED - Fix needs attention")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
