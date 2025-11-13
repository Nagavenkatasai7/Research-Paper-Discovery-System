"""
Complete Pipeline Test - Orchestrator + Synthesis
==================================================
Tests the full multi-agent analysis system with synthesis
"""

import sys
import json
from rag_system.analysis_agents import DocumentAnalysisOrchestrator, SynthesisAgent


def test_full_pipeline():
    print("=" * 80)
    print("FULL PIPELINE TEST - 7 Agents + Synthesis")
    print("=" * 80)

    paper_metadata = {
        'title': 'Attention Is All You Need',
        'authors': ['Vaswani et al.'],
        'year': 2017
    }

    pdf_path = "documents/8277bf0bb00823cca9b6ba58b7f42c48.pdf"

    try:
        # Step 1: Run Orchestrator
        print("\n" + "=" * 80)
        print("STEP 1: MULTI-AGENT ANALYSIS")
        print("=" * 80)

        print("\n🎯 Initializing DocumentAnalysisOrchestrator...")
        orchestrator = DocumentAnalysisOrchestrator()

        print("⚡ Running all 7 agents in parallel...")
        comprehensive_result = orchestrator.analyze_paper(
            pdf_path=pdf_path,
            paper_metadata=paper_metadata,
            parallel=True,
            max_workers=7
        )

        if not comprehensive_result['success']:
            print(f"❌ Orchestrator failed: {comprehensive_result.get('message')}")
            return False

        metrics = comprehensive_result['metrics']
        print(f"\n✅ Multi-agent analysis complete!")
        print(f"   Time: {metrics['total_time']:.2f}s")
        print(f"   Agents: {metrics['successful_agents']}/{metrics['total_agents']}")
        print(f"   Tokens: {metrics['total_tokens']}")
        print(f"   Cost: ${metrics['estimated_cost']:.4f}")

        # Step 2: Run Synthesis Agent
        print("\n" + "=" * 80)
        print("STEP 2: SYNTHESIS")
        print("=" * 80)

        print("\n🔬 Initializing SynthesisAgent...")
        synthesizer = SynthesisAgent()

        print("⏳ Synthesizing findings from all agents...")
        synthesis_result = synthesizer.synthesize(comprehensive_result)

        if not synthesis_result['success']:
            print(f"❌ Synthesis failed: {synthesis_result.get('message')}")
            return False

        print(f"\n✅ Synthesis complete!")
        print(f"   Time: {synthesis_result['elapsed_time']:.2f}s")
        print(f"   Tokens: {synthesis_result.get('tokens_used', 0)}")

        # Step 3: Display Results
        print("\n" + "=" * 80)
        print("COMPREHENSIVE SYNTHESIS RESULTS")
        print("=" * 80)

        synthesis = synthesis_result.get('synthesis', {})

        # Executive Summary
        print("\n📋 EXECUTIVE SUMMARY:")
        print("-" * 80)
        exec_summary = synthesis.get('executive_summary', 'N/A')
        # Word-wrap the summary
        words = exec_summary.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 <= 80:
                line += word + " "
            else:
                print(line.strip())
                line = word + " "
        if line:
            print(line.strip())

        # Key Contributions
        print("\n🎯 KEY CONTRIBUTIONS:")
        print("-" * 80)
        contributions = synthesis.get('key_contributions', [])
        if contributions:
            for i, contrib in enumerate(contributions, 1):
                print(f"  {i}. {contrib}")
        else:
            print("  None identified")

        # Research Context
        print("\n🔍 RESEARCH CONTEXT:")
        print("-" * 80)
        context = synthesis.get('research_context', 'N/A')
        words = context.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 <= 80:
                line += word + " "
            else:
                print(line.strip())
                line = word + " "
        if line:
            print(line.strip())

        # Strengths
        print("\n💪 STRENGTHS:")
        print("-" * 80)
        strengths = synthesis.get('strengths', [])
        if strengths:
            for i, strength in enumerate(strengths, 1):
                print(f"  {i}. {strength}")
        else:
            print("  None identified")

        # Limitations
        print("\n⚠️  LIMITATIONS:")
        print("-" * 80)
        limitations = synthesis.get('limitations', [])
        if limitations:
            for i, lim in enumerate(limitations, 1):
                print(f"  {i}. {lim}")
        else:
            print("  None identified")

        # Future Directions
        print("\n🔮 FUTURE DIRECTIONS:")
        print("-" * 80)
        future = synthesis.get('future_directions', [])
        if future:
            for i, direction in enumerate(future, 1):
                print(f"  {i}. {direction}")
        else:
            print("  None identified")

        # Overall Assessment
        print("\n📊 OVERALL ASSESSMENT:")
        print("-" * 80)
        assessment = synthesis.get('overall_assessment', {})
        print(f"  Quality: {assessment.get('quality', 'N/A')}")
        print(f"  Novelty: {assessment.get('novelty', 'N/A')}")
        print(f"  Impact: {assessment.get('impact', 'N/A')}")
        print(f"  Rigor: {assessment.get('rigor', 'N/A')}")

        # Key Takeaways
        print("\n💡 KEY TAKEAWAYS:")
        print("-" * 80)
        takeaways = synthesis.get('key_takeaways', [])
        if takeaways:
            for i, takeaway in enumerate(takeaways, 1):
                print(f"  {i}. {takeaway}")
        else:
            print("  None identified")

        # Recommended Audience
        print("\n👥 RECOMMENDED AUDIENCE:")
        print("-" * 80)
        audience = synthesis.get('recommended_audience', 'N/A')
        words = audience.split()
        line = ""
        for word in words:
            if len(line) + len(word) + 1 <= 80:
                line += word + " "
            else:
                print(line.strip())
                line = word + " "
        if line:
            print(line.strip())

        # Overall Performance
        print("\n" + "=" * 80)
        print("OVERALL PIPELINE PERFORMANCE")
        print("=" * 80)

        total_time = metrics['total_time'] + synthesis_result['elapsed_time']
        total_tokens = metrics['total_tokens'] + synthesis_result.get('tokens_used', 0)
        total_cost = total_tokens * 0.000009

        print(f"\nPhase 1 - Multi-Agent Analysis:")
        print(f"  Time: {metrics['total_time']:.2f}s")
        print(f"  Tokens: {metrics['total_tokens']}")
        print(f"  Cost: ${metrics['estimated_cost']:.4f}")

        print(f"\nPhase 2 - Synthesis:")
        print(f"  Time: {synthesis_result['elapsed_time']:.2f}s")
        print(f"  Tokens: {synthesis_result.get('tokens_used', 0)}")
        print(f"  Cost: ${(synthesis_result.get('tokens_used', 0) * 0.000009):.4f}")

        print(f"\nTotal Pipeline:")
        print(f"  Time: {total_time:.2f}s")
        print(f"  Tokens: {total_tokens}")
        print(f"  Cost: ${total_cost:.4f}")
        print(f"  Agents used: {metrics['total_agents']} + 1 synthesis")

        # Save results
        print("\n" + "=" * 80)
        print("SAVING RESULTS")
        print("=" * 80)

        # Save comprehensive result
        with open("test_results_full_pipeline.json", 'w') as f:
            json.dump({
                'orchestrator_result': comprehensive_result,
                'synthesis_result': synthesis_result,
                'performance': {
                    'total_time': total_time,
                    'total_tokens': total_tokens,
                    'total_cost': total_cost
                }
            }, f, indent=2)
        print("✓ Full pipeline results saved to: test_results_full_pipeline.json")

        # Generate formatted synthesis report
        formatted_synthesis = synthesizer.format_synthesis(synthesis_result)
        with open("SYNTHESIS_REPORT.txt", 'w') as f:
            f.write(formatted_synthesis)
        print("✓ Synthesis report saved to: SYNTHESIS_REPORT.txt")

        # Validation
        print("\n" + "=" * 80)
        print("VALIDATION")
        print("=" * 80)

        validation_passed = True
        errors = []

        # Check orchestrator success
        if metrics['successful_agents'] < 5:
            errors.append(f"Low agent success rate: {metrics['successful_agents']}/7")
            validation_passed = False

        # Check synthesis success
        if 'parse_error' in synthesis:
            errors.append("Synthesis JSON parsing failed")
            validation_passed = False

        # Check performance
        if total_time > 90:
            errors.append(f"Pipeline too slow: {total_time:.2f}s > 90s")
            validation_passed = False

        # Check synthesis quality
        if not synthesis.get('executive_summary') or len(synthesis.get('executive_summary', '')) < 100:
            errors.append("Executive summary too short or missing")
            validation_passed = False

        if len(synthesis.get('key_contributions', [])) < 2:
            errors.append("Too few key contributions identified")
            validation_passed = False

        if validation_passed:
            print("✅ All validation checks passed!")
            print(f"   - {metrics['successful_agents']}/7 agents successful")
            print(f"   - Synthesis generated successfully")
            print(f"   - Pipeline completed in {total_time:.2f}s")
            print(f"   - Total cost: ${total_cost:.4f}")
        else:
            print("❌ Validation failed:")
            for error in errors:
                print(f"   - {error}")

        print("\n" + "=" * 80)
        if validation_passed:
            print("✅ FULL PIPELINE TEST PASSED!")
        else:
            print("⚠️  FULL PIPELINE TEST COMPLETED WITH WARNINGS")
        print("=" * 80)

        print("\n📄 See SYNTHESIS_REPORT.txt for the complete formatted synthesis")

        return validation_passed

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)
