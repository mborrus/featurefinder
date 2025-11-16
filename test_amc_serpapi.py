#!/usr/bin/env python3
"""
Test AMC scraper with SerpAPI - MINIMAL API USAGE
Only tests one theater to preserve API quota
"""
import os
import sys

# Set API key for testing
os.environ['SERPAPI_KEY'] = 'e70564af39d1d5496238f4177e2b22cef3d9cd7c5f8ec1d6e919223a56ac031b'

from scrapers.amc import AMCScraper

def test_single_theater():
    """Test with just one theater to minimize API usage"""
    print("Testing AMC scraper with SerpAPI (1 API call only)...")
    print("=" * 60)

    scraper = AMCScraper()

    # Temporarily modify to test only one theater
    original_theaters = scraper.theaters.copy()
    scraper.theaters = {
        'AMC Lincoln Square 13': original_theaters['AMC Lincoln Square 13']
    }

    try:
        results = scraper.scrape()

        print(f"\n{'='*60}")
        print(f"RESULTS: Found {len(results)} screenings")
        print(f"{'='*60}\n")

        if results:
            # Show first few screenings
            for i, screening in enumerate(results[:5], 1):
                print(f"{i}. {screening.title}")
                print(f"   Theater: {screening.theater}")
                print(f"   Date: {screening.date}")
                print(f"   Times: {screening.time_slot}")
                print(f"   Special: {screening.special_note}")
                print(f"   Priority: {screening.priority}")
                print()

            if len(results) > 5:
                print(f"   ... and {len(results) - 5} more screenings\n")
        else:
            print("No special/premium format screenings found.")
            print("This might mean:")
            print("- No IMAX/Dolby/special screenings currently showing")
            print("- SerpAPI returned different data structure")
            print("- API key or query issue")

        return len(results) > 0

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_single_theater()
    sys.exit(0 if success else 1)
