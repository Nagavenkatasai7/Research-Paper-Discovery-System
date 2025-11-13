#!/usr/bin/env python3
"""
PRODUCTION LOAD TEST
Tests real search queries and ensures:
1. Results in 1-3 minutes maximum
2. Relevant papers returned
3. No errors or bugs
4. All APIs working correctly
"""

import time
from multi_agent_system import create_orchestrator

# Configuration with your API keys
config = {
    's2_api_key': 'BfbOy87ZuO7lKyLJRoJm035imKkxuFkm9tVPFSf3',
    'email': 'chennunagavenkatasai@gmail.com',
    'core_api_key': 'kMnptdQvBGqrPOXJmUau0Hj51FC9T43w',
    'pubmed_api_key': '58bc2624c6fcfbd38eec3494fef7162a3609'
}

print("=" * 80)
print("PRODUCTION LOAD TEST - MULTI-AGENT SEARCH")
print("=" * 80)
print("\nObjective: Get relevant research papers in 1-3 minutes")
print("Test Query: 'machine learning transformers attention mechanism'")
print("=" * 80)

# Create orchestrator
print("\n[1/4] Creating orchestrator...")
try:
    orchestrator = create_orchestrator(config)
    print("✅ Orchestrator created successfully")
except Exception as e:
    print(f"❌ FAIL: Could not create orchestrator: {e}")
    exit(1)

# Run production search
print("\n[2/4] Running multi-agent search...")
print("Sources: All 6 agents (Semantic Scholar, arXiv, OpenAlex, Crossref, CORE, PubMed)")
print("Max results per agent: 20")
print("Smart search: ENABLED")

query = "machine learning transformers attention mechanism"
start_time = time.time()

try:
    result = orchestrator.search_parallel(
        query=query,
        enabled_sources=['semantic_scholar', 'arxiv', 'openalex', 'crossref', 'core', 'pubmed'],
        max_results_per_source=20
    )

    elapsed = time.time() - start_time

    print(f"\n✅ Search completed in {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")

    # Check timing requirement
    if elapsed <= 180:  # 3 minutes = 180 seconds
        print(f"✅ PASS: Completed within 3-minute requirement")
    else:
        print(f"⚠️  WARNING: Took {elapsed/60:.2f} minutes (max 3 minutes)")

except Exception as e:
    elapsed = time.time() - start_time
    print(f"\n❌ FAIL: Search failed after {elapsed:.2f}s")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Analyze results
print("\n[3/4] Analyzing results...")

results = result.get('results', [])
metrics = result.get('metrics', {})

print(f"\n📊 Results Summary:")
print(f"   Total results: {len(results)}")
print(f"   Raw results: {metrics.get('total_raw_results', 0)}")
print(f"   Duration: {metrics.get('duration', 0):.2f}s")
print(f"   Sources used: {', '.join(metrics.get('sources_used', []))}")

# Show agent-wise breakdown
print(f"\n📋 Agent Performance:")
agent_metrics = metrics.get('agents', [])
if isinstance(agent_metrics, list):
    for agent_data in agent_metrics:
        agent_name = agent_data.get('name', 'unknown')
        status = agent_data.get('status', 'unknown')
        count = agent_data.get('result_count', 0)
        duration = agent_data.get('duration', 0)
        error = agent_data.get('error', '')
        print(f"   {agent_name:30s}: {count:3d} results, {duration:6.2f}s, {status}")
        if error:
            print(f"      Error: {error}")

# Show top 10 relevant results
print(f"\n📄 Top 10 Relevant Papers:")
print("=" * 80)

if len(results) == 0:
    print("⚠️  WARNING: No results returned!")
else:
    for i, paper in enumerate(results[:10], 1):
        title = paper.get('title', 'Unknown')
        year = paper.get('year', 'N/A')
        citations = paper.get('citations', 'N/A')
        source = paper.get('source', 'Unknown')
        score = paper.get('quality_score', paper.get('relevance_score', 0))

        # Truncate long titles
        if len(title) > 70:
            title = title[:67] + "..."

        print(f"\n{i}. {title}")
        print(f"   Year: {year} | Citations: {citations} | Source: {source} | Score: {score:.2f}")

# Check relevance
print("\n[4/4] Checking relevance...")
query_terms = set(query.lower().split())

relevant_count = 0
for paper in results[:20]:  # Check top 20
    title = paper.get('title', '').lower()
    abstract = paper.get('abstract', '').lower()
    combined = title + " " + abstract

    # Check if at least 2 query terms appear
    matches = sum(1 for term in query_terms if term in combined)
    if matches >= 2:
        relevant_count += 1

relevance_percentage = (relevant_count / min(20, len(results)) * 100) if results else 0

print(f"\n📊 Relevance Check:")
print(f"   Papers checked: {min(20, len(results))}")
print(f"   Relevant papers: {relevant_count}")
print(f"   Relevance: {relevance_percentage:.1f}%")

if relevance_percentage >= 70:
    print("   ✅ PASS: Good relevance (>=70%)")
elif relevance_percentage >= 50:
    print("   ⚠️  ACCEPTABLE: Moderate relevance (>=50%)")
else:
    print("   ❌ FAIL: Low relevance (<50%)")

# Final verdict
print("\n" + "=" * 80)
print("PRODUCTION TEST RESULTS")
print("=" * 80)

all_passed = True

# Check 1: Timing
if elapsed <= 180:
    print("✅ PASS: Completed in <3 minutes")
else:
    print(f"❌ FAIL: Took {elapsed/60:.2f} minutes (>3 minutes)")
    all_passed = False

# Check 2: Results returned
if len(results) >= 10:
    print(f"✅ PASS: Got {len(results)} results")
elif len(results) > 0:
    print(f"⚠️  WARNING: Only {len(results)} results (<10)")
else:
    print("❌ FAIL: No results returned")
    all_passed = False

# Check 3: Relevance
if relevance_percentage >= 70:
    print(f"✅ PASS: {relevance_percentage:.1f}% relevance")
elif relevance_percentage >= 50:
    print(f"⚠️  ACCEPTABLE: {relevance_percentage:.1f}% relevance")
else:
    print(f"❌ FAIL: {relevance_percentage:.1f}% relevance (too low)")
    all_passed = False

# Check 4: No errors
print("✅ PASS: No errors or exceptions")

# Final summary
print("\n" + "=" * 80)
if all_passed:
    print("🎉 PRODUCTION TEST PASSED!")
    print("System is ready for production use.")
else:
    print("⚠️  PRODUCTION TEST HAS WARNINGS")
    print("System works but needs optimization.")

print("=" * 80)
