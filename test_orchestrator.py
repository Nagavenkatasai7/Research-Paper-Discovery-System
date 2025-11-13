"""
Test DocumentAnalysisOrchestrator with Transformer Paper
========================================================
Tests parallel execution of all 7 specialized agents
"""

import sys
import json
from rag_system.analysis_agents import DocumentAnalysisOrchestrator


def test_orchestrator():
    print("=" * 80)
    print("ORCHESTRATOR TEST - All 7 Agents in Parallel")
    print("=" * 80)

    paper_metadata = {
        'title': 'Attention Is All You Need',
        'authors': ['Vaswani et al.'],
        'year': 2017
    }

    pdf_path = "documents/8277bf0bb00823cca9b6ba58b7f42c48.pdf"

    try:
        # Initialize orchestrator
        print("\n🎯 Initializing DocumentAnalysisOrchestrator...")
        orchestrator = DocumentAnalysisOrchestrator()
        print("✓ Orchestrator initialized with 7 specialized agents")

        # Test parallel execution
        print("\n" + "=" * 80)
        print("TEST 1: PARALLEL EXECUTION")
        print("=" * 80)

        result_parallel = orchestrator.analyze_paper(
            pdf_path=pdf_path,
            paper_metadata=paper_metadata,
            parallel=True,
            max_workers=7
        )

        print("\n" + "=" * 80)
        print("PARALLEL EXECUTION RESULTS")
        print("=" * 80)

        if not result_parallel['success']:
            print(f"❌ Failed: {result_parallel.get('message', 'Unknown error')}")
            return False

        metrics = result_parallel['metrics']
        print(f"\n📊 Performance Metrics:")
        print(f"  Total agents: {metrics['total_agents']}")
        print(f"  Successful: {metrics['successful_agents']}")
        print(f"  Failed: {metrics['failed_agents']}")
        print(f"  Total time: {metrics['total_time']:.2f}s")
        print(f"  Total tokens: {metrics['total_tokens']}")
        print(f"  Estimated cost: ${metrics['estimated_cost']:.4f}")
        print(f"  Execution mode: {metrics['execution_mode']}")

        # Show success rate
        success_rate = (metrics['successful_agents'] / metrics['total_agents']) * 100
        print(f"\n✓ Success rate: {success_rate:.1f}%")

        # Display section-wise results
        print(f"\n" + "=" * 80)
        print("SECTION-WISE ANALYSIS SUMMARY")
        print("=" * 80)

        analysis_results = result_parallel['analysis_results']

        for agent_name, agent_result in analysis_results.items():
            print(f"\n{agent_name.upper().replace('_', ' ')}:")
            print("-" * 80)

            if agent_result.get('success'):
                elapsed = agent_result.get('elapsed_time', 0)
                tokens = agent_result.get('tokens_used', 0)
                print(f"  ✓ Success")
                print(f"  Time: {elapsed:.2f}s")
                print(f"  Tokens: {tokens}")

                # Show first key finding
                analysis = agent_result.get('analysis', {})
                if analysis and not isinstance(analysis, str):
                    # Get first non-empty field
                    for key, value in analysis.items():
                        if key == 'parse_error':
                            continue
                        if isinstance(value, list) and value:
                            print(f"  {key}: {len(value)} items")
                            break
                        elif isinstance(value, str) and value and len(value) > 20:
                            preview = value[:150] + "..." if len(value) > 150 else value
                            print(f"  {key}: {preview}")
                            break
            else:
                print(f"  ❌ Failed: {agent_result.get('message', 'Unknown error')}")

        # Test sequential execution for comparison
        print("\n\n" + "=" * 80)
        print("TEST 2: SEQUENTIAL EXECUTION (for comparison)")
        print("=" * 80)

        result_sequential = orchestrator.analyze_paper(
            pdf_path=pdf_path,
            paper_metadata=paper_metadata,
            parallel=False
        )

        if result_sequential['success']:
            metrics_seq = result_sequential['metrics']
            print(f"\n📊 Sequential Performance:")
            print(f"  Total time: {metrics_seq['total_time']:.2f}s")
            print(f"  Total tokens: {metrics_seq['total_tokens']}")
            print(f"  Success: {metrics_seq['successful_agents']}/{metrics_seq['total_agents']}")

            # Calculate speedup
            if metrics_seq['total_time'] > 0:
                speedup = metrics_seq['total_time'] / metrics['total_time']
                print(f"\n⚡ Speedup: {speedup:.2f}x faster with parallel execution")

        # Test formatted summary
        print("\n\n" + "=" * 80)
        print("TEST 3: FORMATTED SUMMARY")
        print("=" * 80)

        summary = orchestrator.format_summary(result_parallel)
        print("\n" + summary[:1000] + "\n...")

        # Save results
        print("\n" + "=" * 80)
        print("SAVING RESULTS")
        print("=" * 80)

        with open("test_results_orchestrator_parallel.json", 'w') as f:
            json.dump(result_parallel, f, indent=2)
        print("✓ Parallel results saved to: test_results_orchestrator_parallel.json")

        with open("test_results_orchestrator_sequential.json", 'w') as f:
            json.dump(result_sequential, f, indent=2)
        print("✓ Sequential results saved to: test_results_orchestrator_sequential.json")

        # Final validation
        print("\n" + "=" * 80)
        print("VALIDATION")
        print("=" * 80)

        validation_passed = True
        errors = []

        # Check all agents executed
        expected_agents = ['abstract', 'introduction', 'literature_review',
                          'methodology', 'results', 'discussion', 'conclusion']

        for agent in expected_agents:
            if agent not in analysis_results:
                errors.append(f"Missing agent: {agent}")
                validation_passed = False

        # Check success rate
        if metrics['successful_agents'] < 5:  # At least 5/7 should succeed
            errors.append(f"Low success rate: {metrics['successful_agents']}/7")
            validation_passed = False

        # Check performance
        if metrics['total_time'] > 60:  # Should complete in under 60s
            errors.append(f"Slow execution: {metrics['total_time']:.2f}s > 60s")
            validation_passed = False

        if validation_passed:
            print("✅ All validation checks passed!")
            print(f"   - All 7 agents executed")
            print(f"   - Success rate: {success_rate:.1f}%")
            print(f"   - Performance: {metrics['total_time']:.2f}s")
        else:
            print("❌ Validation failed:")
            for error in errors:
                print(f"   - {error}")

        print("\n" + "=" * 80)
        if validation_passed:
            print("✅ ORCHESTRATOR TEST PASSED!")
        else:
            print("⚠️  ORCHESTRATOR TEST COMPLETED WITH WARNINGS")
        print("=" * 80)

        return validation_passed

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_orchestrator()
    sys.exit(0 if success else 1)
