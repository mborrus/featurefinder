#!/usr/bin/env python3
"""
Debug script to see what SerpAPI returns for AMC theater search
"""
import os
import requests
import json

# Set API key
api_key = 'e70564af39d1d5496238f4177e2b22cef3d9cd7c5f8ec1d6e919223a56ac031b'

# Build SerpAPI request for AMC Lincoln Square
params = {
    'api_key': api_key,
    'engine': 'google',
    'q': 'AMC Lincoln Square 13 showtimes',
    'location': 'New York, NY',
    'hl': 'en',
    'gl': 'us'
}

print("Making SerpAPI request...")
print(f"Query: {params['q']}")
print(f"Location: {params['location']}")
print()

try:
    response = requests.get('https://serpapi.com/search', params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    print("=" * 80)
    print("FULL RESPONSE KEYS:")
    print("=" * 80)
    for key in data.keys():
        print(f"  - {key}")
    print()

    # Check for showtimes
    if 'showtimes' in data:
        print("=" * 80)
        print("SHOWTIMES DATA FOUND:")
        print("=" * 80)
        print(json.dumps(data['showtimes'], indent=2)[:2000])
        print("\n... (truncated if longer)")
    else:
        print("=" * 80)
        print("NO 'showtimes' KEY FOUND")
        print("=" * 80)
        print("\nAvailable keys:", list(data.keys()))

    # Check for other movie-related data
    if 'knowledge_graph' in data:
        print("\n" + "=" * 80)
        print("KNOWLEDGE GRAPH:")
        print("=" * 80)
        kg = data['knowledge_graph']
        print(f"Title: {kg.get('title', 'N/A')}")
        print(f"Type: {kg.get('type', 'N/A')}")
        print(f"Keys: {list(kg.keys())}")

    # Save full response for inspection
    with open('/tmp/serpapi_amc_response.json', 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\n✓ Full response saved to: /tmp/serpapi_amc_response.json")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
