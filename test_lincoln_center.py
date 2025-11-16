#!/usr/bin/env python3
"""
Test script for Lincoln Center scraper
"""
from scrapers.film_at_lincoln_center import FilmAtLincolnCenterScraper

def main():
    print("=" * 70)
    print("TESTING LINCOLN CENTER SCRAPER")
    print("=" * 70)

    scraper = FilmAtLincolnCenterScraper()
    screenings = scraper.scrape()

    print("\n" + "=" * 70)
    print(f"RESULTS: Found {len(screenings)} screenings")
    print("=" * 70)

    if screenings:
        print("\nFirst 5 screenings:")
        for i, screening in enumerate(screenings[:5], 1):
            print(f"\n{i}. {screening.title}")
            print(f"   Date: {screening.date}")
            print(f"   Description: {screening.description[:100]}...")
            print(f"   Special: {screening.special_note}")
            print(f"   URL: {screening.url}")
    else:
        print("\n⚠️  No screenings found")
        print("\nPossible issues:")
        print("- Website structure has changed")
        print("- JavaScript rendering not working")
        print("- Playwright not installed")
        print("- Network issues")

if __name__ == "__main__":
    main()
