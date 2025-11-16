#!/usr/bin/env python3
"""
Quick test of AMC scraper
"""
from scrapers.amc import AMCScraper

def main():
    print("Testing AMC Scraper...")
    print("=" * 60)

    scraper = AMCScraper()
    screenings = scraper.scrape()

    print(f"\nTotal screenings found: {len(screenings)}")
    print("=" * 60)

    if screenings:
        print("\nSample screenings:")
        for i, screening in enumerate(screenings[:5], 1):
            print(f"\n{i}. {screening.title}")
            print(f"   Theater: {screening.theater}")
            print(f"   Date: {screening.date}")
            print(f"   Time: {screening.time_slot}")
            print(f"   Special: {screening.special_note}")
            print(f"   Priority: {screening.priority}")
            if screening.url:
                print(f"   URL: {screening.url}")
    else:
        print("\n⚠️  No screenings found. This could mean:")
        print("  - No special screenings available in the next month")
        print("  - AMC website structure has changed")
        print("  - Network/Playwright issues")

if __name__ == "__main__":
    main()
