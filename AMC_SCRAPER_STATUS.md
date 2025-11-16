# AMC Scraper Status

## Current Status: SERPAPI INTEGRATION (LIMITED) ⚠️

The AMC scraper now uses SerpAPI instead of direct web scraping, but has limitations due to how SerpAPI's Google Showtimes API works.

## Problem

### Original Issue
- **Symptom**: Scraper was timing out after 19+ minutes with repeated selector warnings
- **Root Cause**: AMC Theatres website uses React/Next.js with client-side rendering
- **Impact**: CSS selectors (`.ShowtimesByTheatre`, `.Showtime`, etc.) don't exist in the static HTML

### Technical Details
```
Previous behavior:
- Checking ~10 dates per theater (every 3 days for 30 days)
- 2 theaters × 10 dates = 20 page loads
- Each page timing out after 40 seconds waiting for non-existent selectors
- Total time: 20 × 40s = 13+ minutes minimum
- Result: 0 screenings found
```

## Solution Implemented

The scraper now uses SerpAPI's Google Showtimes API:
- **API Used**: SerpAPI (https://serpapi.com/showtimes-results)
- **Authentication**: Requires SERPAPI_KEY environment variable
- **Rate Limits**: Free tier provides 250 searches/month
- **Current Limitation**: Theater-specific searches return knowledge graph data instead of showtimes carousel

### How It Works
1. Makes API calls to SerpAPI for each theater
2. Uses correct format: `?q=AMC+Lincoln+Square+13&location=New+York,+New+York,+United+States`
3. Parses JSON response for showtimes data
4. Extracts IMAX, Dolby Cinema, and other premium format screenings

### API Request Format
```
https://serpapi.com/search.json?q=AMC+Lincoln+Square+13&location=New+York,+New+York,+United+States&hl=en&gl=us&api_key=YOUR_KEY
```

**Important**:
- Query is theater name WITHOUT "showtimes" keyword
- Location uses full format: "City, State, Country"
- Uses `.json` endpoint explicitly

## Recommended Next Steps

### Option A: Reverse the Search Strategy (SerpAPI)
Instead of searching for theaters, search for popular movies:
- **Query**: "Wicked showtimes New York" → Get list of all theaters showing it
- **Filter**: Extract only AMC Lincoln Square and AMC 84th Street from results
- **Advantages**:
  - Works with current SerpAPI integration
  - Gets actual showtimes data
  - Can identify IMAX/Dolby formats
- **Challenges**:
  - Need to know what movies are currently playing
  - May miss less popular films
  - Requires multiple API calls if checking many movies
  - Uses API quota faster

### Option B: Parse AMC Direct from Organic Results
Use SerpAPI to get AMC's showtimes page URL, then scrape it:
- Theater search returns link to AMC's showtimes page in organic results
- Could then use Playwright to load and parse that page
- Combines API reliability with direct data access

## Alternative Solutions

### Option 1: Use AMC's GraphQL API
AMC exposes a GraphQL API that powers their website:
- **Endpoint**: `https://graph.amctheatres.com`
- **Advantages**:
  - Reliable, structured data
  - No parsing required
  - Faster than web scraping
  - More resilient to website changes
- **Challenges**:
  - Need to reverse-engineer GraphQL queries
  - May require authentication
  - Rate limiting considerations

### Option 2: Use AMC's REST API
AMC has a developer portal with REST API endpoints:
- **URL**: `https://developers.amctheatres.com/`
- **Endpoints**: `/Showtimes`, `/Theatres`, `/Movies`
- **Advantages**:
  - Official, documented API
  - Structured data format
  - Designed for third-party use
- **Challenges**:
  - Requires API key registration
  - May have usage limits or costs
  - Developer portal currently blocks automated requests (403)

### Option 3: Enhanced Playwright Scraping
Improve the web scraping approach:
- **Method**: Intercept network requests to capture GraphQL calls
- **Advantages**:
  - No API registration needed
  - Can extract exact queries the website uses
- **Challenges**:
  - Requires Playwright to run in non-sandboxed environment
  - More brittle than API approach
  - Higher resource usage
  - Still subject to website changes

### Option 4: Use Third-Party Services
Leverage existing movie APIs:
- **Options**:
  - ShowtimeAPI.com (commercial service)
  - MovieGlu API
  - TMS (Tribune Media Services)
- **Advantages**:
  - Aggregates multiple theater chains
  - Professional data quality
  - Maintained by third parties
- **Challenges**:
  - Usually requires payment
  - May not have all special screenings data
  - Adds external dependency

## Recommendation

For a production solution, **Option 1 (GraphQL API)** is recommended because:
1. It's what the website actually uses
2. No API keys or registration needed
3. Provides structured, reliable data
4. Can be implemented with standard HTTP requests

### Implementation Steps for GraphQL Approach:
1. Use Playwright to load AMC showtimes page
2. Intercept network requests to capture GraphQL queries
3. Extract the query structure and variables
4. Implement direct GraphQL API calls using `requests` library
5. Parse JSON responses instead of HTML

## Testing the Current Implementation

The SerpAPI version can be tested:
```bash
export SERPAPI_KEY="your-api-key-here"

python -c "
from scrapers.amc import AMCScraper
import time

start = time.time()
scraper = AMCScraper()
results = scraper.scrape()
elapsed = time.time() - start

print(f'Screenings: {len(results)}')
print(f'Time: {elapsed:.2f}s')
print(f'API calls made: 2 (one per theater)')
"
```

Expected output with current implementation:
- 0 screenings found (theater searches don't return showtimes carousel)
- Time: ~2-4 seconds (API calls are fast)
- Note: Uses 2 API calls from your monthly quota

To test if SerpAPI is working at all, try:
```bash
python test_amc_serpapi.py
```

See debug scripts:
- `debug_serpapi_response.py` - Shows raw API response for theater search
- `debug_serpapi_movies.py` - Tests movie-specific search

## Related Files
- `/home/user/featurefinder/scrapers/amc.py` - Main scraper (disabled)
- `/home/user/featurefinder/scrapers/base.py` - Base scraper class with Playwright support
- `/home/user/featurefinder/debug_amc.py` - Debug script to analyze AMC website structure

## Contact
If you need AMC theater data urgently, consider:
1. Manually checking AMC website for special screenings
2. Using other theater scrapers (Lincoln Center, IFC Center, etc.)
3. Implementing one of the solutions above
