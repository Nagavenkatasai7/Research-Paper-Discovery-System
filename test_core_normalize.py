#!/usr/bin/env python3
"""
Test CORE API normalization and filtering
"""

import requests
from extended_api_clients import COREClient
from smart_search_utils import smart_search_filter, get_year_range

API_KEY = 'kMnptdQvBGqrPOXJmUau0Hj51FC9T43w'

print("=" * 80)
print("CORE API NORMALIZATION & FILTERING TEST")
print("=" * 80)

# Create client
client = COREClient(API_KEY)

# Get raw papers
print("\n[Step 1] Fetching raw papers from CORE...")
papers = client.search_papers("machine learning neural networks", max_results=20)
print(f"✅ Retrieved {len(papers)} papers from CORE")

if papers:
    print(f"\n[Step 2] First paper details:")
    print(f"   Title: {papers[0].get('title', 'N/A')[:60]}...")
    print(f"   Year: {papers[0].get('year', 'N/A')}")
    print(f"   Citations: {papers[0].get('citations', 'N/A')}")
    print(f"   Source: {papers[0].get('source', 'N/A')}")
    print(f"   DOI: {papers[0].get('doi', 'N/A')}")

    # Show year distribution
    print(f"\n[Step 3] Year distribution:")
    year_counts = {}
    for paper in papers:
        year = paper.get('year', 'Unknown')
        year_counts[year] = year_counts.get(year, 0) + 1

    for year, count in sorted(year_counts.items(), key=lambda x: str(x[0]), reverse=True):
        print(f"   {year}: {count} papers")

    # Test smart filtering
    print(f"\n[Step 4] Applying smart search filter...")
    min_year, max_year = get_year_range(years_back=5)
    print(f"   Year range: {min_year} - {max_year}")

    filtered = smart_search_filter(
        papers,
        "machine learning neural networks",
        min_year=min_year,
        max_year=max_year,
        adaptive_citations=True,
        rank_by_relevance_score=True
    )

    print(f"   Before filtering: {len(papers)} papers")
    print(f"   After filtering: {len(filtered)} papers")
    print(f"   Filtered out: {len(papers) - len(filtered)} papers")

    if filtered:
        print(f"\n[Step 5] Top result after filtering:")
        top = filtered[0]
        print(f"   Title: {top.get('title', 'N/A')[:60]}...")
        print(f"   Year: {top.get('year', 'N/A')}")
        print(f"   Citations: {top.get('citations', 'N/A')}")
        print(f"   Relevance: {top.get('relevance_score', 'N/A'):.2f}")
    else:
        print(f"\n❌ All papers filtered out!")
        print(f"   Likely reasons:")
        print(f"   1. Papers too old (before {min_year})")
        print(f"   2. Citation threshold too high (CORE doesn't provide citations)")
        print(f"   3. Relevance score too low")

else:
    print(f"\n❌ No papers retrieved from CORE API")

print("\n" + "=" * 80)
