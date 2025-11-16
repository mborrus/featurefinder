# Playwright Setup for JavaScript-Rendered Sites

## What is Playwright?

Playwright is a browser automation library that can render JavaScript-heavy websites. Unlike BeautifulSoup (which only sees static HTML), Playwright launches a real browser, executes JavaScript, and then extracts the fully rendered content.

## Installation

```bash
# Install Playwright
pip install playwright

# Install browser binaries (required - only needs to be done once)
playwright install chromium
```

## Why It's Needed

Modern websites use JavaScript frameworks (React, Vue, Next.js) that load content dynamically:
- **Time Out NYC**: Next.js app - all articles loaded via JavaScript
- **Screenslate**: Dynamic content loading
- **IFC Center**: Film listings rendered client-side

These sites return minimal HTML initially. The actual content appears only after JavaScript executes.

## How It Works

The `fetch_page_js()` method in `scrapers/base.py`:

1. Launches a headless Chromium browser
2. Navigates to the URL
3. Waits for the page to load (`domcontentloaded`)
4. Optionally waits for specific elements (via CSS selector)
5. Waits 2 extra seconds for JavaScript to finish
6. Extracts the fully rendered HTML
7. Closes the browser
8. Returns BeautifulSoup object with rendered content

## Usage in Scrapers

### Time Out NYC
```python
# Wait for article tiles to load
soup = self.fetch_page_js(url, wait_selector='article')
```

### Screenslate
```python
# Wait for screening list to appear
soup = self.fetch_page_js(url, wait_selector='.view-screenings')
```

### IFC Center
```python
# Wait for film cards/rows
soup = self.fetch_page_js(url, wait_selector='.film-row, .movie-card')
```

## Fallback Strategy

All scrapers now use a fallback approach:
1. Try Playwright first (for JavaScript content)
2. If Playwright fails, fall back to regular `fetch_page()`
3. This ensures scrapers don't completely fail if Playwright has issues

## Performance Considerations

**Playwright is slower than BeautifulSoup:**
- Regular fetch: ~1-2 seconds
- Playwright fetch: ~5-10 seconds (needs to launch browser, render JS)

**When to use:**
- ✅ Use for sites that REQUIRE JavaScript (Time Out, Screenslate, IFC)
- ❌ Don't use for server-rendered sites (Metrograph, Film Forum work fine without it)

## Troubleshooting

### "Playwright not installed" error
```bash
pip install playwright
playwright install chromium
```

### "Browser not found" error
```bash
playwright install chromium
```

### Network/proxy issues
Some restricted environments may block Playwright's network access. In production environments with normal internet access, this should work fine.

### Timeout errors
Increase timeout if site is slow:
```python
soup = self.fetch_page_js(url, wait_selector='article', timeout=60000)  # 60 seconds
```

## Current Status

| Scraper | Uses Playwright | Fallback |
|---------|----------------|----------|
| Metrograph | ❌ No (not needed) | N/A |
| Film Forum | ❌ No (not needed) | N/A |
| Time Out NYC | ✅ Yes | ✅ Yes |
| Screenslate | ✅ Yes | ✅ Yes |
| IFC Center | ✅ Yes | ✅ Yes |
| The New Yorker | ❌ No (403 blocked) | N/A |

## Alternative Approaches

If Playwright doesn't work:
1. **Find JSON APIs**: Some sites have hidden JSON endpoints
2. **Email parsing**: Parse theater newsletter emails instead
3. **RSS feeds**: Some theaters have RSS feeds
4. **Official APIs**: Check if theaters offer developer APIs
