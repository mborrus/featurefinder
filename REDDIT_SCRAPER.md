# Reddit Scraper Documentation

## Overview
The Reddit scraper collects screening information from r/NYCmovies using web scraping techniques with the `.json` endpoint.

## How It Works

### Data Sources
The scraper fetches data from three sources:

1. **Hot Posts** (`/r/NYCmovies/hot.json`)
   - Includes pinned weekly summary posts
   - Pinned posts are identified by the `stickied` or `pinned` flag in the JSON response
   - These posts often contain comprehensive weekly screening roundups

2. **Screening Info Flair** (`/search?q=flair:"Screening Info"`)
   - Posts tagged with the "Screening Info" flair
   - These are specifically marked screening announcements
   - Higher signal-to-noise ratio for relevant content

3. **New Posts** (`/r/NYCmovies/new.json`)
   - Recent posts from the last 7 days
   - Filtered by keywords that indicate special screenings

### Technical Implementation

#### Playwright for Browser Emulation
The scraper uses Playwright to bypass Reddit's anti-scraping measures:
- Emulates a real Chrome browser
- Handles JavaScript-rendered content
- Avoids 403 Forbidden errors from direct HTTP requests

#### JSON Parsing
- Accesses Reddit's native JSON endpoints by appending `.json` to URLs
- Parses JSON responses directly (when served in `<pre>` tags in browser)
- More reliable than HTML parsing

#### Deduplication
- Tracks screening URLs to avoid duplicates across different sources
- Ensures each screening appears only once in the final results

### Data Extraction

The scraper extracts:
- **Title**: Cleaned of Reddit formatting like `[brackets]` and theater names in parentheses
- **Theater**: Matches against a list of known NYC theaters
- **Date**: Extracts dates in various formats (MM/DD, day names, month day)
- **Special Notes**: Identifies Q&A, director appearances, IMAX, 70mm, premieres, etc.
- **Priority**: Higher priority (2) for pinned posts, normal (3) for others
- **URL**: Direct link to the Reddit post

### Priority Assignment
- **Priority 2**: Pinned weekly summary posts
- **Priority 3**: Regular screening posts

### Known Theaters
The scraper recognizes these NYC theaters:
- AMC Lincoln Square
- AMC 84th
- Paris Theater
- Angelika
- Film Forum
- IFC Center
- Metrograph
- Alamo Drafthouse
- Anthology
- BAM
- Quad
- Nitehawk

## Configuration

No API keys required - uses web scraping instead of Reddit API.

## Error Handling

- Retries with exponential backoff
- Gracefully handles rate limiting (429 errors)
- Falls back to returning empty results if all attempts fail
- Continues scraping other sources even if one fails

## Rate Limiting

- 1-second delays between different data sources
- Playwright browser instances are properly closed to avoid resource leaks
- Respects Reddit's rate limiting by catching 429 errors

## Testing

To test the Reddit scraper:

```bash
python3 -c "
from scrapers.reddit import RedditScraper
scraper = RedditScraper()
screenings = scraper.scrape()
print(f'Found {len(screenings)} screenings')
for s in screenings[:5]:
    print(f'{s.title} - {s.theater} - {s.date}')
"
```

## Dependencies

- `playwright`: For browser automation
- `requests`: Fallback HTTP client
- `beautifulsoup4`: Used by base scraper (not directly by Reddit scraper)

Ensure Playwright browsers are installed:
```bash
python3 -m playwright install chromium
```
