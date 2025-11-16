#!/usr/bin/env python3
"""
Debug script to examine AMC website structure and API calls
"""
from playwright.sync_api import sync_playwright
import json

def intercept_api_calls():
    """Capture API calls made by the AMC website"""
    api_calls = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )

        # Intercept network requests
        def handle_request(request):
            url = request.url
            if 'graph.amctheatres.com' in url or 'api' in url or 'graphql' in url:
                api_calls.append({
                    'url': url,
                    'method': request.method,
                    'headers': dict(request.headers),
                    'post_data': request.post_data if request.method == 'POST' else None
                })
                print(f"\n🔍 API Call detected:")
                print(f"   URL: {url}")
                print(f"   Method: {request.method}")
                if request.post_data:
                    print(f"   Data: {request.post_data[:500]}")

        page.on('request', handle_request)

        # Navigate to AMC showtimes page
        url = 'https://www.amctheatres.com/movie-theatres/new-york-city/amc-lincoln-square-13/showtimes'
        print(f"Loading: {url}")
        page.goto(url, wait_until='domcontentloaded', timeout=60000)

        # Wait for page to fully load
        print("Waiting for content to load...")
        page.wait_for_timeout(5000)

        # Try to find common React/Next.js data structures
        print("\n📝 Checking for Next.js data...")
        next_data = page.evaluate('() => window.__NEXT_DATA__')
        if next_data:
            print("Found __NEXT_DATA__:")
            print(json.dumps(next_data, indent=2)[:1000])

        # Get page content and look for useful classes/IDs
        content = page.content()
        print(f"\n📄 Page content length: {len(content)} chars")

        # Look for movie/showtime related elements
        print("\n🎬 Looking for movie elements...")

        # Try various selectors
        selectors_to_try = [
            'article', 'div[class*="movie"]', 'div[class*="Movie"]',
            'div[class*="showtime"]', 'div[class*="Showtime"]',
            '[data-testid*="movie"]', '[data-testid*="showtime"]',
            'button[class*="showtime"]', 'a[href*="/movies/"]'
        ]

        for selector in selectors_to_try:
            try:
                elements = page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    print(f"   ✓ Found {len(elements)} elements with selector: {selector}")
                    # Get first element's HTML
                    if elements:
                        html = elements[0].evaluate('el => el.outerHTML')
                        print(f"      Sample: {html[:200]}")
            except:
                pass

        browser.close()

    return api_calls

if __name__ == '__main__':
    print("Starting AMC website analysis...\n")
    api_calls = intercept_api_calls()

    if api_calls:
        print(f"\n\n📡 Summary: Captured {len(api_calls)} API calls")
        for call in api_calls:
            print(f"\n{call['method']} {call['url']}")
            if call['post_data']:
                print(f"Data: {call['post_data'][:300]}")
    else:
        print("\n❌ No API calls captured")
