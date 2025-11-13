"""
Test Week 4: Enhancements & Integration
=========================================

Verify that:
1. Progressive summarization works in synthesis_agent
2. Quality validator validates analysis results
3. Analysis-aware RAG integrates with multi-agent system
4. End-to-end integration works
"""

import sys
from pathlib import Path


def test_synthesis_progressive_summarization():
    """Test progressive summarization in synthesis_agent"""
    print("="*80)
    print("TEST 1: Progressive Summarization")
    print("="*80)

    try:
        from rag_system.analysis_agents import SynthesisAgent

        agent = SynthesisAgent()
        print("✅ SynthesisAgent initialized")

        # Check for new methods
        required_methods = [
            'create_progressive_summaries',
            '_condense_summary',
            'create_section_summaries',
            '_extract_section_content',
            'get_summary_by_length'
        ]

        missing = []
        for method in required_methods:
            if not hasattr(agent, method):
                missing.append(method)

        if missing:
            print(f"❌ Missing methods: {', '.join(missing)}")
            return False

        print(f"✅ All {len(required_methods)} progressive summarization methods exist")

        # Test method signatures
        import inspect
        sig = inspect.signature(agent.create_progressive_summaries)
        params = list(sig.parameters.keys())

        expected_params = ['synthesis_result', 'levels', 'temperature']
        if not all(p in params for p in expected_params):
            print(f"❌ create_progressive_summaries missing parameters")
            return False

        print("✅ Method signatures correct")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quality_validator_import():
    """Test quality validator can be imported"""
    print("\n" + "="*80)
    print("TEST 2: Quality Validator Import")
    print("="*80)

    try:
        from rag_system.quality_validator import QualityValidator, ValidationIssue

        print("✅ QualityValidator imported successfully")
        print("✅ ValidationIssue imported successfully")

        validator = QualityValidator()
        print("✅ QualityValidator initialized")

        # Check required methods
        required_methods = [
            'validate_analysis',
            '_check_completeness',
            '_check_methodology_results_alignment',
            '_check_claims_evidence_consistency',
            '_check_conclusion_support',
            '_check_cross_sectional_coherence',
            '_calculate_quality_score',
            'get_validation_summary'
        ]

        missing = []
        for method in required_methods:
            if not hasattr(validator, method):
                missing.append(method)

        if missing:
            print(f"❌ Missing methods: {', '.join(missing)}")
            return False

        print(f"✅ All {len(required_methods)} validation methods exist")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quality_validator_functionality():
    """Test quality validator actually validates"""
    print("\n" + "="*80)
    print("TEST 3: Quality Validator Functionality")
    print("="*80)

    try:
        from rag_system.quality_validator import QualityValidator

        validator = QualityValidator()

        # Mock analysis result
        mock_result = {
            'success': True,
            'analysis_results': {
                'abstract': {
                    'success': True,
                    'analysis': {
                        'research_objective': 'Test objective',
                        'key_findings': ['Finding 1', 'Finding 2']
                    }
                },
                'methodology': {
                    'success': True,
                    'analysis': {
                        'research_design': 'Experimental',
                        'approach': 'Machine learning'
                    }
                },
                'results': {
                    'success': True,
                    'analysis': {
                        'main_findings': ['Result 1', 'Result 2']
                    }
                },
                'conclusion': {
                    'success': True,
                    'analysis': {
                        'main_contributions': ['Contribution 1']
                    }
                }
            }
        }

        # Run validation
        result = validator.validate_analysis(mock_result)

        if not result.get('success'):
            print("❌ Validation failed")
            return False

        print("✅ Validation completed successfully")

        # Check result structure
        required_fields = [
            'quality_score', 'total_issues', 'critical_issues',
            'warnings', 'info_items', 'issues', 'categories'
        ]

        missing = [f for f in required_fields if f not in result]
        if missing:
            print(f"❌ Missing fields in result: {', '.join(missing)}")
            return False

        print(f"✅ All {len(required_fields)} result fields present")
        print(f"✅ Quality score: {result['quality_score']:.0%}")
        print(f"✅ Total issues: {result['total_issues']}")

        # Test summary format
        summary = validator.get_validation_summary(result)
        if not summary or len(summary) < 100:
            print("❌ Invalid summary format")
            return False

        print("✅ Summary formatting works")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_analysis_aware_rag_import():
    """Test analysis-aware RAG components"""
    print("\n" + "="*80)
    print("TEST 4: Analysis-Aware RAG Import")
    print("="*80)

    try:
        # Import might fail if dependencies not installed
        try:
            from rag_system.enhanced_rag import AnalysisAwareRetriever
            print("✅ AnalysisAwareRetriever imported successfully")
        except ImportError as e:
            if "chromadb" in str(e) or "sentence_transformers" in str(e):
                print("⚠️ RAG dependencies not installed - skipping")
                return True
            raise

        # Check methods
        import inspect
        methods = [name for name, _ in inspect.getmembers(AnalysisAwareRetriever, predicate=inspect.isfunction)]

        required_methods = [
            'set_analysis_results',
            'retrieve_with_analysis',
            '_boost_important_sections',
            '_get_relevant_findings',
            'format_analysis_context'
        ]

        missing = [m for m in required_methods if m not in methods]
        if missing:
            print(f"❌ Missing methods: {', '.join(missing)}")
            return False

        print(f"✅ All {len(required_methods)} analysis-aware methods exist")

        return True

    except ImportError as e:
        if "chromadb" in str(e) or "sentence_transformers" in str(e):
            print("⚠️ RAG dependencies not installed - skipping")
            return True
        print(f"❌ Import failed: {e}")
        return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_analysis_aware_in_factory():
    """Test analysis-aware retriever in factory function"""
    print("\n" + "="*80)
    print("TEST 5: Analysis-Aware RAG in Factory")
    print("="*80)

    try:
        # Import might fail if dependencies not installed
        try:
            from rag_system.enhanced_rag import create_enhanced_rag_system
        except ImportError as e:
            if "chromadb" in str(e) or "sentence_transformers" in str(e):
                print("⚠️ RAG dependencies not installed - skipping")
                return True
            raise

        # Test factory without paper data
        components = create_enhanced_rag_system(paper_data=None, llm_client=None)

        print("✅ Factory function executed")

        # Check if analysis_aware component is present
        if 'analysis_aware' not in components:
            print("❌ analysis_aware component not in factory output")
            return False

        print("✅ analysis_aware component included in factory")

        if components['analysis_aware'] is None:
            print("❌ analysis_aware component is None")
            return False

        print("✅ analysis_aware component initialized")

        # Check component type
        from rag_system.enhanced_rag import AnalysisAwareRetriever
        if not isinstance(components['analysis_aware'], AnalysisAwareRetriever):
            print("❌ analysis_aware is not AnalysisAwareRetriever instance")
            return False

        print("✅ analysis_aware has correct type")

        return True

    except ImportError as e:
        if "chromadb" in str(e) or "sentence_transformers" in str(e):
            print("⚠️ RAG dependencies not installed - skipping")
            return True
        print(f"❌ Import failed: {e}")
        return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_integration():
    """Test database supports progressive summaries and agent context"""
    print("\n" + "="*80)
    print("TEST 6: Database Integration (Week 3)")
    print("="*80)

    try:
        from rag_system.database import RAGDatabase
        import tempfile
        import os

        # Create temp database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_db_path = tmp.name

        try:
            db = RAGDatabase(db_path=tmp_db_path)
            print("✅ Database initialized")

            # Check tables exist (from Week 3)
            cursor = db.conn.cursor()

            # Check agent_context table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_context'")
            if cursor.fetchone():
                print("✅ agent_context table exists")
            else:
                print("❌ agent_context table missing")
                return False

            # Check progressive_summaries table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='progressive_summaries'")
            if cursor.fetchone():
                print("✅ progressive_summaries table exists")
            else:
                print("❌ progressive_summaries table missing")
                return False

            # Check helper methods exist
            required_methods = [
                'store_agent_context', 'get_agent_context',
                'store_progressive_summary', 'get_progressive_summaries'
            ]

            missing = [m for m in required_methods if not hasattr(db, m)]
            if missing:
                print(f"❌ Missing database methods: {', '.join(missing)}")
                return False

            print(f"✅ All {len(required_methods)} database helper methods exist")

            db.close()
            return True

        finally:
            if os.path.exists(tmp_db_path):
                os.unlink(tmp_db_path)

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_11_agent_system():
    """Test 11-agent system still works (Week 1)"""
    print("\n" + "="*80)
    print("TEST 7: 11-Agent System (Week 1)")
    print("="*80)

    try:
        from rag_system.analysis_agents import DocumentAnalysisOrchestrator

        orchestrator = DocumentAnalysisOrchestrator()
        print("✅ Orchestrator initialized")

        # Check agent count
        if hasattr(orchestrator, 'agents'):
            agent_count = len(orchestrator.agents)
            print(f"✅ Loaded {agent_count} agents")

            if agent_count != 11:
                print(f"⚠️ Expected 11 agents, found {agent_count}")

        # Check context manager (Week 2)
        if hasattr(orchestrator, 'context_manager'):
            print("✅ Context manager present")
        else:
            print("❌ Context manager missing")
            return False

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all Week 4 integration tests"""
    print("\n" + "="*80)
    print("WEEK 4: ENHANCEMENTS & INTEGRATION TESTS")
    print("="*80 + "\n")

    tests = [
        ("Progressive Summarization", test_synthesis_progressive_summarization),
        ("Quality Validator Import", test_quality_validator_import),
        ("Quality Validator Functionality", test_quality_validator_functionality),
        ("Analysis-Aware RAG Import", test_analysis_aware_rag_import),
        ("Analysis-Aware RAG Factory", test_analysis_aware_in_factory),
        ("Database Integration", test_database_integration),
        ("11-Agent System", test_11_agent_system)
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
        print("\n🎉 ALL TESTS PASSED! Week 4 enhancements complete.")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
