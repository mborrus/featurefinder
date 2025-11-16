#!/usr/bin/env python3
"""
Test script for Alamo Drafthouse scraper
"""
from scrapers.alamo_drafthouse import AlamoDrafthouseScraper


def test_alamo_drafthouse():
    print("Testing Alamo Drafthouse Lower Manhattan scraper...")
    print("=" * 60)

    scraper = AlamoDrafthouseScraper()
    screenings = scraper.scrape()

    print(f"\n{'=' * 60}")
    print(f"Total screenings found: {len(screenings)}")
    print(f"{'=' * 60}\n")

    if screenings:
        print("Sample screenings:")
        for i, screening in enumerate(screenings[:5], 1):
            print(f"\n{i}. {screening.title}")
            print(f"   Theater: {screening.theater}")
            if screening.date:
                print(f"   Date: {screening.date}")
            if screening.time_slot:
                print(f"   Time: {screening.time_slot}")
            if screening.special_note:
                print(f"   Special: {screening.special_note}")
            if screening.description:
                print(f"   Description: {screening.description[:100]}...")
            if screening.url:
                print(f"   URL: {screening.url}")
            print(f"   Priority: {screening.priority}")
    else:
        print("No screenings found. This could mean:")
        print("1. The website structure has changed")
        print("2. There are no special events currently listed")
        print("3. The page failed to load properly")
        print("\nPlease check the website manually: https://drafthouse.com/nyc")


if __name__ == '__main__':
    test_alamo_drafthouse()
