#!/usr/bin/env python3
"""
Performance Diagnostic Tool
Measures actual API performance to identify bottlenecks
"""

import time
from multi_agent_system import create_orchestrator

config = {
    's2_api_key': 'BfbOy87ZuO7lKyLJRoJm035imKkxuFkm9tVPFSf3',
    'email': 'chennunagavenkatasai@gmail.com',
    'core_api_key': 'kMnptdQvBGqrPOXJmUau0Hj51FC9T43w',
    'pubmed_api_key': '58bc2624c6fcfbd38eec3494fef7162a3609'
}

print("=" * 80)
print("PERFORMANCE DIAGNOSTIC")
print("=" * 80)

orchestrator = create_orchestrator(config)
agent = orchestrator.agents['semantic_scholar']

# Test 1: WITHOUT smart search
print("\n1. Testing WITHOUT smart search (10 results)...")
start = time.time()
results_basic = agent.search("machine learning", max_results=10, smart_search=False)
time_basic = time.time() - start
print(f"   Time: {time_basic:.2f}s")
print(f"   Results: {len(results_basic)}")

# Test 2: WITH smart search
print("\n2. Testing WITH smart search (10 results, fetches 20)...")
start = time.time()
results_smart = agent.search("machine learning", max_results=10, smart_search=True)
time_smart = time.time() - start
print(f"   Time: {time_smart:.2f}s")
print(f"   Results: {len(results_smart)}")
print(f"   Overhead: {time_smart - time_basic:.2f}s ({((time_smart/time_basic - 1) * 100):.0f}% slower)")

# Test 3: Larger request
print("\n3. Testing WITH smart search (50 results, fetches 100)...")
start = time.time()
results_large = agent.search("neural networks", max_results=50, smart_search=True)
time_large = time.time() - start
print(f"   Time: {time_large:.2f}s")
print(f"   Results: {len(results_large)}")

print("\n" + "=" * 80)
print("DIAGNOSIS:")
print("=" * 80)

if time_smart > time_basic * 1.5:
    print("❌ CRITICAL: Smart search is >50% slower due to 2x fetching")
if time_large > 10:
    print("❌ CRITICAL: Large requests take >10s (fetching 100 results)")
if len(results_smart) < 5:
    print("⚠️  WARNING: Filtering too aggressive, returning <5 results")

print("\nRecommended fixes:")
print("1. Reduce fetch_limit from 2x to 1.3x")
print("2. Add timeouts to all API calls")
print("3. Make Phase 2/3 features opt-in only")
print("=" * 80)
