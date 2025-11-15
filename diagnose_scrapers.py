#!/usr/bin/env python3
"""
Diagnostic script to check what's being found on each website
Run this in your production environment where dependencies are installed
"""
import sys
from scrapers.base import BaseScraper
import re

class DiagnosticScraper(BaseScraper):
    """Diagnostic scraper to inspect page structure"""

    def __init__(self, name, url):
        super().__init__(name)
        self.test_url = url

    def diagnose(self):
        """Fetch and diagnose page structure"""
        print(f"\n{'=' * 70}")
        print(f"DIAGNOSING: {self.name}")
        print(f"URL: {self.test_url}")
        print('=' * 70)

        soup = self.fetch_page(self.test_url)

        if not soup:
            print("❌ FAILED to fetch page")
            return

        print("✓ Page fetched successfully\n")

        # Basic page info
        print(f"Page Title: {soup.title.string if soup.title else 'No title'}\n")

        # Check for common elements
        print("HTML Structure Analysis:")
        print("-" * 70)

        articles = soup.find_all('article', limit=5)
        print(f"  <article> tags: {len(articles)} found")
        if articles:
            print(f"    Sample classes: {articles[0].get('class', 'none')}")

        divs_with_class = [d for d in soup.find_all('div', limit=100) if d.get('class')][:10]
        print(f"  <div> tags with classes: {len(divs_with_class)} found (showing first 10)")
        if divs_with_class:
            for i, div in enumerate(divs_with_class[:3]):
                print(f"    Sample {i+1}: {' '.join(div.get('class', []))}")

        # Look for film-related keywords in class names
        print("\nSearching for film-related elements:")
        print("-" * 70)

        keywords = ['film', 'movie', 'screening', 'event', 'card', 'listing', 'item', 'entry']
        for keyword in keywords:
            elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(keyword, re.I), limit=5)
            if elements:
                print(f"  '{keyword}': {len(elements)} elements found")
                if elements:
                    classes = elements[0].get('class', [])
                    print(f"    Sample classes: {' '.join(classes) if classes else 'none'}")

        # Look for title-like elements
        print("\nSearching for title elements:")
        print("-" * 70)
        h_tags = soup.find_all(['h1', 'h2', 'h3', 'h4'], limit=10)
        print(f"  Found {len(h_tags)} heading tags")
        for i, h in enumerate(h_tags[:3]):
            text = h.get_text(strip=True)[:60]
            classes = ' '.join(h.get('class', []))
            print(f"    {i+1}. <{h.name}> {classes[:40]}: \"{text}\"")

        # Sample text content
        print("\nSample page content (first 500 chars):")
        print("-" * 70)
        text = soup.get_text()[:500].replace('\n', ' ').replace('\r', '')
        print(f"  {text}...")

        print()

def main():
    """Run diagnostics on all problematic scrapers"""

    tests = [
        ("The New Yorker", "https://www.newyorker.com/goings-on-about-town/movies"),
        ("Screenslate", "https://www.screenslate.com/listings"),
        ("IFC Center", "https://www.ifccenter.com/films"),
        ("Time Out NYC", "https://www.timeout.com/newyork/film"),
    ]

    for name, url in tests:
        scraper = DiagnosticScraper(name, url)
        try:
            scraper.diagnose()
        except Exception as e:
            print(f"❌ ERROR during diagnosis: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review the HTML structure for each site")
    print("2. Update the scraper selectors to match actual class names")
    print("3. Consider if sites require JavaScript rendering (use Selenium/Playwright)")
    print()

if __name__ == "__main__":
    main()
