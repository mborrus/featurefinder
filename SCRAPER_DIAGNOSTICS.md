# Scraper Diagnostics

## Current Status (from latest run)

| Source | Status | Issue | Screenings Found |
|--------|--------|-------|------------------|
| Metrograph | ✅ Working | Server-side rendered | 30 |
| Film Forum | ✅ Working | Server-side rendered | 18 |
| The New Yorker | ❌ Blocked | **403 Forbidden** - actively blocking scrapers | 0 |
| Screenslate | ❌ JS Required | Content loaded via JavaScript | 0 |
| IFC Center | ❌ JS Required | Content loaded via JavaScript | 0 |
| Time Out NYC | ❌ JS Required | **Next.js app** - JavaScript-rendered | 0 |
| Reddit | ⚠️ No credentials | Need API keys | 0 |

## Why Scrapers Fail

Web scrapers can fail for several reasons:

### 1. Website Structure Changed
Websites frequently redesign their HTML structure, changing class names and element hierarchies. Scrapers that worked yesterday may fail today.

### 2. JavaScript-Rendered Content (**CONFIRMED**)
Many modern websites use JavaScript frameworks (React, Vue, Next.js, Angular) that render content dynamically. BeautifulSoup (which we currently use) only sees the initial HTML, not JavaScript-rendered content.

**Sites confirmed using heavy JavaScript:**
- **Time Out NYC**: Next.js app - HTML body has ~19 tags total, all content loaded via JS
- **Screenslate**: Minimal HTML, content loaded dynamically
- **IFC Center**: No heading tags found, minimal content

### 3. Anti-Scraping Measures (**CONFIRMED**)
Some sites block automated requests with:
- User-agent filtering
- Rate limiting
- CAPTCHA
- Cloudflare protection

**Sites confirmed blocking scrapers:**
- **The New Yorker**: Returns 403 Forbidden even with full browser headers

### 4. No Content Available
Sometimes there genuinely are no special screenings that week.

## Diagnostic Steps

### Run the Diagnostic Script

```bash
python3 diagnose_scrapers.py
```

This will:
1. Fetch each problematic website
2. Show the HTML structure found
3. List all film-related class names
4. Display sample headings and content

### Interpreting Results

**If you see HTML but no relevant elements:**
- The CSS selectors in the scraper need updating
- Look at the "Sample classes" output
- Update the regex patterns in the scraper

**If you see very little content:**
- The site likely requires JavaScript rendering
- Consider using Selenium or Playwright
- Or use a scraping service like ScraperAPI

**If the fetch fails entirely:**
- The site might be blocking scrapers
- Try adding better headers in `base.py`
- May need to use proxies

## Solutions

### Option 1: Update Selectors (Quick Fix)
Update the regex patterns in each scraper to match the actual class names shown in the diagnostic output.

### Option 2: Use Selenium/Playwright (Better for JS sites)
For JavaScript-heavy sites, use a headless browser:
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://www.newyorker.com/goings-on-about-town/movies')
    content = page.content()
    # Parse with BeautifulSoup
```

### Option 3: Use APIs (Best)
Check if sites offer APIs:
- Some theaters have JSON APIs for their calendars
- Events sites may have developer APIs

### Option 4: Email Parsing (Alternative)
Since many theaters send newsletters, you could:
1. Subscribe to newsletters
2. Parse emails instead of scraping websites
3. More reliable and less likely to break

## Recommended Priority

1. **Fix The New Yorker** - Highest value source
2. **Fix IFC Center** - Good curation
3. **Fix Time Out** - Aggregator with good reach
4. **Fix Screenslate** - Comprehensive but may overlap

## Testing Individual Scrapers

```python
from scrapers.new_yorker import NewYorkerScraper

scraper = NewYorkerScraper()
results = scraper.scrape()
print(f"Found {len(results)} screenings")

if results:
    for s in results[:3]:
        print(f"- {s.title} at {s.theater}")
```
