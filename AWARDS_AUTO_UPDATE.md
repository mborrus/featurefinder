# Automated Awards Predictions Updates

This system automatically updates Oscar predictions and festival film lists on a weekly basis, ensuring the newsletter always features the latest critically acclaimed films.

## How It Works

### 1. **Data Sources**
The system fetches latest predictions from:
- **Variety Oscar Predictions** - Industry-leading awards coverage
- **Gold Derby** - Aggregated expert predictions
- **Festival Sites** - Official winners and selections (requires manual curation)

### 2. **Caching Strategy**
- Data is cached in `data/awards_cache.json`
- Cache refreshes automatically if older than 7 days
- Falls back to hardcoded data if web fetch fails
- **Weekly automatic updates** ensure fresh data

### 3. **Integration Points**
The live data is used by:
- `scrapers/base.py` - Festival and awards detection methods
- `aggregator.py` - Filtering logic (via BaseScraper)
- `config.py` - Dynamic data loading functions

## Usage

### Manual Update

Run the updater standalone to force refresh:

```bash
python awards_updater.py
```

This will:
1. Fetch latest predictions from Variety and Gold Derby
2. Merge with existing hardcoded data (preserves festival metadata)
3. Save to `data/awards_cache.json`
4. Print summary of updates

### Automatic Weekly Updates

The system automatically checks cache age during normal operation:

```python
# In your code - this happens automatically
from config import get_live_awards_data

# Loads from cache if fresh (< 7 days), otherwise fetches new data
festival_films, oscar_contenders = get_live_awards_data()
```

### Force Refresh

To force a refresh regardless of cache age:

```python
from config import get_live_awards_data

# Force refresh from web sources
festival_films, oscar_contenders = get_live_awards_data(use_cache=False)
```

### Integration with Main Workflow

The system is already integrated - no code changes needed!

When you run your main scraping script:
1. System checks if cache exists and is fresh
2. If cache is older than 7 days, automatically fetches new predictions
3. Uses fresh data for film detection and prioritization
4. Falls back to hardcoded data if fetch fails

## Cache File Format

The cache file (`data/awards_cache.json`) contains:

```json
{
  "last_updated": "2025-11-16T14:30:00",
  "sources": ["Variety", "Gold Derby"],
  "festival_films": {
    "hamnet": {
      "festivals": ["Telluride", "TIFF"],
      "awards": ["TIFF People's Choice Award"]
    },
    ...
  },
  "oscar_contenders": [
    "hamnet",
    "one battle after another",
    "sinners",
    ...
  ],
  "raw_predictions": {
    "variety": ["hamnet", "sinners", ...],
    "goldderby": ["hamnet", "marty supreme", ...]
  }
}
```

## Scheduling Weekly Updates

### Option 1: Cron Job (Linux/Mac)

Add to your crontab to run every Monday at 9 AM:

```bash
# Edit crontab
crontab -e

# Add this line
0 9 * * 1 cd /home/user/featurefinder && python awards_updater.py >> logs/awards_update.log 2>&1
```

### Option 2: GitHub Actions (if using GitHub)

Create `.github/workflows/update-awards.yml`:

```yaml
name: Update Awards Predictions

on:
  schedule:
    # Every Monday at 9 AM UTC
    - cron: '0 9 * * 1'
  workflow_dispatch:  # Allow manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install requests beautifulsoup4
      - name: Update awards cache
        run: python awards_updater.py
      - name: Commit updated cache
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add data/awards_cache.json
          git commit -m "chore: update awards predictions cache" || echo "No changes"
          git push
```

### Option 3: Integrated Update (Recommended)

The system **automatically updates weekly** during normal operation - no manual scheduling required!

Just run your regular email generation and the system handles the rest.

## Fallback Behavior

The system is designed to be resilient:

1. **Primary**: Use cached data if fresh (< 7 days old)
2. **Secondary**: Fetch from web if cache expired
3. **Fallback**: Use hardcoded data if fetch fails

**Your newsletter will always work**, even if:
- Network is down
- Variety/Gold Derby change their site structure
- Cache file is corrupted

## Monitoring

Check when data was last updated:

```bash
# View cache metadata
cat data/awards_cache.json | grep last_updated

# View full cache
cat data/awards_cache.json | jq '.'
```

## Maintenance

### Adding New Sources

Edit `awards_updater.py` and add methods:

```python
def fetch_new_source_predictions(self) -> List[str]:
    """Fetch from new prediction source"""
    # Your scraping logic here
    return predictions
```

Then update `update_cache()` to include the new source.

### Updating Hardcoded Data

Edit `config.py`:

- `FESTIVAL_FILMS_2024_2025` - Add new festival winners
- `OSCAR_CONTENDERS_2025` - Add new contenders
- `FESTIVAL_KEYWORDS` - Add new festival/award terms
- `AWARDS_KEYWORDS` - Add new awards-related keywords

The automated system will merge these with web-fetched data.

## Benefits

✅ **Always Fresh** - Weekly automatic updates from authoritative sources
✅ **Resilient** - Multiple fallback mechanisms ensure reliability
✅ **Transparent** - Cache file shows exactly what data is being used
✅ **Zero Effort** - No manual maintenance required
✅ **Auditable** - Track when and what was updated
✅ **Accurate** - Uses industry-standard prediction sources

## Example Workflow

```
Week 1 (Nov 11):
- User runs email generation
- No cache exists → Fetches from Variety/Gold Derby
- Saves to data/awards_cache.json
- Uses fresh data for newsletter

Week 2 (Nov 18):
- User runs email generation
- Cache is 7 days old → Fetches fresh predictions
- Updates cache with new data
- Newsletter uses latest predictions

Week 2 (Nov 19):
- User runs email generation again
- Cache is 1 day old → Uses cached data (fast!)
- No web fetch needed

Week 3 (Nov 25):
- User runs email generation
- Cache is 7 days old → Fetches fresh data
- Cycle continues...
```

## Troubleshooting

**Cache not updating:**
- Check `data/awards_cache.json` permissions
- Verify network connectivity
- Run `python awards_updater.py` manually to see errors

**Old data still showing:**
- Delete `data/awards_cache.json` to force refresh
- Check that `get_live_awards_data()` is being called

**Web fetch failing:**
- System will fall back to hardcoded data automatically
- Check if Variety/Gold Derby changed their site structure
- Update scraping selectors in `awards_updater.py`

## Future Enhancements

Potential improvements:
- Add more prediction sources (The Hollywood Reporter, IndieWire)
- Scrape festival official sites for winners
- Use APIs (TMDB, OMDB) for structured data
- Add sentiment analysis from reviews
- Track prediction changes over time
- Generate trend reports
