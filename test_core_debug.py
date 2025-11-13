#!/usr/bin/env python3
"""
Debug test for CORE API - find out why it returns 0 results
"""

import requests
import json

API_KEY = 'kMnptdQvBGqrPOXJmUau0Hj51FC9T43w'
BASE_URL = "https://api.core.ac.uk/v3"

print("=" * 80)
print("CORE API DEBUG TEST")
print("=" * 80)

# Test 1: Try the current endpoint
print("\n[Test 1] Current endpoint: /search/works")
print("-" * 80)

headers = {'Authorization': f'Bearer {API_KEY}'}
params = {
    'q': 'machine learning neural networks',
    'limit': 10
}

try:
    response = requests.get(
        f"{BASE_URL}/search/works",
        params=params,
        headers=headers,
        timeout=15
    )

    print(f"Status code: {response.status_code}")
    print(f"URL: {response.url}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        print(f"Results count: {len(data.get('results', []))}")

        if data.get('results'):
            print(f"\nFirst result:")
            print(json.dumps(data['results'][0], indent=2)[:500])
        else:
            print(f"\n⚠️ No results found!")
            print(f"Full response: {json.dumps(data, indent=2)[:500]}")
    else:
        print(f"❌ Error response: {response.text[:500]}")

except Exception as e:
    print(f"❌ Exception: {e}")

# Test 2: Try alternative endpoint
print("\n\n[Test 2] Alternative endpoint: /works/search")
print("-" * 80)

try:
    response = requests.get(
        f"{BASE_URL}/works/search",
        params=params,
        headers=headers,
        timeout=15
    )

    print(f"Status code: {response.status_code}")
    print(f"URL: {response.url}")

    if response.status_code == 200:
        data = response.json()
        print(f"Response keys: {list(data.keys())}")
        print(f"Results count: {len(data.get('results', []))}")

        if data.get('results'):
            print(f"\nFirst result:")
            print(json.dumps(data['results'][0], indent=2)[:500])
    else:
        print(f"Error response: {response.text[:500]}")

except Exception as e:
    print(f"❌ Exception: {e}")

# Test 3: Check API status
print("\n\n[Test 3] API Status Check")
print("-" * 80)

try:
    response = requests.get(
        f"{BASE_URL}/",
        headers=headers,
        timeout=15
    )

    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text[:200]}")

except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "=" * 80)
print("DEBUG TEST COMPLETE")
print("=" * 80)
