"""
Automated updater for festival films and Oscar contenders
Fetches latest predictions from Variety, Gold Derby, and other sources
Caches results in JSON file for weekly updates
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Set
import requests
from bs4 import BeautifulSoup


class AwardsUpdater:
    """Fetches and caches latest Oscar predictions and festival films"""

    def __init__(self, cache_file: str = 'data/awards_cache.json'):
        self.cache_file = cache_file
        self.cache_max_age_days = 7  # Refresh weekly

        # Ensure data directory exists
        os.makedirs(os.path.dirname(cache_file) if os.path.dirname(cache_file) else '.', exist_ok=True)

    def should_update(self) -> bool:
        """Check if cache needs updating (older than 7 days or doesn't exist)"""
        if not os.path.exists(self.cache_file):
            return True

        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)

            last_update = datetime.fromisoformat(cache_data.get('last_updated', '2000-01-01'))
            age = datetime.now() - last_update

            return age.days >= self.cache_max_age_days
        except Exception:
            return True

    def fetch_variety_predictions(self) -> List[str]:
        """
        Fetch Oscar predictions from Variety
        Returns list of film titles predicted for Best Picture
        """
        predictions = []

        try:
            # Variety's Oscar predictions page
            url = 'https://variety.com/lists/2026-oscars-predictions/'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"  Warning: Variety fetch returned status {response.status_code}")
                return predictions

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for film titles in various structures Variety might use
            # This is a best-effort extraction and may need adjustment

            # Method 1: Look for article titles or h2/h3 headers
            for header in soup.find_all(['h2', 'h3', 'h4']):
                text = header.get_text().strip()
                # Filter out obvious non-film titles
                if text and len(text) < 100 and not any(skip in text.lower() for skip in
                    ['category', 'prediction', 'winner', 'by:', 'updated', 'posted', 'share']):
                    # Clean up the title
                    title = text.strip('"').strip("'").strip()
                    if title and len(title) > 2:
                        predictions.append(title.lower())

            # Method 2: Look for specific list items or entries
            for item in soup.find_all('li'):
                text = item.get_text().strip()
                if text and 10 < len(text) < 100:
                    # Try to extract film title
                    title = text.split('(')[0].strip()  # Remove year/director info
                    if title and len(title) > 2:
                        predictions.append(title.lower())

            # Remove duplicates while preserving order
            seen = set()
            predictions = [x for x in predictions if not (x in seen or seen.add(x))]

            print(f"  Fetched {len(predictions)} predictions from Variety")

        except Exception as e:
            print(f"  Error fetching Variety predictions: {e}")

        return predictions[:30]  # Limit to top 30 to avoid noise

    def fetch_goldderby_predictions(self) -> List[str]:
        """
        Fetch Oscar predictions from Gold Derby
        Returns list of film titles predicted for Best Picture
        """
        predictions = []

        try:
            url = 'https://www.goldderby.com/odds/combined-odds/oscars-best-picture-2026/'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"  Warning: Gold Derby fetch returned status {response.status_code}")
                return predictions

            soup = BeautifulSoup(response.content, 'html.parser')

            # Gold Derby usually has odds tables or lists
            # Look for film titles in table rows or list items
            for row in soup.find_all(['tr', 'li']):
                text = row.get_text().strip()
                if text and 5 < len(text) < 100:
                    # Clean title
                    title = text.split('(')[0].strip()
                    title = title.split('-')[0].strip()  # Remove odds
                    if title and len(title) > 2:
                        predictions.append(title.lower())

            # Remove duplicates
            seen = set()
            predictions = [x for x in predictions if not (x in seen or seen.add(x))]

            print(f"  Fetched {len(predictions)} predictions from Gold Derby")

        except Exception as e:
            print(f"  Error fetching Gold Derby predictions: {e}")

        return predictions[:25]

    def fetch_festival_winners(self) -> Dict[str, Dict]:
        """
        Fetch recent festival winners and selections
        Returns dict mapping film titles to festival/awards info
        """
        festival_films = {}

        # For now, this would require more sophisticated scraping
        # We could fetch from:
        # - Cannes official site
        # - Venice official site
        # - TIFF official site
        # - IndieWire festival coverage
        # - Variety festival coverage

        # This is a placeholder - in practice, festival sites are complex
        # and may require more sophisticated parsing or even manual curation

        print("  Note: Festival winner fetching requires manual curation - using static data")

        return festival_films

    def merge_with_existing(self, new_predictions: List[str], existing_films: Dict) -> Dict:
        """
        Merge new predictions with existing hardcoded data
        Preserves festival/awards metadata from existing entries
        """
        merged = {}

        # Start with existing data
        for title, info in existing_films.items():
            merged[title.lower()] = info

        # Add new predictions (without detailed festival info unless we scraped it)
        for title in new_predictions:
            title_lower = title.lower().strip()
            if title_lower not in merged:
                merged[title_lower] = {'festivals': [], 'awards': []}

        return merged

    def update_cache(self) -> bool:
        """
        Update the awards cache with latest data
        Returns True if successful, False otherwise
        """
        print("Updating awards predictions cache...")

        try:
            # Fetch from multiple sources
            variety_predictions = self.fetch_variety_predictions()
            goldderby_predictions = self.fetch_goldderby_predictions()

            # Combine predictions (union of both sources)
            all_predictions = list(set(variety_predictions + goldderby_predictions))

            # Load existing hardcoded data to preserve festival info
            from config import FESTIVAL_FILMS_2024_2025, OSCAR_CONTENDERS_2025

            # Merge new predictions with existing data
            merged_films = self.merge_with_existing(all_predictions, FESTIVAL_FILMS_2024_2025)
            merged_contenders = list(set(OSCAR_CONTENDERS_2025 + all_predictions))

            # Create cache data
            cache_data = {
                'last_updated': datetime.now().isoformat(),
                'sources': ['Variety', 'Gold Derby'],
                'festival_films': merged_films,
                'oscar_contenders': merged_contenders,
                'raw_predictions': {
                    'variety': variety_predictions,
                    'goldderby': goldderby_predictions
                }
            }

            # Write to cache file
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)

            print(f"✓ Cache updated successfully")
            print(f"  Festival films: {len(merged_films)}")
            print(f"  Oscar contenders: {len(merged_contenders)}")
            print(f"  Cache file: {self.cache_file}")

            return True

        except Exception as e:
            print(f"✗ Error updating cache: {e}")
            return False

    def load_cache(self) -> Dict:
        """
        Load awards data from cache
        Returns cached data or empty dict if unavailable
        """
        if not os.path.exists(self.cache_file):
            return {}

        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache: {e}")
            return {}

    def get_awards_data(self, force_update: bool = False) -> Dict:
        """
        Get awards data, updating cache if needed

        Args:
            force_update: Force cache update even if not expired

        Returns:
            Dictionary with festival_films and oscar_contenders
        """
        # Check if update needed
        if force_update or self.should_update():
            print("Cache expired or missing, fetching latest data...")
            self.update_cache()
        else:
            cache_data = self.load_cache()
            last_update = cache_data.get('last_updated', 'unknown')
            print(f"Using cached data (last updated: {last_update})")

        # Load and return cache
        cache_data = self.load_cache()

        if not cache_data:
            # Fall back to hardcoded data
            print("Warning: No cache available, using hardcoded data")
            from config import FESTIVAL_FILMS_2024_2025, OSCAR_CONTENDERS_2025
            return {
                'festival_films': FESTIVAL_FILMS_2024_2025,
                'oscar_contenders': OSCAR_CONTENDERS_2025
            }

        return {
            'festival_films': cache_data.get('festival_films', {}),
            'oscar_contenders': cache_data.get('oscar_contenders', [])
        }


def main():
    """Standalone script to update awards cache"""
    updater = AwardsUpdater()

    print("=" * 60)
    print("Awards Predictions Updater")
    print("=" * 60)

    # Force update
    success = updater.update_cache()

    if success:
        print("\n" + "=" * 60)
        print("Update completed successfully!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Update failed - using existing data")
        print("=" * 60)


if __name__ == '__main__':
    main()
