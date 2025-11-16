"""
Scraper for MoMA (Museum of Modern Art) Film Calendar
"""
from typing import List
from .base import BaseScraper, Screening
from config import get_theater_url
import re


class MoMAScraper(BaseScraper):
    """Scrapes MoMA's film calendar"""

    def __init__(self):
        super().__init__('MoMA')
        self.base_url = 'https://www.moma.org'

    def scrape(self) -> List[Screening]:
        """Scrape MoMA film calendar"""
        screenings = []

        try:
            # MoMA's film calendar page
            url = f'{self.base_url}/calendar/film'
            print("  Using Playwright to render JavaScript content...")

            # MoMA likely uses JavaScript for dynamic content
            # Wait for calendar entries to load
            soup = self.fetch_page_js(
                url,
                wait_selector='article, .event, .screening',
                timeout=40000
            )

            if not soup:
                print("  Playwright failed, falling back to regular fetch...")
                soup = self.fetch_page(url)

            if not soup:
                return screenings

            # Find film/event listings - try multiple strategies

            # Strategy 1: Look for article elements
            articles = soup.find_all('article')

            # Strategy 2: Look for divs/sections with event/film-related classes
            event_elements = soup.find_all(
                ['div', 'section', 'li', 'a'],
                class_=re.compile(r'event|film|movie|screening|calendar|card|item|entry|show', re.I)
            )

            # Strategy 3: Look for elements with data attributes (common in React apps)
            data_elements = soup.find_all(
                ['div', 'section', 'article'],
                attrs={'data-event': True}
            ) or soup.find_all(
                ['div', 'section', 'article'],
                attrs={'data-title': True}
            )

            # Strategy 4: Look for time elements (usually associated with events)
            time_containers = []
            time_elements = soup.find_all('time')
            for time_elem in time_elements:
                # Get the parent container
                parent = time_elem.find_parent(['article', 'div', 'section', 'li'])
                if parent and parent not in time_containers:
                    time_containers.append(parent)

            # Combine and deduplicate
            all_elements = articles + event_elements + data_elements + time_containers
            film_elements = list({id(elem): elem for elem in all_elements}.values())

            print(f"  Found {len(articles)} articles, {len(event_elements)} event elements, {len(data_elements)} data elements, {len(time_containers)} time containers")
            print(f"  Total: {len(film_elements)} potential film elements")

            for element in film_elements[:100]:  # Limit to first 100 to avoid too much processing
                try:
                    screening = self._parse_event(element)
                    if screening:
                        screenings.append(screening)
                except Exception as e:
                    # Silently skip parsing errors for cleaner output
                    continue

        except Exception as e:
            print(f"Error scraping MoMA: {e}")

        return screenings

    def _parse_event(self, element) -> Screening:
        """Parse an event element"""
        # Extract title
        title_elem = element.find(
            ['h1', 'h2', 'h3', 'h4', 'h5'],
            class_=re.compile(r'title|name|film|movie|heading|event', re.I)
        )
        if not title_elem:
            # Try finding any heading element
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5'])
        if not title_elem:
            # Try finding a link with substantial text
            title_elem = element.find('a', href=True)
            # Also check for data-title attribute
            if not title_elem and element.get('data-title'):
                title = element.get('data-title')
                title_elem = element  # Use element itself

        if not title_elem:
            return None

        title = title_elem.get_text(strip=True) if hasattr(title_elem, 'get_text') else str(title_elem)
        if not title or len(title) < 2:
            return None

        # Skip navigation and UI elements
        skip_words = [
            'filter', 'menu', 'search', 'login', 'sign up', 'subscribe',
            'newsletter', 'visit', 'plan your visit', 'tickets', 'membership',
            'hours', 'location', 'directions', 'accessibility', 'calendar',
            'exhibitions', 'today', 'this week', 'this month'
        ]
        if any(skip_word in title.lower() for skip_word in skip_words):
            return None

        # Skip if title is too short (likely not a film title)
        if len(title) < 3:
            return None

        # Extract description
        desc_elem = element.find(
            ['p', 'div', 'span'],
            class_=re.compile(r'description|synopsis|summary|excerpt|text|body|content', re.I)
        )
        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ''

        # Extract director
        director_elem = element.find(
            ['span', 'div', 'p'],
            class_=re.compile(r'director|by|filmmaker|artist|credit', re.I)
        )
        director = director_elem.get_text(strip=True) if director_elem else ''

        # Sometimes director is in the text content
        if not director:
            director_match = re.search(
                r'(?:directed by|dir\.|director|by)\s+([^,.|\n]+)',
                element.get_text(),
                re.I
            )
            if director_match:
                director = director_match.group(1).strip()

        # Extract date/time
        date_str = ''

        # Try time element first
        time_elem = element.find('time')
        if time_elem:
            # Check datetime attribute
            if time_elem.get('datetime'):
                date_str = time_elem.get('datetime')
            else:
                date_str = time_elem.get_text(strip=True)

        # Try class-based selectors
        if not date_str:
            date_elem = element.find(
                ['span', 'div', 'p'],
                class_=re.compile(r'date|time|when|day|showtime|schedule', re.I)
            )
            date_str = date_elem.get_text(strip=True) if date_elem else ''

        # Also look for time patterns in text
        if not date_str:
            time_match = re.search(r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)', element.get_text())
            if time_match:
                date_str = time_match.group(0)

        # Determine special notes
        full_text = element.get_text()
        special_note = self._determine_special_note(full_text, title)

        # Extract URL
        link = element.find('a', href=True)
        url = link['href'] if link else ''
        if url and not url.startswith('http'):
            url = self.base_url + url

        # Ensure every screening has a ticket URL (fallback to theater homepage)
        if not url:
            url = get_theater_url('MoMA')
            if not url:
                url = self.base_url + '/calendar/film'

        return Screening(
            title=title,
            theater='MoMA',
            date=date_str,
            description=description,
            special_note=special_note,
            director=director,
            url=url,
            priority=1  # MoMA has excellent repertory programming and filmmaker Q&As
        )

    def _determine_special_note(self, text: str, title: str) -> str:
        """Determine what makes this screening special - MoMA focus"""
        notes = []
        text_lower = text.lower()
        title_lower = title.lower()

        # Q&As and filmmaker appearances (MoMA is known for these)
        if any(word in text_lower for word in ['q&a', 'q & a', 'discussion', 'conversation']):
            notes.append('Q&A')
        if 'filmmaker' in text_lower and any(word in text_lower for word in ['appearance', 'present', 'person', 'attendance', 'in person']):
            notes.append('Filmmaker Appearance')
        if 'director' in text_lower and any(word in text_lower for word in ['appearance', 'present', 'person', 'attendance', 'in person']):
            notes.append('Director Appearance')
        if any(word in text_lower for word in ['artist', 'curator']) and any(word in text_lower for word in ['talk', 'discussion', 'present']):
            notes.append('Artist/Curator Talk')

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
        if 'new print' in text_lower or 'original print' in text_lower:
            notes.append('Special Print')

        # Premieres and special events
        if 'premiere' in text_lower or 'opening night' in text_lower:
            notes.append('Premiere')
        if 'closing night' in text_lower:
            notes.append('Closing Night')

        # MoMA special series and programs
        if any(word in text_lower for word in ['retrospective', 'series']):
            notes.append('Special Series')
        if 'festival' in text_lower:
            notes.append('Festival')
        if 'tribute' in text_lower or 'homage' in text_lower:
            notes.append('Tribute')
        if any(word in text_lower for word in ['repertory', 'revival', 'classic']):
            notes.append('Repertory')
        if 'exhibition' in text_lower:
            notes.append('Related to Exhibition')

        # Exclusive/special programming
        if 'exclusive' in text_lower:
            notes.append('Exclusive')
        if 'preview' in text_lower:
            notes.append('Preview Screening')
        if 'advance' in text_lower and 'screening' in text_lower:
            notes.append('Advance Screening')
        if 'rare' in text_lower or 'seldom seen' in text_lower:
            notes.append('Rare Screening')

        # MoMA-specific programming
        if 'to save and project' in text_lower:
            notes.append('To Save and Project')
        if 'contenders' in text_lower:
            notes.append('Contenders Series')
        if 'moma doc fortnight' in text_lower or 'documentary fortnight' in text_lower:
            notes.append('Doc Fortnight')

        return ' | '.join(notes) if notes else 'MoMA Film Screening'
