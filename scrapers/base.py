"""
Base scraper class for movie screening sources
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import time


class Screening:
    """Data class for a movie screening"""
    def __init__(self, title: str, theater: str, date: str = '', time_slot: str = '',
                 description: str = '', special_note: str = '', director: str = '',
                 ticket_info: str = '', url: str = '', priority: int = 5,
                 ticket_sale_date: str = ''):
        self.title = title
        self.theater = theater
        self.date = date
        self.time_slot = time_slot
        self.description = description
        self.special_note = special_note
        self.director = director
        self.ticket_info = ticket_info
        self.url = url
        self.priority = priority  # Lower number = higher priority
        self.ticket_sale_date = ticket_sale_date  # When tickets go on sale

    def to_dict(self) -> Dict:
        return {
            'title': self.title,
            'theater': self.theater,
            'date': self.date,
            'time': self.time_slot,
            'description': self.description,
            'special_note': self.special_note,
            'director': self.director,
            'ticket_info': self.ticket_info,
            'url': self.url,
            'priority': self.priority,
            'ticket_sale_date': self.ticket_sale_date
        }

    def __repr__(self):
        return f"Screening({self.title} at {self.theater} on {self.date})"


class BaseScraper(ABC):
    """Base class for all scrapers"""

    def __init__(self, name: str):
        self.name = name
        self.session = requests.Session()
        # Better headers to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    @abstractmethod
    def scrape(self) -> List[Screening]:
        """Scrape screenings from the source"""
        pass

    def fetch_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch a page and return BeautifulSoup object"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                if attempt == retries - 1:
                    print(f"Failed to fetch {url}: {e}")
                    return None
                time.sleep(2 ** attempt)
        return None

    def fetch_page_js(self, url: str, wait_selector: str = None, timeout: int = 30000) -> Optional[BeautifulSoup]:
        """
        Fetch a JavaScript-rendered page using Playwright

        Args:
            url: URL to fetch
            wait_selector: CSS selector to wait for before returning (e.g., 'article.tile')
            timeout: Maximum time to wait in milliseconds (default 30s)

        Returns:
            BeautifulSoup object with rendered content or None if failed
        """
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                # Launch browser in headless mode
                browser = p.chromium.launch(headless=True)

                # Create a new page with realistic viewport
                page = browser.new_page(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )

                # Navigate to the page (use 'domcontentloaded' which is more reliable)
                page.goto(url, wait_until='domcontentloaded', timeout=timeout)

                # Wait for specific content to load if selector provided
                if wait_selector:
                    try:
                        page.wait_for_selector(wait_selector, timeout=timeout)
                    except Exception as e:
                        print(f"  Warning: Selector '{wait_selector}' not found, continuing anyway...")

                # Give JavaScript a moment to finish rendering
                page.wait_for_timeout(2000)

                # Get the fully rendered HTML
                content = page.content()

                browser.close()

                return BeautifulSoup(content, 'html.parser')

        except ImportError:
            print(f"  Playwright not installed. Run: pip install playwright && playwright install chromium")
            return None
        except Exception as e:
            print(f"  Failed to fetch {url} with Playwright: {e}")
            return None

    def is_special_screening(self, text: str) -> bool:
        """Check if text indicates a special screening"""
        text_lower = text.lower()
        keywords = [
            'q&a', 'q & a', 'director', 'opening night', 'premiere',
            'festival', 'special screening', 'advance screening',
            'preview', 'repertory', 'retrospective', 'restoration',
            '35mm', '70mm', 'imax', 'exclusive', 'limited release',
            'anniversary', 'midnight', 'classics', 'cult'
        ]
        return any(keyword in text_lower for keyword in keywords)

    def _get_awards_data(self) -> tuple:
        """
        Get awards data, preferring live cache over hardcoded data
        Returns: (festival_films_dict, oscar_contenders_list, festival_keywords, awards_keywords)
        """
        try:
            # Try to load from live cache
            from config import get_live_awards_data, FESTIVAL_KEYWORDS, AWARDS_KEYWORDS
            festival_films, oscar_contenders = get_live_awards_data(use_cache=True)
            return festival_films, oscar_contenders, FESTIVAL_KEYWORDS, AWARDS_KEYWORDS
        except Exception:
            # Fall back to hardcoded data
            from config import FESTIVAL_FILMS_2024_2025, OSCAR_CONTENDERS_2025, FESTIVAL_KEYWORDS, AWARDS_KEYWORDS
            return FESTIVAL_FILMS_2024_2025, OSCAR_CONTENDERS_2025, FESTIVAL_KEYWORDS, AWARDS_KEYWORDS

    def is_festival_film(self, title: str, description: str = '') -> bool:
        """
        Check if a film premiered at a major festival
        Uses live cache data when available (updated weekly)

        Args:
            title: Film title
            description: Film description/notes (may contain festival mentions)

        Returns:
            True if film is from a major festival
        """
        festival_films, _, festival_keywords, _ = self._get_awards_data()

        # Normalize title for matching
        title_lower = title.lower().strip()

        # Check against known festival films database
        if title_lower in festival_films:
            return True

        # Check description for festival keywords
        combined_text = f"{title} {description}".lower()
        return any(keyword in combined_text for keyword in festival_keywords)

    def is_awards_contender(self, title: str, description: str = '') -> bool:
        """
        Check if a film is an Oscar/awards contender
        Uses live cache data when available (updated weekly)

        Args:
            title: Film title
            description: Film description/notes (may contain awards mentions)

        Returns:
            True if film is an awards contender
        """
        _, oscar_contenders, _, awards_keywords = self._get_awards_data()

        # Normalize title for matching
        title_lower = title.lower().strip()

        # Check against Oscar contenders list
        if title_lower in oscar_contenders:
            return True

        # Check description for awards keywords
        combined_text = f"{title} {description}".lower()
        return any(keyword in combined_text for keyword in awards_keywords)

    def is_prestigious_film(self, title: str, description: str = '') -> bool:
        """
        Check if a film is prestigious (festival premier or awards contender)

        Args:
            title: Film title
            description: Film description/notes

        Returns:
            True if film is prestigious
        """
        return self.is_festival_film(title, description) or self.is_awards_contender(title, description)

    def get_festival_info(self, title: str) -> Dict:
        """
        Get festival and awards information for a film
        Uses live cache data when available (updated weekly)

        Args:
            title: Film title

        Returns:
            Dictionary with festival and awards info, or empty dict if not found
        """
        festival_films, _, _, _ = self._get_awards_data()

        title_lower = title.lower().strip()
        return festival_films.get(title_lower, {})
