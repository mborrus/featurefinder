"""
Scraper for Angelika Film Center NYC
"""
from typing import List
from .base import BaseScraper, Screening
from config import get_theater_url
import re


class AngelikaScraper(BaseScraper):
    """Scrapes Angelika Film Center NYC"""

    def __init__(self):
        super().__init__('Angelika Film Center')
        self.base_url = 'https://angelikafilmcenter.com'

    def scrape(self) -> List[Screening]:
        """Scrape Angelika Film Center schedule"""
        screenings = []

        try:
            url = f'{self.base_url}/nyc'
            print("  Using Playwright to render JavaScript content...")

            # Angelika is a React app - requires JavaScript rendering
            # Wait for movie cards/listings to load
            soup = self.fetch_page_js(url, wait_selector='.movie-card, .film-card, [class*="movie"], [class*="film"]', timeout=40000)

            if not soup:
                print("  Playwright failed, falling back to regular fetch...")
                soup = self.fetch_page(url)

            if not soup:
                return screenings

            # Find film listings - look for common patterns in cinema websites
            film_elements = soup.find_all(['div', 'article', 'li', 'section'],
                                         class_=re.compile(r'movie|film|show|screening|card|item|session', re.I))

            print(f"  Found {len(film_elements)} potential film elements")

            for element in film_elements[:40]:
                try:
                    screening = self._parse_film(element)
                    if screening:
                        screenings.append(screening)
                except Exception as e:
                    print(f"  Error parsing Angelika screening: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping Angelika Film Center: {e}")

        return screenings

    def _parse_film(self, element) -> Screening:
        """Parse a film element"""
        # Extract title
        title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5'], class_=re.compile(r'title|name|film|movie', re.I))
        if not title_elem:
            title_elem = element.find(['h2', 'h3', 'h4', 'a'])

        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        if not title or len(title) < 2:
            return None
        
        # Filter out menu items and non-film content
        title_upper = title.upper()
        menu_keywords = ['COFFEE', 'ESPRESSO', 'FOOD', 'DRINK', 'MENU', 'CONCESSION', 
                        'BEVERAGE', 'SNACK', 'MEMBERSHIP', 'GIFT CARD', 'COMING SOON']
        if any(keyword in title_upper for keyword in menu_keywords):
            return None
        
        # Filter out titles that are all caps and very short (likely headers/labels)
        if title == title_upper and len(title.split()) <= 3:
            return None

        # Extract description
        desc_elem = element.find(['p', 'div', 'span'], class_=re.compile(r'description|synopsis|summary|overview', re.I))
        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ''

        # Extract director
        director_elem = element.find(['span', 'div', 'p'], class_=re.compile(r'director|by|filmmaker', re.I))
        director = director_elem.get_text(strip=True) if director_elem else ''

        # Sometimes director is in description
        if not director:
            director_match = re.search(r'(?:directed by|dir\.|director)\s+([^,.\n]+)', element.get_text(), re.I)
            if director_match:
                director = director_match.group(1).strip()

        # Extract date/time
        date_elem = element.find(['time', 'span', 'div'], class_=re.compile(r'date|time|when|showing|session', re.I))
        date_str = date_elem.get_text(strip=True) if date_elem else ''

        # Determine special notes
        full_text = element.get_text()
        special_note = self._determine_special_note(full_text)

        # Extract URL
        link = element.find('a', href=True)
        url = link['href'] if link else ''
        if url and not url.startswith('http'):
            url = self.base_url + url

        # Ensure every screening has a ticket URL (fallback to theater homepage)
        if not url:
            url = get_theater_url('Angelika Film Center')

        return Screening(
            title=title,
            theater='Angelika Film Center',
            date=date_str,
            description=description,
            special_note=special_note,
            director=director,
            url=url,
            priority=2  # Angelika is a high-quality arthouse theater
        )

    def _determine_special_note(self, text: str) -> str:
        """Determine what makes this screening special"""
        notes = []
        text_lower = text.lower()

        if any(word in text_lower for word in ['q&a', 'q & a']):
            notes.append('Q&A')
        if 'director' in text_lower and any(word in text_lower for word in ['appearance', 'present', 'person', 'attendance']):
            notes.append('Director Appearance')
        if '35mm' in text_lower:
            notes.append('35mm')
        if '70mm' in text_lower:
            notes.append('70mm')
        if 'restoration' in text_lower or 'restored' in text_lower or '4k' in text_lower:
            notes.append('Restoration')
        if 'premiere' in text_lower or 'opening night' in text_lower:
            notes.append('Premiere')
        if any(word in text_lower for word in ['retrospective', 'series', 'festival']):
            notes.append('Special Series')
        if 'exclusive' in text_lower:
            notes.append('Exclusive')
        if any(word in text_lower for word in ['repertory', 'revival', 'classic screening']):
            notes.append('Repertory')
        if 'midnight' in text_lower:
            notes.append('Midnight Screening')

        return ' | '.join(notes) if notes else 'Arthouse Screening'
