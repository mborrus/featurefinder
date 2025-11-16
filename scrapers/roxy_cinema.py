"""
Scraper for The Roxy Cinema
"""
from typing import List
from .base import BaseScraper, Screening
from config import get_theater_url
import re


class RoxyCinemaScraper(BaseScraper):
    """Scrapes The Roxy Cinema (Tribeca arthouse theater)"""

    def __init__(self):
        super().__init__('The Roxy Cinema')
        self.base_url = 'https://www.roxycinemanewyork.com'

    def scrape(self) -> List[Screening]:
        """Scrape Roxy Cinema schedule"""
        screenings = []

        try:
            # Get the Now Showing page
            url = f'{self.base_url}/now-showing'
            print("  Using Playwright to render JavaScript content...")

            # Use JS rendering as the site uses a carousel/slider
            soup = self.fetch_page_js(url, wait_selector='.swiper-slide, .screening-item, .hero__slider')

            if not soup:
                print("  Playwright failed, falling back to regular fetch...")
                soup = self.fetch_page(url)

            if not soup:
                return screenings

            # Find film listings - target the screening card class
            film_elements = soup.find_all(['div', 'article'],
                                         class_=re.compile(r'detailed-screening__card|rb-event__articles', re.I))

            for element in film_elements[:40]:  # Get more items since it's a carousel
                try:
                    screening = self._parse_film(element)
                    if screening:
                        screenings.append(screening)
                except Exception as e:
                    print(f"Error parsing Roxy Cinema screening: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping Roxy Cinema: {e}")

        return screenings

    def _parse_film(self, element) -> Screening:
        """Parse a film element"""
        # Extract title
        title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name|film', re.I))
        if not title_elem:
            title_elem = element.find(['h2', 'h3', 'h4', 'a'])

        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        # Filter out non-film content (buttons, notices, etc.)
        if not title or len(title) < 3:
            return None
        # Skip common button text and notices
        if title.lower() in ['buy', 'read more', 'view all', 'tickets']:
            return None
        # Skip obvious notices/announcements
        if 'complete listing' in title.lower() or 'announced soon' in title.lower():
            return None

        # Extract description
        desc_elem = element.find(['p', 'div'], class_=re.compile(r'description|synopsis|excerpt|summary', re.I))
        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ''

        # Extract director
        director_elem = element.find(['span', 'div', 'p'], class_=re.compile(r'director|filmmaker|by', re.I))
        director = director_elem.get_text(strip=True) if director_elem else ''

        # Extract date/time - Roxy uses format like "11.15.2025 | 3:00PM"
        date_elem = element.find(['time', 'span', 'div'], class_=re.compile(r'date|time|when|showing|schedule', re.I))
        date_str = date_elem.get_text(strip=True) if date_elem else ''

        # Determine special notes
        full_text = element.get_text()
        special_note = self._determine_special_note(full_text, title)

        # Extract URL - pattern is /screenings/[film-title-slug]/
        link = element.find('a', href=True)
        url = link['href'] if link else ''
        if url and not url.startswith('http'):
            url = self.base_url + url

        # Ensure every screening has a ticket URL (fallback to theater homepage)
        if not url:
            url = get_theater_url('The Roxy Cinema')

        return Screening(
            title=title,
            theater='The Roxy Cinema',
            date=date_str,
            description=description,
            special_note=special_note,
            director=director,
            url=url,
            priority=1  # Roxy Cinema is a curated arthouse theater
        )

    def _determine_special_note(self, text: str, title: str = '') -> str:
        """Determine what makes this screening special"""
        notes = []
        text_lower = text.lower()
        title_lower = title.lower()

        # Check for Q&A
        if any(word in text_lower for word in ['q&a', 'q & a', '+ q&a']):
            notes.append('Q&A')

        # Check for introductions
        if '+ intro' in text_lower or 'introduction' in text_lower:
            notes.append('Intro')

        # Check for director presence
        if 'director' in text_lower and any(word in text_lower for word in ['appearance', 'present', 'person', 'attendance', 'intro']):
            notes.append('Director Appearance')

        # Check for film formats
        if '35mm' in text_lower or '35mm' in title_lower:
            notes.append('35mm')
        if '70mm' in text_lower or '70mm' in title_lower:
            notes.append('70mm')
        if '16mm' in text_lower or '16mm' in title_lower:
            notes.append('16mm')

        # Check for restorations
        if 'restoration' in text_lower or 'restored' in text_lower or '4k' in text_lower:
            notes.append('Restoration')

        # Check for special events
        if 'premiere' in text_lower or 'opening' in text_lower:
            notes.append('Premiere')
        if 'midnight' in text_lower:
            notes.append('Midnight Screening')

        # Check for curated series (Roxy has "Making Waves:" and other series)
        if 'making waves' in text_lower:
            notes.append('Making Waves Series')
        if any(word in text_lower for word in ['retrospective', 'series', 'festival']):
            notes.append('Special Series')

        # Check for repertory/classics
        if any(word in text_lower for word in ['repertory', 'revival', 'classic']):
            notes.append('Repertory')

        # Check for exclusive screenings
        if 'exclusive' in text_lower:
            notes.append('Exclusive')

        return ' | '.join(notes) if notes else 'Curated Screening'
