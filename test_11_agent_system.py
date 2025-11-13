"""
Test 11-Agent System Integration
==================================

Verify that all 11 agents (7 original + 4 new) are properly integrated
and can be instantiated without errors.
"""

import sys
from pathlib import Path

def test_agent_imports():
    """Test that all 11 agents can be imported"""
    print("="*80)
    print("TEST 1: Agent Imports")
    print("="*80)

    try:
        from rag_system.analysis_agents import (
            AbstractAgent,
            IntroductionAgent,
            LiteratureReviewAgent,
            MethodologyAgent,
            ResultsAgent,
            DiscussionAgent,
            ConclusionAgent,
            ReferencesAgent,
            TablesAgent,
            FiguresAgent,
            MathAgent,
            DocumentAnalysisOrchestrator
        )
        print("✅ All 11 agents imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_instantiation():
    """Test that all 11 agents can be instantiated"""
    print("\n" + "="*80)
    print("TEST 2: Agent Instantiation")
    print("="*80)

    try:
        from rag_system.analysis_agents import (
            AbstractAgent,
            IntroductionAgent,
            LiteratureReviewAgent,
            MethodologyAgent,
            ResultsAgent,
            DiscussionAgent,
            ConclusionAgent,
            ReferencesAgent,
            TablesAgent,
            FiguresAgent,
            MathAgent
        )

        agents = {
            'Abstract': AbstractAgent(),
            'Introduction': IntroductionAgent(),
            'Literature Review': LiteratureReviewAgent(),
            'Methodology': MethodologyAgent(),
            'Results': ResultsAgent(),
            'Discussion': DiscussionAgent(),
            'Conclusion': ConclusionAgent(),
            'References': ReferencesAgent(),
            'Tables': TablesAgent(),
            'Figures': FiguresAgent(),
            'Mathematics': MathAgent()
        }

        for name, agent in agents.items():
            print(f"✅ {name}: {agent.agent_name} - {agent.section_name}")

        print(f"\n✅ All {len(agents)} agents instantiated successfully")
        return True

    except Exception as e:
        print(f"❌ Instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator_initialization():
    """Test that orchestrator initializes with all 11 agents"""
    print("\n" + "="*80)
    print("TEST 3: Orchestrator Initialization")
    print("="*80)

    try:
        from rag_system.analysis_agents import DocumentAnalysisOrchestrator

        orchestrator = DocumentAnalysisOrchestrator()

        print(f"✅ Orchestrator initialized")
        print(f"   Total agents: {len(orchestrator.agents)}")
        print(f"\n   Agents:")
        for agent_name in orchestrator.agents.keys():
            agent = orchestrator.agents[agent_name]
            print(f"   - {agent_name}: {agent.section_name}")

        # Verify we have exactly 11 agents
        expected_count = 11
        actual_count = len(orchestrator.agents)

        if actual_count == expected_count:
            print(f"\n✅ Orchestrator has correct number of agents: {actual_count}/{expected_count}")
            return True
        else:
            print(f"\n❌ Agent count mismatch: {actual_count}/{expected_count}")
            return False

    except Exception as e:
        print(f"❌ Orchestrator initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_section_strategies():
    """Test that section strategies are defined for all 11 agents"""
    print("\n" + "="*80)
    print("TEST 4: Section Extraction Strategies")
    print("="*80)

    try:
        from rag_system.analysis_agents import DocumentAnalysisOrchestrator

        orchestrator = DocumentAnalysisOrchestrator()

        print(f"Section strategies defined:")
        for section_name, strategy in orchestrator.section_strategies.items():
            print(f"\n   {section_name}:")
            print(f"      Keys: {strategy['keys'][:2]}...")
            print(f"      Pages: {strategy['pages']}")
            print(f"      Max chars: {strategy['max_chars']}")

        # Verify all agents have strategies
        agents_with_strategies = set(orchestrator.section_strategies.keys())
        all_agents = set(orchestrator.agents.keys())

        if agents_with_strategies == all_agents:
            print(f"\n✅ All {len(all_agents)} agents have extraction strategies")
            return True
        else:
            missing = all_agents - agents_with_strategies
            extra = agents_with_strategies - all_agents
            print(f"\n❌ Strategy mismatch:")
            if missing:
                print(f"   Missing strategies: {missing}")
            if extra:
                print(f"   Extra strategies: {extra}")
            return False

    except Exception as e:
        print(f"❌ Section strategy test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_prompts():
    """Test that each agent has proper system and user prompts"""
    print("\n" + "="*80)
    print("TEST 5: Agent Prompt Systems")
    print("="*80)

    try:
        from rag_system.analysis_agents import (
            ReferencesAgent,
            TablesAgent,
            FiguresAgent,
            MathAgent
        )

        # Test the 4 new agents
        new_agents = {
            'References': ReferencesAgent(),
            'Tables': TablesAgent(),
            'Figures': FiguresAgent(),
            'Mathematics': MathAgent()
        }

        test_metadata = {
            'title': 'Test Paper',
            'authors': ['Smith', 'Jones'],
            'year': 2024
        }

        for name, agent in new_agents.items():
            # Test system prompt
            system_prompt = agent.get_system_prompt()
            assert len(system_prompt) > 100, f"{name} system prompt too short"
            print(f"✅ {name} system prompt: {len(system_prompt)} characters")

            # Test user prompt
            user_prompt = agent.get_user_prompt("Sample text for testing", test_metadata)
            assert len(user_prompt) > 50, f"{name} user prompt too short"
            print(f"✅ {name} user prompt: {len(user_prompt)} characters")

        print(f"\n✅ All 4 new agents have proper prompt systems")
        return True

    except Exception as e:
        print(f"❌ Prompt test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("11-AGENT SYSTEM INTEGRATION TESTS")
    print("="*80 + "\n")

    tests = [
        ("Agent Imports", test_agent_imports),
        ("Agent Instantiation", test_agent_instantiation),
        ("Orchestrator Initialization", test_orchestrator_initialization),
        ("Section Strategies", test_section_strategies),
        ("Agent Prompts", test_agent_prompts)
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
        print("\n🎉 ALL TESTS PASSED! 11-agent system is fully integrated.")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
