#!/usr/bin/env python3
"""
Test script for Paris Theater scraper
"""
from scrapers.paris_theater import ParisTheaterScraper

def main():
    print("=" * 70)
    print("TESTING PARIS THEATER SCRAPER")
    print("=" * 70)

    scraper = ParisTheaterScraper()
    screenings = scraper.scrape()

    print("\n" + "=" * 70)
    print(f"RESULTS: Found {len(screenings)} screenings")
    print("=" * 70)

    if screenings:
        print("\nFirst 5 screenings:")
        for i, screening in enumerate(screenings[:5], 1):
            print(f"\n{i}. {screening.title}")
            print(f"   Date: {screening.date}")
            print(f"   Description: {screening.description[:100]}..." if screening.description else "   Description: N/A")
            print(f"   Special: {screening.special_note}")
            print(f"   URL: {screening.url}")
    else:
        print("\n⚠️  No screenings found")
        print("\nPossible issues:")
        print("- Website structure has changed")
        print("- JavaScript rendering not working")
        print("- Playwright not installed")
        print("- Network issues or website returning 503 errors")

if __name__ == "__main__":
    main()
