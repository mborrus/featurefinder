#!/usr/bin/env python3
"""
Try different query to get movie showtimes carousel
"""
import requests
import json

api_key = 'e70564af39d1d5496238f4177e2b22cef3d9cd7c5f8ec1d6e919223a56ac031b'

# Try searching for "movie showtimes" in New York
params = {
    'api_key': api_key,
    'engine': 'google',
    'q': 'movie showtimes',  # More general query
    'location': 'New York, NY',
    'hl': 'en',
    'gl': 'us'
}

print("Testing query: 'movie showtimes' in New York")
print("=" * 80)

try:
    response = requests.get('https://serpapi.com/search', params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    print("Response keys:", list(data.keys()))
    print()

    if 'showtimes' in data:
        print("✓ SHOWTIMES KEY FOUND!")
        print("=" * 80)
        showtimes = data['showtimes']
        print(f"Number of showtime days: {len(showtimes)}")

        if showtimes:
            print(f"\nFirst day:")
            first_day = showtimes[0]
            print(f"  Day: {first_day.get('day')}")
            print(f"  Date: {first_day.get('date')}")

            # Check structure
            if 'theaters' in first_day:
                print(f"  Structure: theaters -> movies")
                print(f"  Number of theaters: {len(first_day.get('theaters', []))}")
                if first_day['theaters']:
                    theater = first_day['theaters'][0]
                    print(f"\n  Sample theater: {theater.get('name', 'N/A')}")

            elif 'movies' in first_day:
                print(f"  Structure: movies -> theaters")
                print(f"  Number of movies: {len(first_day.get('movies', []))}")
                if first_day['movies']:
                    movie = first_day['movies'][0]
                    print(f"\n  Sample movie: {movie.get('name', 'N/A')}")

        print(f"\n✓ Saving full response to /tmp/serpapi_movies_response.json")
        with open('/tmp/serpapi_movies_response.json', 'w') as f:
            json.dump(data, f, indent=2)

    else:
        print("✗ NO SHOWTIMES KEY")
        print("Available keys:", list(data.keys()))

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
