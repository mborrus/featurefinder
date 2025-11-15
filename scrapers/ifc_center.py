"""
Scraper for IFC Center
"""
from typing import List
from .base import BaseScraper, Screening
import re


class IFCCenterScraper(BaseScraper):
    """Scrapes IFC Center"""

    def __init__(self):
        super().__init__('IFC Center')
        self.base_url = 'https://www.ifccenter.com'

    def scrape(self) -> List[Screening]:
        """Scrape IFC Center schedule"""
        screenings = []

        try:
            url = f'{self.base_url}/films'
            soup = self.fetch_page(url)

            if not soup:
                return screenings

            # Find film listings
            film_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'film|movie|screening|event|card', re.I))

            for element in film_elements[:30]:
                try:
                    screening = self._parse_film(element)
                    if screening:
                        screenings.append(screening)
                except Exception as e:
                    print(f"Error parsing IFC Center screening: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping IFC Center: {e}")

        return screenings

    def _parse_film(self, element) -> Screening:
        """Parse a film element"""
        # Extract title
        title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name|film', re.I))
        if not title_elem:
            title_elem = element.find(['h2', 'h3', 'a'])

        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        if not title or len(title) < 2:
            return None

        # Extract description
        desc_elem = element.find(['p', 'div'], class_=re.compile(r'description|synopsis|excerpt', re.I))
        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ''

        # Extract director
        director_elem = element.find(['span', 'div', 'p'], class_=re.compile(r'director|by', re.I))
        director = director_elem.get_text(strip=True) if director_elem else ''

        # Extract date/time
        date_elem = element.find(['time', 'span', 'div'], class_=re.compile(r'date|time|when|showing', re.I))
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
            theater='IFC Center',
            date=date_str,
            description=description,
            special_note=special_note,
            director=director,
            url=url,
            priority=2
        )

    def _determine_special_note(self, text: str) -> str:
        """Determine what makes this screening special"""
        notes = []
        text_lower = text.lower()

        if any(word in text_lower for word in ['q&a', 'q & a']):
            notes.append('Q&A')
        if 'director' in text_lower and any(word in text_lower for word in ['appearance', 'present', 'person']):
            notes.append('Director Appearance')
        if '35mm' in text_lower:
            notes.append('35mm')
        if 'restoration' in text_lower or 'restored' in text_lower:
            notes.append('Restoration')
        if 'midnight' in text_lower:
            notes.append('Midnight Screening')
        if 'premiere' in text_lower:
            notes.append('Premiere')
        if any(word in text_lower for word in ['repertory', 'revival', 'classic']):
            notes.append('Repertory')
        if 'waverly midnights' in text_lower:
            notes.append('Waverly Midnights')

        return ' | '.join(notes) if notes else 'Special Screening'
