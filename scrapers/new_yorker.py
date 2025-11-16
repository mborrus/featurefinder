"""
Scraper for The New Yorker's Goings On About Town - Movies section
Highly curated film recommendations and special screenings
"""
from typing import List
from .base import BaseScraper, Screening
from config import get_theater_url
import re


class NewYorkerScraper(BaseScraper):
    """Scrapes The New Yorker's film section"""

    def __init__(self):
        super().__init__('The New Yorker')
        self.base_url = 'https://www.newyorker.com'

    def scrape(self) -> List[Screening]:
        """Scrape The New Yorker's Goings On About Town - Movies"""
        screenings = []

        try:
            # The New Yorker's curated film section
            url = f'{self.base_url}/goings-on-about-town/movies'
            soup = self.fetch_page(url)

            if not soup:
                return screenings

            # Find film listings - The New Yorker uses specific article/card structures
            film_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'goings-on|river-item|movie|film|card|listing', re.I))

            for element in film_elements[:40]:  # Slightly more since they're curated
                try:
                    screening = self._parse_film(element)
                    if screening:
                        screenings.append(screening)
                except Exception as e:
                    print(f"Error parsing New Yorker film: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping The New Yorker: {e}")

        return screenings

    def _parse_film(self, element) -> Screening:
        """Parse a film element"""
        # Extract title
        title_elem = element.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'title|heading|name', re.I))
        if not title_elem:
            title_elem = element.find(['h2', 'h3', 'h4', 'a'])

        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        # Remove common prefixes
        title = re.sub(r'^(Review:|Critic\'s Pick:|Now Showing:)\s*', '', title, flags=re.I)

        if not title or len(title) < 2:
            return None

        # Extract description/review excerpt
        desc_elem = element.find(['p', 'div'], class_=re.compile(r'description|excerpt|summary|dek|body', re.I))
        description = desc_elem.get_text(strip=True)[:250] if desc_elem else ''

        # Extract director
        director = ''
        director_elem = element.find(['span', 'div', 'p'], class_=re.compile(r'director|filmmaker|byline', re.I))
        if director_elem:
            director = director_elem.get_text(strip=True)
        else:
            # Sometimes director is in the description
            director_match = re.search(r'(?:directed by|dir\.|director)\s+([^,.\n]+)', element.get_text(), re.I)
            if director_match:
                director = director_match.group(1).strip()

        # Extract venue/theater
        venue_elem = element.find(['span', 'div', 'p', 'a'], class_=re.compile(r'venue|location|theater|where', re.I))
        theater = 'Various NYC Theaters'  # Default for The New Yorker
        if venue_elem:
            theater_text = venue_elem.get_text(strip=True)
            # Try to extract specific theater names
            theater = self._extract_theater(theater_text)

        # Extract date/time
        date_elem = element.find(['time', 'span', 'div'], class_=re.compile(r'date|time|when|schedule', re.I))
        date_str = date_elem.get_text(strip=True) if date_elem else ''

        # Determine special notes
        full_text = element.get_text()
        special_note = self._determine_special_note(full_text)

        # Extract ticket availability
        ticket_status, ticket_sale_date = self.extract_ticket_availability(full_text)

        # Extract URL
        link = element.find('a', href=True)
        url = link['href'] if link else ''
        if url and not url.startswith('http'):
            url = self.base_url + url

        # Ensure every screening has a ticket URL (fallback to theater or New Yorker homepage)
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
            director=director,
            url=url,
            priority=1,  # The New Yorker has excellent curation
            tickets_on_sale=ticket_status,
            ticket_sale_date=ticket_sale_date
        )

    def _extract_theater(self, text: str) -> str:
        """Extract theater name from venue text"""
        theaters = [
            'Film Forum', 'IFC Center', 'Metrograph', 'Angelika',
            'Paris Theater', 'Lincoln Center', 'Film at Lincoln Center',
            'AMC Lincoln Square', 'AMC 84th', 'Anthology Film Archives',
            'BAM', 'Museum of Modern Art', 'MoMA', 'Quad Cinema',
            'Nitehawk', 'Roxy Cinema', 'Alamo Drafthouse'
        ]

        text_lower = text.lower()
        for theater in theaters:
            if theater.lower() in text_lower:
                # Normalize theater names
                if 'lincoln center' in theater.lower() or 'film at lincoln' in theater.lower():
                    return 'Film at Lincoln Center'
                elif 'amc lincoln' in theater.lower():
                    return 'AMC Lincoln Square'
                elif 'amc 84' in theater.lower():
                    return 'AMC 84th Street'
                else:
                    return theater

        return 'Various NYC Theaters'

    def _determine_special_note(self, text: str) -> str:
        """Determine what makes this screening special"""
        notes = []
        text_lower = text.lower()

        # Check for New Yorker-specific markers
        if "critic's pick" in text_lower or "critics' pick" in text_lower:
            notes.append("Critic's Pick")
        if any(word in text_lower for word in ['q&a', 'q & a']):
            notes.append('Q&A')
        if 'director' in text_lower and any(word in text_lower for word in ['appearance', 'present', 'person', 'attendance', 'in person']):
            notes.append('Director Appearance')
        if '35mm' in text_lower:
            notes.append('35mm')
        if '70mm' in text_lower:
            notes.append('70mm')
        if 'imax' in text_lower:
            notes.append('IMAX')
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

        return ' | '.join(notes) if notes else ''
