#!/usr/bin/env python3
"""
Test AMC scraper with corrected SerpAPI format
Uses the correct query format: theater name without "showtimes"
"""
import os
import sys

# Set API key for testing
os.environ['SERPAPI_KEY'] = 'e70564af39d1d5496238f4177e2b22cef3d9cd7c5f8ec1d6e919223a56ac031b'

from scrapers.amc import AMCScraper
import time

def test_amc_scraper():
    """Test AMC scraper with corrected format"""
    print("Testing AMC scraper with CORRECTED SerpAPI format")
    print("=" * 80)
    print("Query format: 'AMC Lincoln Square 13' (NO 'showtimes' keyword)")
    print("Location format: 'New York, New York, United States'")
    print("Endpoint: search.json")
    print("=" * 80)
    print()

    scraper = AMCScraper()

    # Test just one theater to minimize API usage
    original_theaters = scraper.theaters.copy()
    scraper.theaters = {
        'AMC Lincoln Square 13': original_theaters['AMC Lincoln Square 13']
    }

    try:
        start = time.time()
        results = scraper.scrape()
        elapsed = time.time() - start

        print(f"\n{'='*80}")
        print(f"RESULTS:")
        print(f"  Screenings found: {len(results)}")
        print(f"  Time elapsed: {elapsed:.2f}s")
        print(f"  API calls made: 1")
        print(f"{'='*80}\n")

        if results:
            print("SUCCESS! Found screenings:\n")
            for i, screening in enumerate(results[:10], 1):
                print(f"{i}. {screening.title}")
                print(f"   Theater: {screening.theater}")
                print(f"   Date: {screening.date}")
                print(f"   Times: {screening.time_slot[:50]}...")
                print(f"   Format: {screening.special_note}")
                print()

            if len(results) > 10:
                print(f"   ... and {len(results) - 10} more\n")

            return True
        else:
            print("No special/premium screenings found.")
            print("This could mean:")
            print("  - No IMAX/Dolby/special screenings currently showing")
            print("  - API returned different structure")
            print("  - Need to check /tmp/serpapi_*.json for response")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_amc_scraper()
    sys.exit(0 if success else 1)
