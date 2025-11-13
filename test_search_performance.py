"""
Quick Performance Test - Multi-Agent Search
Tests actual search speed with current configuration
"""

import time
from api_clients import MultiAPISearcher

print("\n" + "="*80)
print("MULTI-AGENT SEARCH PERFORMANCE TEST")
print("="*80)

searcher = MultiAPISearcher()
query = "transformer neural networks"

print(f"\nQuery: '{query}'")
print(f"Configuration:")
print(f"  - Max results: 20")
print(f"  - Sources: semantic_scholar, arxiv")
print(f"  - Note: App uses multi-agent orchestrator with all 6 sources")

print("\n" + "-"*80)
print("Running parallel search...")
print("-"*80)

start_time = time.time()

results = searcher.search_all(
    query=query,
    sources=['semantic_scholar', 'arxiv'],
    max_results=20
)

elapsed_time = time.time() - start_time

print("\n" + "="*80)
print("RESULTS")
print("="*80)
print(f"\n✅ Search completed successfully!")
print(f"   Total time: {elapsed_time:.2f} seconds")
print(f"   Total results: {len(results)} papers")
print(f"   Average speed: {len(results)/elapsed_time:.1f} papers/second")

# Source breakdown
source_counts = {}
for paper in results:
    source = paper.get('source', 'unknown')
    source_counts[source] = source_counts.get(source, 0) + 1

print(f"\n📊 Results by source:")
for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"   {source:20s}: {count:3d} papers")

# Performance verdict
print(f"\n⚡ Performance Verdict:")
if elapsed_time < 10:
    print("   🚀 EXCELLENT - Under 10 seconds")
elif elapsed_time < 20:
    print("   ✅ GOOD - Under 20 seconds")
elif elapsed_time < 30:
    print("   ⚠️  ACCEPTABLE - Under 30 seconds")
else:
    print("   ❌ SLOW - Over 30 seconds")

print("\n" + "="*80)
