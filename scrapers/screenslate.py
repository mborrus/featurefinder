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

            # Use JS rendering - wait for article tiles which are the screening cards
            # Screenslate uses article.tile for each screening
            soup = self.fetch_page_js(url, wait_selector='article.tile')

            if not soup:
                print("  Playwright failed, falling back to regular fetch...")
                soup = self.fetch_page(url)

            if not soup:
                return screenings

            # Find all screening entries
            # Screenslate uses article.tile for each screening card
            screening_elements = soup.find_all('article', class_='tile')

            # Fallback to other patterns if no tiles found
            if not screening_elements:
                print("  No article.tile elements found, trying broader search...")
                screening_elements = soup.find_all(['article', 'div'], class_=re.compile(r'screening|listing|event|tile|card', re.I))

            print(f"  Found {len(screening_elements)} potential screening elements")

            for element in screening_elements[:100]:  # Increased limit to get more screenings
                try:
                    screening = self._parse_screening(element)
                    if screening and self._is_relevant(screening):
                        screenings.append(screening)
                except Exception as e:
                    print(f"  Error parsing screening: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping Screenslate: {e}")

        return screenings

    def _parse_screening(self, element) -> Screening:
        """Parse a single screening element"""
        # Extract title - Screenslate uses h3 or h4 for film titles in tiles
        title_elem = element.find(['h3', 'h4', 'h2', 'h1'])
        if not title_elem:
            title_elem = element.find('a', class_=re.compile(r'title|film|screening', re.I))
        if not title_elem:
            title_elem = element.find('a')

        title = title_elem.get_text(strip=True) if title_elem else ''

        # Skip if no title found
        if not title:
            return None

        # Extract theater/venue - look for venue/theater in spans or divs
        theater_elem = element.find(['span', 'div', 'p', 'a'], class_=re.compile(r'venue|theater|location|cinema', re.I))
        if not theater_elem:
            # Sometimes venue is in a link
            venue_link = element.find('a', href=re.compile(r'/venues/', re.I))
            theater_elem = venue_link if venue_link else None

        theater = theater_elem.get_text(strip=True) if theater_elem else 'Venue TBA'

        # Extract date/time - Screenslate often uses time tags or date classes
        date_elem = element.find('time')
        if not date_elem:
            date_elem = element.find(['span', 'div'], class_=re.compile(r'date|time|when|showtime', re.I))

        date_str = ''
        if date_elem:
            # Try to get datetime attribute first (more accurate)
            date_str = date_elem.get('datetime', '') or date_elem.get_text(strip=True)

        # Extract description - look for synopsis or description
        desc_elem = element.find(['p', 'div'], class_=re.compile(r'description|synopsis|summary|about', re.I))
        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ''

        # Extract link - prioritize links to the screening page
        link_elem = element.find('a', href=re.compile(r'/screenings/', re.I))
        if not link_elem:
            link_elem = element.find('a', href=True)

        url = ''
        if link_elem and link_elem.get('href'):
            href = link_elem['href']
            url = self.base_url + href if href.startswith('/') else href

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
