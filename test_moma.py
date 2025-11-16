"""
Test script for MoMA scraper
"""
from scrapers.moma import MoMAScraper

def test_moma_scraper():
    print("Testing MoMA scraper...")
    scraper = MoMAScraper()
    screenings = scraper.scrape()

    print(f"\nFound {len(screenings)} screenings from MoMA")

    if screenings:
        print("\nFirst few screenings:")
        for i, screening in enumerate(screenings[:5], 1):
            print(f"\n{i}. {screening.title}")
            print(f"   Date: {screening.date}")
            print(f"   Special Note: {screening.special_note}")
            print(f"   Director: {screening.director}")
            print(f"   Description: {screening.description[:100]}..." if len(screening.description) > 100 else f"   Description: {screening.description}")
            print(f"   URL: {screening.url}")
    else:
        print("No screenings found. This might be expected if:")
        print("  1. Playwright is not installed")
        print("  2. MoMA's website structure has changed")
        print("  3. There are currently no film events listed")

if __name__ == '__main__':
    test_moma_scraper()
