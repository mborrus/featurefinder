"""
Scraper for Film at Lincoln Center
"""
from typing import List
from .base import BaseScraper, Screening
import re


class FilmAtLincolnCenterScraper(BaseScraper):
    """Scrapes Film at Lincoln Center"""

    def __init__(self):
        super().__init__('Film at Lincoln Center')
        self.base_url = 'https://www.filmlinc.org'

    def scrape(self) -> List[Screening]:
        """Scrape Film at Lincoln Center schedule"""
        screenings = []

        try:
            # Use the now-playing page which shows all current screenings
            url = f'{self.base_url}/now-playing/'
            print("  Using Playwright to render JavaScript content...")

            # Film at Lincoln Center is a React/Next.js app - requires JavaScript rendering
            # Wait for film cards/listings to load - try multiple selectors
            soup = self.fetch_page_js(
                url,
                wait_selector='article',  # Most likely selector for film cards
                timeout=40000
            )

            if not soup:
                print("  Playwright failed, falling back to regular fetch...")
                soup = self.fetch_page(url)

            if not soup:
                return screenings

            # Find film listings - look for common patterns in React-based cinema websites
            # Try multiple strategies to find film content

            # Strategy 1: Look for article elements (common in modern React sites)
            articles = soup.find_all('article')

            # Strategy 2: Look for divs/sections with film-related classes
            film_divs = soup.find_all(
                ['div', 'section', 'li'],
                class_=re.compile(r'film|movie|card|screening|event|showtime|series|show|program', re.I)
            )

            # Strategy 3: If we didn't find much, look for containers with multiple links (often film grids)
            if len(articles) + len(film_divs) < 5:
                print("  Found few elements, trying broader search...")
                # Look for any div that contains multiple headings or links
                all_containers = soup.find_all(['div', 'section', 'main'])
                potential_containers = [
                    c for c in all_containers
                    if len(c.find_all(['h2', 'h3', 'h4'], limit=3)) >= 2
                ]
                film_divs.extend(potential_containers[:20])

            # Combine and deduplicate
            film_elements = list({id(elem): elem for elem in (articles + film_divs)}.values())

            print(f"  Found {len(articles)} articles, {len(film_divs)} film-related divs")
            print(f"  Total: {len(film_elements)} potential film elements")

            for element in film_elements[:50]:
                try:
                    screening = self._parse_film(element)
                    if screening:
                        screenings.append(screening)
                except Exception as e:
                    print(f"  Error parsing Film at Lincoln Center screening: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping Film at Lincoln Center: {e}")

        return screenings

    def _parse_film(self, element) -> Screening:
        """Parse a film element"""
        # Extract title - Lincoln Center often uses h2, h3 for film titles
        title_elem = element.find(
            ['h1', 'h2', 'h3', 'h4', 'h5'],
            class_=re.compile(r'title|name|film|movie|heading', re.I)
        )
        if not title_elem:
            # Try finding any heading element
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5'])
        if not title_elem:
            # Try finding a link with substantial text
            title_elem = element.find('a', href=True)

        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        if not title or len(title) < 2:
            return None

        # Skip if this looks like navigation or UI elements
        if any(skip_word in title.lower() for skip_word in ['filter', 'menu', 'search', 'login', 'sign up', 'subscribe', 'newsletter']):
            return None

        # Extract description
        desc_elem = element.find(
            ['p', 'div', 'span'],
            class_=re.compile(r'description|synopsis|summary|overview|excerpt|body', re.I)
        )
        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ''

        # Extract director
        director_elem = element.find(
            ['span', 'div', 'p'],
            class_=re.compile(r'director|by|filmmaker|credit', re.I)
        )
        director = director_elem.get_text(strip=True) if director_elem else ''

        # Sometimes director is in description or credits
        if not director:
            director_match = re.search(
                r'(?:directed by|dir\.|director|by)\s+([^,.|\n]+)',
                element.get_text(),
                re.I
            )
            if director_match:
                director = director_match.group(1).strip()

        # Extract date/time - Lincoln Center shows times prominently
        date_elem = element.find(
            ['time', 'span', 'div'],
            class_=re.compile(r'date|time|when|showing|showtime|session|schedule', re.I)
        )
        date_str = date_elem.get_text(strip=True) if date_elem else ''

        # Also look for time patterns in text
        if not date_str:
            time_match = re.search(r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)', element.get_text())
            if time_match:
                date_str = time_match.group(0)

        # Determine special notes - Lincoln Center is known for special series and festivals
        full_text = element.get_text()
        special_note = self._determine_special_note(full_text, title)

        # Extract URL
        link = element.find('a', href=True)
        url = link['href'] if link else ''
        if url and not url.startswith('http'):
            url = self.base_url + url

        return Screening(
            title=title,
            theater='Film at Lincoln Center',
            date=date_str,
            description=description,
            special_note=special_note,
            director=director,
            url=url,
            priority=1  # Film at Lincoln Center is highest priority - premier arthouse venue
        )

    def _determine_special_note(self, text: str, title: str) -> str:
        """Determine what makes this screening special - Lincoln Center focus"""
        notes = []
        text_lower = text.lower()
        title_lower = title.lower()

        # New York Film Festival - highest priority
        if any(word in text_lower or word in title_lower for word in ['nyff', 'new york film festival']):
            notes.append('NYFF')

        # Q&As and appearances
        if any(word in text_lower for word in ['q&a', 'q & a']):
            notes.append('Q&A')
        if 'director' in text_lower and any(word in text_lower for word in ['appearance', 'present', 'person', 'attendance', 'in person']):
            notes.append('Director Appearance')
        if any(word in text_lower for word in ['cast', 'filmmaker', 'actor']) and any(word in text_lower for word in ['appearance', 'present', 'person']):
            notes.append('Special Guest')

        # Film formats
        if '35mm' in text_lower:
            notes.append('35mm')
        if '70mm' in text_lower:
            notes.append('70mm')
        if '16mm' in text_lower:
            notes.append('16mm')

        # Restorations and special prints
        if 'restoration' in text_lower or 'restored' in text_lower or '4k' in text_lower:
            notes.append('Restoration')
        if 'remaster' in text_lower:
            notes.append('Remastered')

        # Premieres and special events
        if 'premiere' in text_lower or 'opening night' in text_lower:
            notes.append('Premiere')
        if 'closing night' in text_lower:
            notes.append('Closing Night')

        # Lincoln Center special series and programs
        if any(word in text_lower for word in ['retrospective', 'series']):
            notes.append('Special Series')
        if 'festival' in text_lower and 'nyff' not in notes:
            notes.append('Festival')
        if 'tribute' in text_lower or 'homage' in text_lower:
            notes.append('Tribute')
        if any(word in text_lower for word in ['repertory', 'revival', 'classic screening']):
            notes.append('Repertory')

        # Exclusive/special programming
        if 'exclusive' in text_lower:
            notes.append('Exclusive')
        if 'preview' in text_lower:
            notes.append('Preview Screening')
        if 'advance' in text_lower and 'screening' in text_lower:
            notes.append('Advance Screening')

        # Film Comment connection
        if 'film comment' in text_lower:
            notes.append('Film Comment Event')

        return ' | '.join(notes) if notes else 'Lincoln Center Screening'
