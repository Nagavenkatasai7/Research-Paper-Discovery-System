"""
Critical Bug Tests - Testing Identified Issues
===============================================
Tests for the 2 bugs found in RAG integration:
1. Hybrid search result structure mismatch (content vs text field)
2. Query expansion not working as expected
"""

import sys
sys.path.append('.')

from rag_system.enhanced_rag import create_enhanced_rag_system
from grok_client import GrokClient
import config

def test_bug_1_hybrid_search_result_structure():
    """
    BUG #1: Hybrid search returns 'text' field but test expects 'content'
    Root Cause: API contract mismatch between implementation and tests
    """
    print("\n" + "="*80)
    print("🐛 BUG TEST #1: Hybrid Search Result Structure")
    print("="*80)

    try:
        # Initialize RAG system
        components = create_enhanced_rag_system()
        rag = components['rag']

        # Index test paper
        test_paper = {
            'title': 'Test Paper',
            'sections': {
                'introduction': 'This is the introduction section with test content.',
                'methodology': 'This is the methodology section describing our approach.',
                'results': 'This section contains the experimental results and findings.'
            }
        }

        rag.index_paper(test_paper['title'], test_paper['sections'])

        # Perform hybrid search
        results = rag.retrieve("What methodology was used?", top_k=3, hybrid_alpha=0.5)

        print(f"\n📊 Retrieved {len(results)} results")

        # Check result structure
        if len(results) > 0:
            first_result = results[0]
            print(f"\n🔍 Result keys: {list(first_result.keys())}")

            # Test for both 'text' and 'content' fields
            has_text = 'text' in first_result
            has_content = 'content' in first_result

            print(f"   Has 'text' field: {has_text}")
            print(f"   Has 'content' field: {has_content}")

            if has_text and not has_content:
                print("\n⚠️  BUG CONFIRMED: Results use 'text' field, not 'content'")
                print("   RECOMMENDATION: Update test expectations OR standardize to 'content'")
                return "BUG_CONFIRMED"
            elif has_content:
                print("\n✅ Results correctly use 'content' field")
                return "PASS"
            else:
                print("\n❌ Results missing both 'text' and 'content' fields")
                return "CRITICAL_ERROR"
        else:
            print("\n❌ No results returned from hybrid search")
            return "NO_RESULTS"

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return "ERROR"


def test_bug_2_query_expansion():
    """
    BUG #2: Query expansion not significantly expanding queries
    Root Cause: Grok API might be returning minimal expansions for already-clear queries
    """
    print("\n" + "="*80)
    print("🐛 BUG TEST #2: Query Expansion")
    print("="*80)

    try:
        # Initialize components
        components = create_enhanced_rag_system()
        query_expander = components['query_expander']

        # Test with various query types
        test_queries = [
            ("vague query", "quantum computing"),  # Should expand
            ("clear query", "variational quantum eigensolver algorithm for molecular simulation"),  # May not expand much
            ("acronym", "VQE"),  # Should expand acronym
            ("broad topic", "AI")  # Should expand significantly
        ]

        expansion_success = 0
        total_tests = len(test_queries)

        for query_type, original_query in test_queries:
            print(f"\n🧪 Testing {query_type}: '{original_query}'")

            expanded = query_expander.expand_query(original_query, "Test Paper Title")

            original_len = len(original_query.split())
            expanded_len = len(expanded.get('expanded', '').split())

            print(f"   Original length: {original_len} words")
            print(f"   Expanded length: {expanded_len} words")
            print(f"   Expanded query: {expanded.get('expanded', '')[:100]}...")

            # Query should be expanded by at least 20% for vague/broad queries
            if query_type in ["vague query", "acronym", "broad topic"]:
                if expanded_len > original_len * 1.2:
                    print(f"   ✅ Query expanded successfully ({expanded_len/original_len:.1f}x)")
                    expansion_success += 1
                else:
                    print(f"   ⚠️  Query not sufficiently expanded (only {expanded_len/original_len:.1f}x)")
            else:
                # For already clear queries, minimal expansion is acceptable
                print(f"   ℹ️  Clear query - minimal expansion acceptable")
                expansion_success += 1

        success_rate = (expansion_success / total_tests) * 100
        print(f"\n📊 Expansion success rate: {success_rate:.1f}%")

        if success_rate >= 75:
            print("✅ Query expansion working adequately")
            return "PASS"
        elif success_rate >= 50:
            print("⚠️  Query expansion working partially - needs improvement")
            return "PARTIAL"
        else:
            print("❌ Query expansion not working as expected")
            return "FAIL"

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return "ERROR"


def test_bug_3_chat_initialization():
    """
    Additional test: Verify chat system initializes correctly
    """
    print("\n" + "="*80)
    print("🔍 ADDITIONAL TEST: Chat System Initialization")
    print("="*80)

    try:
        components = create_enhanced_rag_system()

        # Check all required components
        required = ['rag', 'query_expander', 'multi_hop_qa', 'self_reflective']

        all_present = True
        for component in required:
            is_present = component in components and components[component] is not None
            status = "✅" if is_present else "❌"
            print(f"{status} {component}: {'Present' if is_present else 'Missing'}")
            if not is_present:
                all_present = False

        if all_present:
            print("\n✅ All components initialized correctly")
            return "PASS"
        else:
            print("\n❌ Some components missing")
            return "FAIL"

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return "ERROR"


if __name__ == "__main__":
    print("""
================================================================================
CRITICAL BUG TESTING SUITE
================================================================================
Testing identified bugs in RAG integration
""")

    # Run all bug tests
    results = {
        'Bug #1 (Hybrid Search Structure)': test_bug_1_hybrid_search_result_structure(),
        'Bug #2 (Query Expansion)': test_bug_2_query_expansion(),
        'Additional (Chat Initialization)': test_bug_3_chat_initialization()
    }

    print("\n" + "="*80)
    print("📊 TEST RESULTS SUMMARY")
    print("="*80)

    for test_name, result in results.items():
        status_emoji = {
            'PASS': '✅',
            'PARTIAL': '⚠️',
            'FAIL': '❌',
            'ERROR': '❌',
            'BUG_CONFIRMED': '🐛',
            'CRITICAL_ERROR': '🔥',
            'NO_RESULTS': '⚠️'
        }.get(result, '❓')

        print(f"{status_emoji} {test_name}: {result}")

    # Calculate overall status
    passed = sum(1 for r in results.values() if r == 'PASS')
    total = len(results)

    print(f"\n📈 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("✅ ALL TESTS PASSED")
    elif passed >= total * 0.7:
        print("⚠️  MOST TESTS PASSED - Minor issues remain")
    else:
        print("❌ MULTIPLE TESTS FAILED - Attention required")
