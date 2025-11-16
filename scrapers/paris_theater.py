"""
Scraper for Paris Theater
"""
from typing import List
from .base import BaseScraper, Screening
from config import get_theater_url
import re


class ParisTheaterScraper(BaseScraper):
    """Scrapes Paris Theater - a priority theater focused on limited/arthouse releases"""

    def __init__(self):
        super().__init__('Paris Theater')
        self.base_url = 'https://www.paristheatrenyc.com'

    def scrape(self) -> List[Screening]:
        """Scrape Paris Theater schedule"""
        screenings = []

        try:
            # Try main page first
            url = self.base_url
            print("  Using Playwright to render JavaScript content...")

            # Use JS rendering as many modern theater sites are JavaScript-heavy
            soup = self.fetch_page_js(url, wait_selector='.film, .movie, .screening, .event, article')

            if not soup:
                print("  Playwright failed, falling back to regular fetch...")
                soup = self.fetch_page(url)

            if not soup:
                return screenings

            # Find film listings - try multiple common patterns
            film_elements = soup.find_all(['div', 'article', 'li', 'section'],
                                         class_=re.compile(r'film|movie|screening|event|card|item|show', re.I))

            for element in film_elements[:30]:
                try:
                    screening = self._parse_film(element)
                    if screening:
                        screenings.append(screening)
                except Exception as e:
                    print(f"Error parsing Paris Theater screening: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping Paris Theater: {e}")

        return screenings

    def _parse_film(self, element) -> Screening:
        """Parse a film element"""
        # Extract title
        title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a'], class_=re.compile(r'title|name|film', re.I))
        if not title_elem:
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a'])

        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        if not title or len(title) < 2:
            return None

        # Extract description
        desc_elem = element.find(['p', 'div'], class_=re.compile(r'description|synopsis|excerpt|summary|about', re.I))
        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ''

        # Extract director
        director_elem = element.find(['span', 'div', 'p'], class_=re.compile(r'director|filmmaker|by', re.I))
        director = director_elem.get_text(strip=True) if director_elem else ''

        # Extract date/time
        date_elem = element.find(['time', 'span', 'div'], class_=re.compile(r'date|time|when|showing|schedule', re.I))
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
            url = get_theater_url('Paris Theater')

        return Screening(
            title=title,
            theater='Paris Theater',
            date=date_str,
            description=description,
            special_note=special_note,
            director=director,
            url=url,
            priority=1  # Priority theater for limited/arthouse releases
        )

    def _determine_special_note(self, text: str) -> str:
        """Determine what makes this screening special"""
        notes = []
        text_lower = text.lower()

        # Paris Theater specializes in limited/arthouse releases
        if 'limited' in text_lower or 'exclusive' in text_lower:
            notes.append('Limited Release')
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
        if 'premiere' in text_lower or 'opening' in text_lower:
            notes.append('Premiere')
        if any(word in text_lower for word in ['retrospective', 'series', 'festival']):
            notes.append('Special Series')
        if any(word in text_lower for word in ['repertory', 'revival', 'classic']):
            notes.append('Repertory')
        if 'arthouse' in text_lower or 'art house' in text_lower:
            notes.append('Arthouse')

        return ' | '.join(notes) if notes else 'Curated Screening'
