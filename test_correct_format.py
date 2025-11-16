#!/usr/bin/env python3
"""
Test SerpAPI with correct URL format (no 'showtimes' in query)
"""
import requests
import json

api_key = 'e70564af39d1d5496238f4177e2b22cef3d9cd7c5f8ec1d6e919223a56ac031b'

# Use the exact format from the example
params = {
    'q': 'AMC Lincoln Square 13',  # NO "showtimes" added
    'location': 'New York, New York, United States',  # Full format
    'hl': 'en',
    'gl': 'us',
    'api_key': api_key
}

print("Testing with correct format:")
print(f"  Query: {params['q']}")
print(f"  Location: {params['location']}")
print("=" * 80)

try:
    # Note: using search.json endpoint
    response = requests.get('https://serpapi.com/search.json', params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    print("\nResponse keys:", list(data.keys()))

    if 'showtimes' in data:
        print("\n✓✓✓ SHOWTIMES KEY FOUND! ✓✓✓")
        showtimes = data['showtimes']
        print(f"Number of days: {len(showtimes)}")

        if showtimes:
            day = showtimes[0]
            print(f"\nFirst day: {day.get('day')} {day.get('date')}")

            # Check structure
            if 'movies' in day:
                movies = day['movies']
                print(f"Number of movies: {len(movies)}")

                # Show first few movies
                for i, movie in enumerate(movies[:3], 1):
                    print(f"\n  {i}. {movie.get('name')}")
                    showings = movie.get('showing', [])
                    for showing in showings:
                        types = showing.get('type', [])
                        times = showing.get('time', [])
                        print(f"     {types}: {times[:3]}")

        with open('/tmp/serpapi_correct_format.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n✓ Saved to /tmp/serpapi_correct_format.json")

    else:
        print("\n✗ NO SHOWTIMES KEY")
        print("Available keys:", list(data.keys()))

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
