"""
Scraper for Time Out NYC film events
"""
from typing import List
from .base import BaseScraper, Screening
import re


class TimeOutScraper(BaseScraper):
    """Scrapes Time Out NYC for film events"""

    def __init__(self):
        super().__init__('Time Out NYC')
        self.base_url = 'https://www.timeout.com'

    def scrape(self) -> List[Screening]:
        """Scrape Time Out NYC film events"""
        screenings = []

        try:
            # Time Out has film events section
            url = f'{self.base_url}/newyork/film'
            soup = self.fetch_page(url)

            if not soup:
                return screenings

            # Find event listings - Time Out uses article.tile structure
            # Based on diagnostics: <article class="tile _article_wkzyo_1">
            event_elements = soup.find_all('article', class_=re.compile(r'tile|article', re.I))

            # Fallback to other structures if needed
            if not event_elements:
                event_elements = soup.find_all(['div', 'li'], class_=re.compile(r'event|card|listing|film', re.I))

            for element in event_elements[:30]:
                try:
                    screening = self._parse_event(element)
                    if screening and self._is_special(screening):
                        screenings.append(screening)
                except Exception as e:
                    print(f"Error parsing Time Out event: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping Time Out NYC: {e}")

        return screenings

    def _parse_event(self, element) -> Screening:
        """Parse an event element"""
        # Extract title - Time Out uses h3 with specific classes
        # Based on diagnostics: <h3 class="_h3_c6c0h_1">Review: Frankenstein</h3>
        title_elem = element.find(['h3', 'h2', 'h4'], class_=re.compile(r'_h\d|title|heading', re.I))
        if not title_elem:
            title_elem = element.find('a', class_=re.compile(r'title|name', re.I))
        if not title_elem:
            title_elem = element.find(['h2', 'h3', 'h4', 'a'])

        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        if not title or len(title) < 3:
            return None

        # Extract venue
        venue_elem = element.find(['span', 'div', 'p', 'a'], class_=re.compile(r'venue|location|theater', re.I))
        theater = venue_elem.get_text(strip=True) if venue_elem else 'Venue TBA'

        # Extract description
        desc_elem = element.find(['p', 'div'], class_=re.compile(r'description|summary|excerpt', re.I))
        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ''

        # Extract date/time
        date_elem = element.find(['time', 'span', 'div'], class_=re.compile(r'date|time|when', re.I))
        date_str = date_elem.get_text(strip=True) if date_elem else ''

        # Determine special notes
        full_text = element.get_text()
        special_note = self._determine_special_note(full_text)

        # Extract URL
        link = element.find('a', href=True)
        url = link['href'] if link else ''
        if url and not url.startswith('http'):
            url = self.base_url + url

        return Screening(
            title=title,
            theater=theater,
            date=date_str,
            description=description,
            special_note=special_note,
            url=url,
            priority=3
        )

    def _determine_special_note(self, text: str) -> str:
        """Determine what makes this screening special"""
        notes = []
        text_lower = text.lower()

        if any(word in text_lower for word in ['q&a', 'q & a']):
            notes.append('Q&A')
        if 'director' in text_lower and 'appearance' in text_lower:
            notes.append('Director Appearance')
        if 'imax' in text_lower:
            notes.append('IMAX')
        if '70mm' in text_lower or '35mm' in text_lower:
            notes.append('Film Print')
        if 'premiere' in text_lower:
            notes.append('Premiere')
        if 'festival' in text_lower:
            notes.append('Festival')
        if 'screening' in text_lower and any(word in text_lower for word in ['special', 'advance', 'early']):
            notes.append('Special Screening')

        return ' | '.join(notes) if notes else ''

    def _is_special(self, screening: Screening) -> bool:
        """Check if this is a special screening worth including"""
        # Must have either special notes or be at a known theater
        if screening.special_note:
            return True

        # Check if it's at a known specialty theater
        specialty_theaters = ['film forum', 'ifc', 'metrograph', 'angelika', 'paris', 'anthology']
        return any(theater in screening.theater.lower() for theater in specialty_theaters)
