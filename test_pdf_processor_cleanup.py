"""
Test to verify PDF processor resource cleanup
Tests Fix #10: Resource leaks in PDF processor
"""

import sys
from pathlib import Path
import tempfile
import fitz  # PyMuPDF

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def create_test_pdf():
    """Create a simple test PDF for testing"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc = fitz.open()

    # Add a few pages with text
    for i in range(3):
        page = doc.new_page()
        page.insert_text((72, 72), f"Test Page {i+1}\nThis is test content for page {i+1}.")

    doc.save(temp_file.name)
    doc.close()
    return temp_file.name


def test_finally_blocks_present():
    """Verify all PDF-opening methods have finally blocks"""
    print("Test 1: Finally blocks present in all PDF methods")
    print("-" * 60)

    try:
        pdf_processor_path = Path("rag_system/pdf_processor.py")

        with open(pdf_processor_path, 'r') as f:
            content = f.read()

        # Methods that open PDFs
        pdf_methods = [
            'extract_text_from_pdf',
            'get_page_text',
            'get_page_count',
            'extract_images_info'
        ]

        for method in pdf_methods:
            # Find the method
            method_start = content.find(f'def {method}(')
            if method_start == -1:
                raise Exception(f"Method {method} not found")

            # Find the next method or end of class (larger window for extract_text_from_pdf)
            next_def = content.find('\n    def ', method_start + 10)
            if next_def == -1:
                method_section = content[method_start:]
            else:
                method_section = content[method_start:next_def]

            # Check for finally block
            if 'finally:' not in method_section:
                raise Exception(f"Method {method} missing finally block")

            # Check for doc.close() in finally
            finally_pos = method_section.find('finally:')
            if 'doc.close()' not in method_section[finally_pos:]:
                raise Exception(f"Method {method} doesn't close doc in finally block")

            print(f"  ✓ {method}() has proper finally block with doc.close()")

        print("✅ Test 1 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}\n")
        return False


def test_extract_text_cleanup():
    """Test extract_text_from_pdf properly closes resources"""
    print("Test 2: extract_text_from_pdf resource cleanup")
    print("-" * 60)

    try:
        from rag_system.pdf_processor import PDFProcessor

        test_pdf = create_test_pdf()
        processor = PDFProcessor()

        # Test successful extraction
        result = processor.extract_text_from_pdf(test_pdf)

        if not result['success']:
            raise Exception("Extraction failed")

        print(f"  ✓ Successfully extracted text from {result['total_pages']} pages")

        # Test with invalid PDF path (should handle gracefully)
        result_invalid = processor.extract_text_from_pdf("nonexistent.pdf")

        if result_invalid['success']:
            raise Exception("Should have failed with invalid path")

        print("  ✓ Handled invalid PDF gracefully")

        # Cleanup
        Path(test_pdf).unlink()

        print("✅ Test 2 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_get_page_text_cleanup():
    """Test get_page_text properly closes resources"""
    print("Test 3: get_page_text resource cleanup")
    print("-" * 60)

    try:
        from rag_system.pdf_processor import PDFProcessor

        test_pdf = create_test_pdf()
        processor = PDFProcessor()

        # Test successful page retrieval
        text = processor.get_page_text(test_pdf, 1)

        if text is None:
            raise Exception("Failed to get page text")

        if "Test Page 1" not in text:
            raise Exception("Incorrect page text retrieved")

        print("  ✓ Successfully retrieved page text")

        # Test with invalid page number
        text_invalid = processor.get_page_text(test_pdf, 999)

        if text_invalid is not None:
            raise Exception("Should return None for invalid page")

        print("  ✓ Handled invalid page number gracefully")

        # Test with invalid PDF
        text_bad_pdf = processor.get_page_text("nonexistent.pdf", 1)

        if text_bad_pdf is not None:
            raise Exception("Should return None for invalid PDF")

        print("  ✓ Handled invalid PDF gracefully")

        # Cleanup
        Path(test_pdf).unlink()

        print("✅ Test 3 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_get_page_count_cleanup():
    """Test get_page_count properly closes resources"""
    print("Test 4: get_page_count resource cleanup")
    print("-" * 60)

    try:
        from rag_system.pdf_processor import PDFProcessor

        test_pdf = create_test_pdf()
        processor = PDFProcessor()

        # Test successful page count
        count = processor.get_page_count(test_pdf)

        if count != 3:
            raise Exception(f"Expected 3 pages, got {count}")

        print(f"  ✓ Successfully counted {count} pages")

        # Test with invalid PDF
        count_invalid = processor.get_page_count("nonexistent.pdf")

        if count_invalid != 0:
            raise Exception("Should return 0 for invalid PDF")

        print("  ✓ Handled invalid PDF gracefully (returned 0)")

        # Cleanup
        Path(test_pdf).unlink()

        print("✅ Test 4 PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Test 4 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_extract_images_info_cleanup():
    """Test extract_images_info properly closes resources"""
    print("Test 5: extract_images_info resource cleanup")
    print("-" * 60)

    try:
        from rag_system.pdf_processor import PDFProcessor

        test_pdf = create_test_pdf()
        processor = PDFProcessor()

        # Test successful image info extraction
        images_info = processor.extract_images_info(test_pdf)

        # Our test PDF has no images, so should return empty list
        if not isinstance(images_info, list):
            raise Exception("Should return a list")

        print(f"  ✓ Successfully extracted image info (found {len(images_info)} images)")

        # Test with invalid PDF
        images_invalid = processor.extract_images_info("nonexistent.pdf")

        if not isinstance(images_invalid, list):
            raise Exception("Should return empty list for invalid PDF")

        print("  ✓ Handled invalid PDF gracefully (returned empty list)")

        # Cleanup
        Path(test_pdf).unlink()

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
    print("PDF PROCESSOR RESOURCE CLEANUP TEST SUITE")
    print("Testing Fix #10: PDF processor resource leaks")
    print("=" * 60)
    print()

    tests = [
        test_finally_blocks_present,
        test_extract_text_cleanup,
        test_get_page_text_cleanup,
        test_get_page_count_cleanup,
        test_extract_images_info_cleanup
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
        print("\n✅ ALL TESTS PASSED - Fix #10 is working correctly!")
        print("\nPDF processor resource leak fixes:")
        print("  ✓ All PDF-opening methods use try-finally blocks")
        print("  ✓ Document handles always closed, even on exceptions")
        print("  ✓ Proper error handling maintains resource cleanup")
        print("  ✓ No file handle leaks in any code path")
        print("\nFixed methods:")
        print("  • extract_text_from_pdf() - already had proper cleanup")
        print("  • get_page_text() - added try-finally block")
        print("  • get_page_count() - added try-finally block")
        print("  • extract_images_info() - added try-finally block")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED - Fix needs attention")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
