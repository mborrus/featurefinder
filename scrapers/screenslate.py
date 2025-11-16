"""
Scraper for screenslate.com - comprehensive NYC film screening aggregator
"""
from typing import List
from .base import BaseScraper, Screening
from config import get_theater_url
from datetime import datetime, timedelta
import re


class ScreenslateScraper(BaseScraper):
    """Scrapes screenslate.com for NYC special screenings"""

    def __init__(self):
        super().__init__('Screenslate')
        self.base_url = 'https://www.screenslate.com'

    def scrape(self) -> List[Screening]:
        """Scrape screenslate for upcoming special screenings"""
        screenings = []

        try:
            # Screenslate has a clean listings page - uses JavaScript rendering
            url = f'{self.base_url}/listings'
            print("  Using Playwright to render JavaScript content...")

            # Use JS rendering and wait for screening elements to load
            soup = self.fetch_page_js(url, wait_selector='.view-screenings')

            if not soup:
                print("  Playwright failed, falling back to regular fetch...")
                soup = self.fetch_page(url)

            if not soup:
                return screenings

            # Find all screening entries
            # Screenslate typically uses article or div elements for each screening
            screening_elements = soup.find_all(['article', 'div'], class_=re.compile(r'screening|listing|event', re.I))

            for element in screening_elements[:50]:  # Limit to avoid too much data
                try:
                    screening = self._parse_screening(element)
                    if screening and self._is_relevant(screening):
                        screenings.append(screening)
                except Exception as e:
                    print(f"Error parsing screenslate screening: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping Screenslate: {e}")

        return screenings

    def _parse_screening(self, element) -> Screening:
        """Parse a single screening element"""
        # Extract title
        title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name|film', re.I))
        if not title_elem:
            title_elem = element.find('a')

        title = title_elem.get_text(strip=True) if title_elem else ''

        # Extract theater/venue
        theater_elem = element.find(['span', 'div', 'p'], class_=re.compile(r'venue|theater|location', re.I))
        theater = theater_elem.get_text(strip=True) if theater_elem else 'Venue TBA'

        # Extract date/time
        date_elem = element.find(['time', 'span', 'div'], class_=re.compile(r'date|time|when', re.I))
        date_str = date_elem.get_text(strip=True) if date_elem else ''

        # Extract description
        desc_elem = element.find(['p', 'div'], class_=re.compile(r'description|synopsis|about', re.I))
        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ''

        # Extract link
        link_elem = element.find('a', href=True)
        url = self.base_url + link_elem['href'] if link_elem and link_elem['href'].startswith('/') else ''

        # Determine special notes
        full_text = element.get_text()
        special_note = self._extract_special_notes(full_text)

        # Ensure every screening has a ticket URL (fallback to theater or Screenslate homepage)
        if not url:
            # Try to get URL for the specific theater
            theater_url = get_theater_url(theater)
            url = theater_url if theater_url else self.base_url

        return Screening(
            title=title,
            theater=theater,
            date=date_str,
            description=description,
            special_note=special_note,
            url=url,
            priority=2
        )

    def _extract_special_notes(self, text: str) -> str:
        """Extract special screening information"""
        notes = []
        text_lower = text.lower()

        if 'imax' in text_lower:
            notes.append('IMAX')
        if '70mm' in text_lower:
            notes.append('70mm')
        if '35mm' in text_lower:
            notes.append('35mm')
        if any(word in text_lower for word in ['q&a', 'q & a']):
            notes.append('Q&A')
        if 'director' in text_lower and any(word in text_lower for word in ['appearance', 'present', 'attendance']):
            notes.append('Director Appearance')
        if 'premiere' in text_lower:
            notes.append('Premiere')
        if 'festival' in text_lower:
            notes.append('Festival Screening')
        if any(word in text_lower for word in ['repertory', 'retrospective', 'classics']):
            notes.append('Repertory')
        if 'restoration' in text_lower:
            notes.append('Restoration')

        return ' | '.join(notes) if notes else ''

    def _is_relevant(self, screening: Screening) -> bool:
        """Check if screening is relevant (Manhattan, special event)"""
        # Skip if Brooklyn (unless explicitly special)
        if 'brooklyn' in screening.theater.lower() and not screening.special_note:
            return False

        # Include if it has special notes or is from a known art house theater
        if screening.special_note:
            return True

        # Include if from repertory/art house theaters
        art_house_theaters = ['film forum', 'ifc', 'metrograph', 'anthology', 'paris', 'angelika']
        return any(theater in screening.theater.lower() for theater in art_house_theaters)
