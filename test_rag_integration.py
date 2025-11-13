"""
Comprehensive RAG Integration Test
Tests all 3 phases of the enhanced RAG system
"""

import sys
import traceback
from grok_client import GrokClient
import config

print("="*80)
print(" COMPREHENSIVE RAG INTEGRATION TEST")
print("="*80)
print()

# Track test results
all_tests_passed = True
test_results = []

def test_step(description):
    """Decorator for test steps"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            global all_tests_passed
            try:
                print(f"🧪 {description}...", end=" ", flush=True)
                result = func(*args, **kwargs)
                print("✅ PASSED")
                test_results.append((description, "PASSED", None))
                return result
            except Exception as e:
                print(f"❌ FAILED")
                print(f"   Error: {str(e)}")
                print(f"   {traceback.format_exc()}")
                test_results.append((description, "FAILED", str(e)))
                all_tests_passed = False
                return None
        return wrapper
    return decorator

# TEST 1: Import Modules
@test_step("Test 1: Import enhanced RAG module")
def test_imports():
    from rag_system.enhanced_rag import create_enhanced_rag_system
    return create_enhanced_rag_system

create_enhanced_rag_system = test_imports()

# TEST 2: Initialize Grok Client
@test_step("Test 2: Initialize Grok client")
def test_grok_init():
    grok = GrokClient(
        api_key=config.GROK_SETTINGS['api_key'],
        model="grok-beta",
        validate=False
    )
    return grok

grok = test_grok_init()

# TEST 3: Create Test Paper Data
@test_step("Test 3: Create test paper data")
def test_paper_data():
    paper_data = {
        'title': 'Test Paper on Quantum Computing for Finance',
        'sections': {
            'abstract': 'This paper presents a novel quantum computing approach for financial portfolio optimization. We demonstrate significant improvements in computational efficiency.',
            'introduction': 'Financial portfolio optimization is a challenging problem. Classical methods struggle with large-scale problems. Our quantum approach uses variational quantum eigensolvers (VQE) to address these challenges.',
            'methodology': 'We employed a hybrid quantum-classical framework. The quantum circuit consists of 10 qubits with parameterized rotation gates. We used the COBYLA optimizer for variational parameters.',
            'results': 'Our experiments show a 30% improvement in gate fidelity compared to baseline approaches. The quantum algorithm achieved convergence in 50 iterations with error rates below 1%.',
            'discussion': 'The main limitations include scalability due to NISQ hardware constraints and noise affecting accuracy. Future work will focus on error mitigation techniques.',
            'conclusion': 'We have demonstrated the viability of quantum computing for finance applications, with clear advantages in computational efficiency.'
        }
    }
    return paper_data

paper_data = test_paper_data()

# TEST 4: Initialize Enhanced RAG System
print("\n📦 PHASE 1: Foundation (Vector DB + Hybrid Search)")
print("-" * 80)

@test_step("Test 4: Initialize enhanced RAG system")
def test_rag_initialization():
    if not create_enhanced_rag_system or not grok or not paper_data:
        raise Exception("Prerequisites not met")

    components = create_enhanced_rag_system(paper_data, grok)

    # Verify all components exist
    assert 'rag' in components, "RAG component missing"
    assert 'query_expander' in components, "Query expander missing"
    assert 'multi_hop_qa' in components, "Multi-hop QA missing"
    assert 'self_reflective' in components, "Self-reflective RAG missing"

    return components

components = test_rag_initialization()

# TEST 5: Test Vector Database Stats
@test_step("Test 5: Verify vector database has indexed chunks")
def test_vector_stats():
    if not components:
        raise Exception("RAG components not initialized")

    stats = components['rag'].get_paper_stats()
    assert stats['total_chunks'] > 0, "No chunks indexed"
    assert stats['sections'] > 0, "No sections indexed"
    print(f"\n   📊 Indexed: {stats['total_chunks']} chunks, {stats['sections']} sections")
    return stats

stats = test_vector_stats()

# TEST 6: Test Hybrid Search (Phase 1)
@test_step("Test 6: Test hybrid search retrieval")
def test_hybrid_search():
    if not components:
        raise Exception("RAG components not initialized")

    query = "What methodology did the authors use?"
    results = components['rag'].retrieve(query, top_k=5, hybrid_alpha=0.5)

    assert len(results) > 0, "No results retrieved"
    assert 'content' in results[0], "Result missing content"
    assert 'score' in results[0], "Result missing score"
    print(f"\n   🔍 Retrieved {len(results)} relevant chunks")
    print(f"   Top result score: {results[0]['score']:.2f}")
    return results

retrieval_results = test_hybrid_search()

# TEST 7: Test Query Expansion (Phase 2)
print("\n🧠 PHASE 2: Intelligence (Query Expansion + Multi-hop)")
print("-" * 80)

@test_step("Test 7: Test query expansion")
def test_query_expansion():
    if not components:
        raise Exception("RAG components not initialized")

    original_query = "What is the method?"
    expanded = components['query_expander'].expand_query(
        query=original_query,
        paper_title=paper_data['title']
    )

    assert 'expanded' in expanded, "Expanded query missing"
    assert len(expanded['expanded']) > len(original_query), "Query not expanded"
    print(f"\n   Original: '{original_query}'")
    print(f"   Expanded: '{expanded['expanded'][:100]}...'")
    return expanded

expanded_query = test_query_expansion()

# TEST 8: Test Multi-hop Detection
@test_step("Test 8: Test multi-hop question detection")
def test_multihop_detection():
    if not components:
        raise Exception("RAG components not initialized")

    # Should detect multi-hop
    multihop_query = "How does the proposed method compare to the baseline mentioned in the introduction?"
    is_multihop = components['multi_hop_qa'].detect_multi_hop(multihop_query)
    assert is_multihop, "Failed to detect multi-hop question"

    # Should NOT detect multi-hop
    single_query = "What are the results?"
    is_single = components['multi_hop_qa'].detect_multi_hop(single_query)
    assert not is_single, "False positive on single-hop question"

    print(f"\n   ✓ Multi-hop detection working correctly")
    return True

test_multihop_detection()

# TEST 9: Test Multi-hop QA
@test_step("Test 9: Test multi-hop question answering")
def test_multihop_qa():
    if not components:
        raise Exception("RAG components not initialized")

    query = "How does the quantum approach compare to classical methods and what are the results?"
    result = components['multi_hop_qa'].answer_multi_hop(
        query=query,
        paper_title=paper_data['title']
    )

    assert 'answer' in result, "Answer missing from result"
    assert len(result['answer']) > 0, "Empty answer"
    assert 'evidence' in result, "Evidence missing"
    print(f"\n   Answer length: {len(result['answer'])} chars")
    print(f"   Evidence sections: {len(result.get('evidence', []))}")
    return result

multihop_result = test_multihop_qa()

# TEST 10: Test Self-Reflective RAG (Phase 3)
print("\n✨ PHASE 3: Polish (Self-Reflection + Confidence)")
print("-" * 80)

@test_step("Test 10: Test self-reflective RAG with confidence scoring")
def test_self_reflective():
    if not components:
        raise Exception("RAG components not initialized")

    query = "What are the limitations of this approach?"
    result = components['self_reflective'].answer_with_reflection(
        query=query,
        paper_title=paper_data['title'],
        max_iterations=2
    )

    assert 'answer' in result, "Answer missing"
    assert 'confidence' in result, "Confidence score missing"
    assert 0 <= result['confidence'] <= 1, "Confidence score out of range"

    confidence = result['confidence']
    iterations = result.get('iterations', 1)

    print(f"\n   Answer length: {len(result['answer'])} chars")
    print(f"   Confidence: {confidence:.2%}")
    print(f"   Iterations: {iterations}")

    return result

reflection_result = test_self_reflective()

# TEST 11: Test Confidence Thresholds
@test_step("Test 11: Verify confidence scoring logic")
def test_confidence_logic():
    if not reflection_result:
        raise Exception("Self-reflective result not available")

    confidence = reflection_result['confidence']

    if confidence >= 0.7:
        level = "High"
    elif confidence >= 0.5:
        level = "Medium"
    else:
        level = "Low"

    print(f"\n   Confidence level: {level}")
    return True

test_confidence_logic()

# TEST 12: Test Chat_With_Paper.py Syntax
print("\n🔍 INTEGRATION VERIFICATION")
print("-" * 80)

@test_step("Test 12: Verify Chat_With_Paper.py has no syntax errors")
def test_chat_syntax():
    import ast
    with open('pages/Chat_With_Paper.py', 'r') as f:
        code = f.read()
    ast.parse(code)
    return True

test_chat_syntax()

# TEST 13: Verify Imports in Chat_With_Paper.py
@test_step("Test 13: Verify enhanced RAG import in Chat_With_Paper.py")
def test_chat_imports():
    with open('pages/Chat_With_Paper.py', 'r') as f:
        code = f.read()
    assert 'from rag_system.enhanced_rag import create_enhanced_rag_system' in code, "Import missing"
    assert 'enhanced_rag' in code, "RAG session state missing"
    assert 'rag_initialized' in code, "RAG initialized flag missing"
    return True

test_chat_imports()

# SUMMARY
print("\n" + "="*80)
print(" TEST SUMMARY")
print("="*80)
print()

passed = sum(1 for _, status, _ in test_results if status == "PASSED")
failed = sum(1 for _, status, _ in test_results if status == "FAILED")
total = len(test_results)

print(f"Total Tests: {total}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")
print()

if all_tests_passed:
    print("🎉 ALL TESTS PASSED! Integration is successful.")
    print()
    print("✅ Phase 1 (Foundation): Vector DB + Hybrid Search - WORKING")
    print("✅ Phase 2 (Intelligence): Query Expansion + Multi-hop QA - WORKING")
    print("✅ Phase 3 (Polish): Self-Reflection + Confidence - WORKING")
    print("✅ Integration: Chat_With_Paper.py - READY")
    print()
    print("🚀 The enhanced RAG system is fully integrated and operational!")
else:
    print("⚠️ SOME TESTS FAILED. Please review the errors above.")
    print()
    print("Failed tests:")
    for desc, status, error in test_results:
        if status == "FAILED":
            print(f"  ❌ {desc}")
            print(f"     Error: {error}")
    sys.exit(1)

print("="*80)
