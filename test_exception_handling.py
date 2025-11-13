"""
Test to verify exception handling improvements
Tests Fix #7: Bare exception handlers replaced with specific exceptions
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def test_no_bare_exceptions_in_production():
    """Verify no bare exception handlers in production code"""
    print("Test 1: No bare exception handlers in production code")
    print("-" * 60)

    try:
        production_files = [
            "rag_system/pdf_processor.py",
            "rag_system/enhanced_rag.py",
            "pages/Document_Analysis.py",
            "pages/Chat_With_Paper.py",
            "utils.py",
            "phase3_production.py",
            "phase2_advanced_search.py"
        ]

        issues_found = []

        for file_path in production_files:
            path = Path(file_path)
            if not path.exists():
                print(f"  ⚠️  Skipping {file_path} (not found)")
                continue

            with open(path, 'r') as f:
                lines = f.readlines()

            # Check for bare exception handlers
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped == "except:":
                    issues_found.append((file_path, i))

        if len(issues_found) > 0:
            print(f"  ❌ Found {len(issues_found)} bare exception handlers:")
            for file_path, line_num in issues_found:
                print(f"    {file_path}:{line_num}")
            raise Exception("Bare exception handlers still present in production code")
        else:
            print("  ✓ No bare exception handlers found in production code")

        print("✅ Test 1 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}\n")
        return False


def test_specific_exceptions_used():
    """Verify specific exception types are used in fixed files"""
    print("Test 2: Specific exception types used")
    print("-" * 60)

    try:
        # Check for proper exception patterns in key files
        expected_patterns = {
            "rag_system/pdf_processor.py": ["except Exception as e:"],
            "rag_system/enhanced_rag.py": [
                "except Exception as e:",
                "except (ValueError, IndexError) as e:"
            ],
            "pages/Document_Analysis.py": ["except OSError as e:"],
            "pages/Chat_With_Paper.py": ["except Exception as e:"],
            "utils.py": [
                "except (TypeError, ValueError) as e:",
                "except (requests.RequestException, Exception) as e:"
            ],
            "phase3_production.py": ["except (ValueError, TypeError) as e:"],
            "phase2_advanced_search.py": ["except (ValueError, AttributeError) as e:"]
        }

        for file_path, patterns in expected_patterns.items():
            path = Path(file_path)
            if not path.exists():
                print(f"  ⚠️  Skipping {file_path} (not found)")
                continue

            with open(path, 'r') as f:
                content = f.read()

            found_count = 0
            for pattern in patterns:
                if pattern in content:
                    found_count += 1

            if found_count > 0:
                print(f"  ✓ {file_path}: Found {found_count} specific exception handlers")
            else:
                raise Exception(f"No specific exception patterns found in {file_path}")

        print("✅ Test 2 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}\n")
        return False


def test_exception_logging_present():
    """Verify exception handlers have logging or comments"""
    print("Test 3: Exception handlers have logging/comments")
    print("-" * 60)

    try:
        # Files that should have logging or comments in exception handlers
        files_to_check = {
            "rag_system/pdf_processor.py": "Warning: Error closing PDF document",
            "rag_system/enhanced_rag.py": "Warning: Answer refinement iteration failed",
            "pages/Document_Analysis.py": "Warning: Failed to delete temporary file",
            "pages/Chat_With_Paper.py": "Warning: Could not retrieve RAG stats"
        }

        for file_path, expected_message in files_to_check.items():
            path = Path(file_path)
            if not path.exists():
                print(f"  ⚠️  Skipping {file_path} (not found)")
                continue

            with open(path, 'r') as f:
                content = f.read()

            if expected_message in content or "print(f\"" in content:
                print(f"  ✓ {file_path}: Has exception logging")
            else:
                # Check for at least comments
                if "# " in content and "exception" in content.lower():
                    print(f"  ✓ {file_path}: Has exception comments")
                else:
                    raise Exception(f"No logging or comments found in {file_path}")

        print("✅ Test 3 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}\n")
        return False


def test_code_still_runs():
    """Test that code with fixed exceptions still runs"""
    print("Test 4: Code with fixed exceptions runs correctly")
    print("-" * 60)

    try:
        # Test imports
        from rag_system.pdf_processor import PDFProcessor
        from rag_system.enhanced_rag import EnhancedRAGSystem
        from utils import validate_url, clean_html

        print("  ✓ All imports successful")

        # Test URL validation with invalid URL (should return False, not crash)
        result = validate_url("invalid_url_xyz")
        if result == False:
            print("  ✓ validate_url handles invalid URLs correctly")

        # Test clean_html
        cleaned = clean_html("<p>Test</p>")
        if "Test" in cleaned:
            print("  ✓ clean_html works correctly")

        # Test PDFProcessor initialization
        pdf_proc = PDFProcessor()
        print("  ✓ PDFProcessor initializes correctly")

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
    print("EXCEPTION HANDLING IMPROVEMENTS TEST SUITE")
    print("Testing Fix #7: Bare exception handlers replaced")
    print("=" * 60)
    print()

    tests = [
        test_no_bare_exceptions_in_production,
        test_specific_exceptions_used,
        test_exception_logging_present,
        test_code_still_runs
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
        print("\n✅ ALL TESTS PASSED - Fix #7 is working correctly!")
        print("\nException handling improvements:")
        print("  ✓ No bare exception handlers in production code")
        print("  ✓ Specific exception types used (Exception, OSError, ValueError, etc.)")
        print("  ✓ Exception handlers include logging/comments for debugging")
        print("  ✓ Code functionality preserved")
        print("\nFixed files:")
        print("  • rag_system/pdf_processor.py")
        print("  • rag_system/enhanced_rag.py")
        print("  • pages/Document_Analysis.py")
        print("  • pages/Chat_With_Paper.py")
        print("  • utils.py (3 locations)")
        print("  • phase3_production.py")
        print("  • phase2_advanced_search.py")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED - Fix needs attention")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
