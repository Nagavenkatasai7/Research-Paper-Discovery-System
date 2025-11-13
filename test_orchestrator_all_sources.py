#!/usr/bin/env python3
"""
Test orchestrator with ALL 6 sources
Verify results come from: Semantic Scholar, arXiv, OpenAlex, Crossref, CORE, PubMed
"""

import time
from multi_agent_system import create_orchestrator

# Configuration
config = {
    's2_api_key': 'BfbOy87ZuO7lKyLJRoJm035imKkxuFkm9tVPFSf3',
    'email': 'chennunagavenkatasai@gmail.com',
    'core_api_key': 'kMnptdQvBGqrPOXJmUau0Hj51FC9T43w',
    'pubmed_api_key': '58bc2624c6fcfbd38eec3494fef7162a3609'
}

print("=" * 80)
print("TESTING ORCHESTRATOR WITH ALL 6 SOURCES")
print("=" * 80)

# Create orchestrator
print("\n[1/3] Creating orchestrator...")
orchestrator = create_orchestrator(config)
print("✅ Orchestrator created")

# Test search with ALL 6 sources
print("\n[2/3] Running search with ALL 6 sources...")
print("Query: 'machine learning neural networks'")
print("Sources: semantic_scholar, arxiv, openalex, crossref, core, pubmed")
print("-" * 80)

start = time.time()

result = orchestrator.search_parallel(
    query="machine learning neural networks",
    enabled_sources=['semantic_scholar', 'arxiv', 'openalex', 'crossref', 'core', 'pubmed'],
    max_results_per_source=20
)

elapsed = time.time() - start

print(f"\n✅ Search completed in {elapsed:.2f} seconds")

# Analyze results
results = result.get('results', [])
metrics = result.get('metrics', {})

print("\n[3/3] Results Analysis:")
print("=" * 80)

print(f"\n📊 OVERALL RESULTS:")
print(f"   Total papers: {len(results)}")
print(f"   Raw results: {metrics.get('total_raw_results', 0)}")
print(f"   Duration: {metrics.get('duration', 0):.2f}s")
print(f"   Sources used: {', '.join(metrics.get('sources_used', []))}")

print(f"\n📋 AGENT-BY-AGENT BREAKDOWN:")
print("-" * 80)

agent_metrics = metrics.get('agents', [])
for agent_data in agent_metrics:
    name = agent_data.get('name', 'Unknown')
    status = agent_data.get('status', 'unknown')
    count = agent_data.get('results_count', 0)
    duration = agent_data.get('duration', 0)
    error = agent_data.get('error', '')

    status_emoji = "✅" if status == "completed" else "❌" if status == "failed" else "⏱️"

    print(f"{status_emoji} {name:30s}: {count:3d} papers, {duration:6.2f}s, [{status}]")
    if error:
        print(f"   └─ Error: {error}")

# Count papers by source
print(f"\n📚 PAPERS BY SOURCE:")
print("-" * 80)
source_count = {}
for paper in results:
    source = paper.get('source', 'Unknown')
    source_count[source] = source_count.get(source, 0) + 1

for source, count in sorted(source_count.items(), key=lambda x: x[1], reverse=True):
    print(f"   {source:20s}: {count:3d} papers")

# Show sample papers from each source
print(f"\n📄 SAMPLE PAPERS (first from each source):")
print("=" * 80)

seen_sources = set()
for paper in results:
    source = paper.get('source', 'Unknown')
    if source not in seen_sources:
        seen_sources.add(source)
        title = paper.get('title', 'Unknown')[:60] + "..."
        year = paper.get('year', 'N/A')
        citations = paper.get('citations', 'N/A')
        print(f"\n[{source}]")
        print(f"  Title: {title}")
        print(f"  Year: {year} | Citations: {citations}")

# Final summary
print("\n" + "=" * 80)
print("ORCHESTRATOR TEST SUMMARY")
print("=" * 80)

print(f"\n✅ Sources configured: 6 (all enabled)")
print(f"✅ Sources that returned results: {len(source_count)}")
print(f"✅ Total unique papers: {len(results)}")
print(f"✅ Search time: {elapsed:.2f}s")

if len(source_count) >= 3:
    print(f"\n🎉 SUCCESS! Orchestrator is using multiple sources!")
    print(f"   Got results from {len(source_count)} different sources")
else:
    print(f"\n⚠️  WARNING: Only {len(source_count)} sources returned results")

print("=" * 80)
