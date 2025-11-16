"""
Scraper for Film Forum
"""
from typing import List
from .base import BaseScraper, Screening
from config import get_theater_url
import re


class FilmForumScraper(BaseScraper):
    """Scrapes Film Forum repertory theater"""

    def __init__(self):
        super().__init__('Film Forum')
        self.base_url = 'https://filmforum.org'

    def scrape(self) -> List[Screening]:
        """Scrape Film Forum schedule"""
        screenings = []

        try:
            url = f'{self.base_url}/now-showing'
            soup = self.fetch_page(url)

            if not soup:
                return screenings

            # Film Forum typically has divs or articles for each film
            film_elements = soup.find_all(['div', 'article'], class_=re.compile(r'film|movie|screening|event', re.I))

            for element in film_elements[:30]:
                try:
                    screening = self._parse_film(element)
                    if screening:
                        screenings.append(screening)
                except Exception as e:
                    print(f"Error parsing Film Forum screening: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping Film Forum: {e}")

        return screenings

    def _parse_film(self, element) -> Screening:
        """Parse a film element"""
        # Extract title
        title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name', re.I))
        if not title_elem:
            title_elem = element.find(['h1', 'h2', 'h3', 'h4'])

        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)

        # Extract director if available
        director_elem = element.find(['span', 'div', 'p'], class_=re.compile(r'director', re.I))
        director = director_elem.get_text(strip=True) if director_elem else ''

        # Extract description
        desc_elem = element.find(['p', 'div'], class_=re.compile(r'description|synopsis|summary', re.I))
        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ''

        # Extract date/time
        date_elem = element.find(['time', 'span', 'div'], class_=re.compile(r'date|time|when|showing', re.I))
        date_str = date_elem.get_text(strip=True) if date_elem else ''

        # Film Forum is all repertory/special screenings
        full_text = element.get_text()
        special_note = self._determine_special_note(full_text, title)

        # Extract URL
        link = element.find('a', href=True)
        url = link['href'] if link else ''
        if url and not url.startswith('http'):
            url = self.base_url + url

        # Ensure every screening has a ticket URL (fallback to theater homepage)
        if not url:
            url = get_theater_url('Film Forum')

        return Screening(
            title=title,
            theater='Film Forum',
            date=date_str,
            description=description,
            special_note=special_note,
            director=director,
            url=url,
            priority=1  # Film Forum is always special/repertory
        )

    def _determine_special_note(self, text: str, title: str) -> str:
        """Determine what makes this screening special"""
        notes = []
        text_lower = text.lower()

        # Film Forum specializes in repertory
        notes.append('Repertory')

        if '35mm' in text_lower:
            notes.append('35mm')
        if '70mm' in text_lower:
            notes.append('70mm')
        if 'restoration' in text_lower or 'restored' in text_lower:
            notes.append('Restoration')
        if any(word in text_lower for word in ['q&a', 'q & a']):
            notes.append('Q&A')
        if 'director' in text_lower and 'appearance' in text_lower:
            notes.append('Director Appearance')
        if 'premiere' in text_lower or 'opening' in text_lower:
            notes.append('Premiere')
        if 'series' in text_lower or 'retrospective' in text_lower:
            notes.append('Special Series')

        return ' | '.join(notes)
