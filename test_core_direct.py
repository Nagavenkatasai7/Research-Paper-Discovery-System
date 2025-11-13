#!/usr/bin/env python3
"""
Direct test of CORE Agent with 10-year date range
"""

from multi_agent_system import COREAgent

print("=" * 80)
print("DIRECT CORE AGENT TEST (with 10-year date range)")
print("=" * 80)

# Create CORE agent
core_agent = COREAgent(api_key='kMnptdQvBGqrPOXJmUau0Hj51FC9T43w')

print("\n[Step 1] Running CORE agent search...")
print("Query: 'machine learning neural networks'")
print("Max results: 20")
print("Smart search: True (with 10-year date range)")

results = core_agent.search(
    query="machine learning neural networks",
    max_results=20,
    smart_search=True
)

print(f"\n[Step 2] Results:")
print(f"Status: {core_agent.status}")
print(f"Error: {core_agent.error or 'None'}")
print(f"Results count: {len(results)}")
print(f"Duration: {core_agent.get_metrics()['duration']:.2f}s")

if results:
    print(f"\n[Step 3] Sample papers:")
    for i, paper in enumerate(results[:3], 1):
        print(f"\n   Paper {i}:")
        print(f"   Title: {paper.get('title', 'N/A')[:60]}...")
        print(f"   Year: {paper.get('year', 'N/A')}")
        print(f"   Citations: {paper.get('citations', 'N/A')}")
        print(f"   Relevance: {paper.get('relevance_score', 'N/A')}")
else:
    print(f"\n❌ No papers returned")
    print(f"   This means papers were filtered out by smart search")

print("\n" + "=" * 80)
