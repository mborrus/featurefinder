# AMC Scraper Status

## Current Status: DISABLED ⚠️

The AMC scraper has been temporarily disabled due to fundamental compatibility issues with AMC's website architecture.

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

The scraper has been disabled to prevent timeouts and provide a better user experience. The code now:
- Returns immediately (< 0.1 seconds)
- Prints clear warning message explaining the situation
- Includes commented code for future reference

## Future Solutions

### Option 1: Use AMC's GraphQL API (Recommended)
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

## Testing the Fix

The current disabled version can be tested:
```bash
python -c "
from scrapers.amc import AMCScraper
import time

start = time.time()
scraper = AMCScraper()
results = scraper.scrape()
elapsed = time.time() - start

print(f'Screenings: {len(results)}')
print(f'Time: {elapsed:.2f}s')
print(f'Status: {"PASS" if elapsed < 1 else "FAIL"}')
"
```

Expected output:
- 0 screenings found (scraper is disabled)
- Time < 0.1 seconds (instant return)
- Warning message printed

## Related Files
- `/home/user/featurefinder/scrapers/amc.py` - Main scraper (disabled)
- `/home/user/featurefinder/scrapers/base.py` - Base scraper class with Playwright support
- `/home/user/featurefinder/debug_amc.py` - Debug script to analyze AMC website structure

## Contact
If you need AMC theater data urgently, consider:
1. Manually checking AMC website for special screenings
2. Using other theater scrapers (Lincoln Center, IFC Center, etc.)
3. Implementing one of the solutions above
