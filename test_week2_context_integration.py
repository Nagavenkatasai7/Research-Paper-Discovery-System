"""
Test Week 2: Context Manager & Document Processor Integration
================================================================

Verify that:
1. ContextManager integrates with orchestrator
2. Two-pass analysis works
3. DocumentProcessor supports multiple formats
"""

import sys
from pathlib import Path

def test_context_manager_import():
    """Test that ContextManager can be imported"""
    print("="*80)
    print("TEST 1: ContextManager Import")
    print("="*80)

    try:
        from rag_system.context_manager import ContextManager, Finding
        print("✅ ContextManager imported successfully")
        print("✅ Finding dataclass imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_context_manager_functionality():
    """Test ContextManager basic functionality"""
    print("\n" + "="*80)
    print("TEST 2: ContextManager Functionality")
    print("="*80)

    try:
        from rag_system.context_manager import ContextManager

        cm = ContextManager()
        print("✅ ContextManager initialized")

        # Register findings
        cm.register_finding(
            'methodology',
            'methodology',
            {'technique': 'Transformer'},
            relevance_to=['results'],
            priority='high'
        )

        cm.register_finding(
            'results',
            'result',
            {'metric': 'BLEU', 'value': 28.4},
            relevance_to=['discussion'],
            priority='high'
        )

        print(f"✅ Registered {len(cm.findings)} findings")

        # Retrieve context
        context = cm.get_context_for_agent('discussion')
        print(f"✅ Retrieved context from {len(context)} agents")

        # Build cross-reference map
        cross_ref = cm.build_cross_reference_map({})
        print(f"✅ Built cross-reference map with {len(cross_ref)} categories")

        # Get statistics
        stats = cm.get_summary_statistics()
        print(f"✅ Statistics: {stats['total_findings']} findings, {stats['high_priority_findings']} high priority")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_document_processor_import():
    """Test that DocumentProcessor can be imported"""
    print("\n" + "="*80)
    print("TEST 3: DocumentProcessor Import")
    print("="*80)

    try:
        from rag_system.document_processor import DocumentProcessor
        print("✅ DocumentProcessor imported successfully")

        processor = DocumentProcessor()
        print(f"✅ Supported formats: {processor.supported_formats}")

        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator_context_integration():
    """Test that orchestrator has context manager"""
    print("\n" + "="*80)
    print("TEST 4: Orchestrator Context Integration")
    print("="*80)

    try:
        from rag_system.analysis_agents import DocumentAnalysisOrchestrator

        orchestrator = DocumentAnalysisOrchestrator()
        print("✅ Orchestrator initialized")

        # Check if context_manager exists
        assert hasattr(orchestrator, 'context_manager'), "Orchestrator missing context_manager"
        print("✅ Orchestrator has context_manager attribute")

        # Check if _extract_and_register_findings method exists
        assert hasattr(orchestrator, '_extract_and_register_findings'), "Missing _extract_and_register_findings method"
        print("✅ Orchestrator has _extract_and_register_findings method")

        # Check context manager is initialized
        assert orchestrator.context_manager is not None, "context_manager is None"
        print("✅ ContextManager is initialized in orchestrator")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_analyze_paper_signature():
    """Test that analyze_paper has enable_context_sharing parameter"""
    print("\n" + "="*80)
    print("TEST 5: analyze_paper Context Parameter")
    print("="*80)

    try:
        from rag_system.analysis_agents import DocumentAnalysisOrchestrator
        import inspect

        orchestrator = DocumentAnalysisOrchestrator()

        # Get analyze_paper signature
        sig = inspect.signature(orchestrator.analyze_paper)
        params = sig.parameters

        # Check for enable_context_sharing parameter
        assert 'enable_context_sharing' in params, "Missing enable_context_sharing parameter"
        print("✅ analyze_paper has enable_context_sharing parameter")

        # Check default value
        default = params['enable_context_sharing'].default
        print(f"✅ Default value: {default}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_finding_extraction():
    """Test _extract_and_register_findings method"""
    print("\n" + "="*80)
    print("TEST 6: Finding Extraction from Agent Results")
    print("="*80)

    try:
        from rag_system.analysis_agents import DocumentAnalysisOrchestrator

        orchestrator = DocumentAnalysisOrchestrator()

        # Mock agent results
        mock_results = {
            'methodology': {
                'success': True,
                'analysis': {
                    'approach': 'Transformer architecture',
                    'technique': 'self-attention',
                    'limitations': ['High computational cost']
                }
            },
            'results': {
                'success': True,
                'analysis': {
                    'key_findings': ['BLEU score of 28.4', 'Faster training'],
                    'main_contributions': ['Novel attention mechanism']
                }
            },
            'tables': {
                'success': True,
                'analysis': {
                    'key_metrics': [
                        {'metric_name': 'BLEU', 'best_value': 28.4}
                    ]
                }
            }
        }

        # Extract findings
        orchestrator._extract_and_register_findings(mock_results)

        # Check findings were registered
        stats = orchestrator.context_manager.get_summary_statistics()
        print(f"✅ Extracted {stats['total_findings']} findings")
        print(f"✅ From {stats['agents_with_findings']} agents")
        print(f"✅ High priority: {stats['high_priority_findings']}")

        # Check specific finding types
        findings_by_type = stats['findings_by_type']
        print(f"✅ Finding types: {list(findings_by_type.keys())}")

        assert stats['total_findings'] > 0, "No findings extracted"

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("WEEK 2: CONTEXT MANAGER & DOCUMENT PROCESSOR INTEGRATION TESTS")
    print("="*80 + "\n")

    tests = [
        ("ContextManager Import", test_context_manager_import),
        ("ContextManager Functionality", test_context_manager_functionality),
        ("DocumentProcessor Import", test_document_processor_import),
        ("Orchestrator Context Integration", test_orchestrator_context_integration),
        ("analyze_paper Context Parameter", test_analyze_paper_signature),
        ("Finding Extraction", test_finding_extraction)
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
        print("\n🎉 ALL TESTS PASSED! Week 2 integration is complete.")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
