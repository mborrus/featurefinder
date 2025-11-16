"""
Scraper for Alamo Drafthouse Lower Manhattan
"""
from typing import List
from .base import BaseScraper, Screening
from datetime import datetime, timedelta
import re


class AlamoDrafthouseScraper(BaseScraper):
    """Scrapes Alamo Drafthouse Lower Manhattan theater"""

    def __init__(self):
        super().__init__('Alamo Drafthouse')
        self.base_url = 'https://drafthouse.com'
        self.theater_name = 'Alamo Drafthouse Lower Manhattan'
        # Focus on Lower Manhattan location
        self.theater_url = f'{self.base_url}/nyc'

    def scrape(self) -> List[Screening]:
        """Scrape Alamo Drafthouse Lower Manhattan for upcoming screenings"""
        screenings = []

        print(f"  Checking {self.theater_name}...")

        try:
            # Alamo Drafthouse uses a JavaScript-heavy SPA, use Playwright
            # Wait for film/event elements to load
            soup = self.fetch_page_js(
                self.theater_url,
                wait_selector='[class*="film"], [class*="movie"], [class*="event"], [class*="session"], a[href*="/show/"]',
                timeout=60000
            )

            if not soup:
                print(f"    Failed to load {self.theater_name}")
                return screenings

            # Look for event/film links and cards
            # Alamo Drafthouse typically has links to individual shows
            event_links = soup.find_all('a', href=re.compile(r'/(show|event|film|session)/'))

            # Also look for common container patterns
            event_containers = soup.find_all(
                ['div', 'article', 'section', 'li'],
                class_=re.compile(r'(film|movie|event|session|show|card|item|screening)', re.I)
            )

            # Deduplicate by tracking seen titles and URLs
            seen = set()

            # Process direct event links
            for link in event_links:
                try:
                    screening = self._parse_event_link(link)
                    if screening and screening.title not in seen:
                        seen.add(screening.title)
                        screenings.append(screening)
                except Exception as e:
                    continue

            # Process container elements
            for container in event_containers:
                try:
                    screening = self._parse_event_container(container)
                    if screening and screening.title not in seen:
                        seen.add(screening.title)
                        screenings.append(screening)
                except Exception as e:
                    continue

            print(f"    Found {len(screenings)} screenings")

        except Exception as e:
            print(f"    Error scraping {self.theater_name}: {e}")

        return screenings

    def _parse_event_link(self, link) -> Screening:
        """Parse an event link element"""
        # Get the text from the link
        title_text = link.get_text(strip=True)

        if not title_text or len(title_text) < 2:
            return None

        # Skip navigation and other non-event links
        skip_keywords = ['BUY TICKETS', 'LEARN MORE', 'VIEW ALL', 'MENU', 'CALENDAR', 'ACCOUNT']
        if any(keyword in title_text.upper() for keyword in skip_keywords):
            return None

        # Get URL
        url = link.get('href', '')
        if url and not url.startswith('http'):
            url = self.base_url + url

        # Get the parent container for more context
        parent = link.find_parent(['div', 'article', 'section', 'li'])
        if parent:
            full_text = parent.get_text()
        else:
            full_text = title_text

        # Extract date/time information if available
        date_str = self._extract_date(full_text)

        # Determine special notes
        special_note = self._determine_special_note(full_text)

        # Only include if it has special characteristics or is clearly an event
        if not special_note and not self._is_special_event(title_text, full_text):
            return None

        return Screening(
            title=title_text,
            theater=self.theater_name,
            date=date_str,
            special_note=special_note,
            url=url,
            priority=1  # Alamo Drafthouse events are typically special
        )

    def _parse_event_container(self, container) -> Screening:
        """Parse an event container element"""
        # Extract title
        title_elem = container.find(
            ['h1', 'h2', 'h3', 'h4', 'a'],
            class_=re.compile(r'(title|name|film|movie|event)', re.I)
        )

        if not title_elem:
            # Try finding any prominent link or heading
            title_elem = container.find(['h2', 'h3', 'a'])

        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        if not title or len(title) < 2:
            return None

        # Get full text for analysis
        full_text = container.get_text()

        # Extract description
        desc_elem = container.find(
            ['p', 'div'],
            class_=re.compile(r'(description|synopsis|summary|excerpt)', re.I)
        )
        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ''

        # Extract date/time
        date_str = self._extract_date(full_text)

        # Determine special notes
        special_note = self._determine_special_note(full_text)

        # Only include special events
        if not special_note and not self._is_special_event(title, full_text):
            return None

        # Extract URL
        link = container.find('a', href=True)
        url = link['href'] if link else ''
        if url and not url.startswith('http'):
            url = self.base_url + url

        if not url:
            url = self.theater_url

        return Screening(
            title=title,
            theater=self.theater_name,
            date=date_str,
            description=description,
            special_note=special_note,
            url=url,
            priority=1
        )

    def _extract_date(self, text: str) -> str:
        """Extract date information from text"""
        # Look for common date patterns
        # e.g., "Nov 16", "November 16", "11/16", "Friday, November 16"

        # Try to find month names
        months = [
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'jan', 'feb', 'mar', 'apr', 'may', 'jun',
            'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
        ]

        text_lower = text.lower()

        # Look for "Month Day" pattern
        for month in months:
            # Pattern: Month DD or Month D
            pattern = rf'{month}\s+(\d{{1,2}})'
            match = re.search(pattern, text_lower)
            if match:
                # Extract and capitalize the month
                month_start = match.start()
                date_str = text[month_start:match.end()]
                return date_str.title()

        # Look for day of week
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days:
            if day in text_lower:
                # Find the context around the day
                day_idx = text_lower.index(day)
                # Extract a reasonable chunk
                date_chunk = text[day_idx:min(day_idx + 50, len(text))]
                # Look for month in this chunk
                for month in months:
                    if month in date_chunk.lower():
                        # Return up to the first few words
                        return date_chunk.split(',')[0].strip()

        return ''

    def _determine_special_note(self, text: str) -> str:
        """Determine what makes this screening special"""
        notes = []
        text_lower = text.lower()

        # Q&A and appearances
        if any(word in text_lower for word in ['q&a', 'q & a', 'q+a']):
            notes.append('Q&A')
        if 'director' in text_lower and any(word in text_lower for word in ['appearance', 'present', 'person', 'attendance', 'intro']):
            notes.append('Director Appearance')
        if 'cast' in text_lower and any(word in text_lower for word in ['appearance', 'present', 'person', 'attendance']):
            notes.append('Cast Appearance')

        # Special event types
        if 'quote-along' in text_lower or 'quote along' in text_lower:
            notes.append('Quote-Along')
        if 'sing-along' in text_lower or 'sing along' in text_lower:
            notes.append('Sing-Along')
        if 'master pancake' in text_lower or 'pancake' in text_lower:
            notes.append('Master Pancake')

        # Premieres and special screenings
        if 'premiere' in text_lower or 'opening night' in text_lower:
            notes.append('Premiere')
        if 'advance screening' in text_lower or 'early access' in text_lower:
            notes.append('Advance Screening')
        if 'special presentation' in text_lower or 'special screening' in text_lower or 'special event' in text_lower:
            notes.append('Special Event')

        # Formats and presentations
        if '35mm' in text_lower:
            notes.append('35mm')
        if '70mm' in text_lower:
            notes.append('70mm')
        if 'imax' in text_lower:
            notes.append('IMAX')
        if 'restoration' in text_lower or 'restored' in text_lower:
            notes.append('Restoration')
        if '4k' in text_lower:
            notes.append('4K')

        # Series and festivals
        if any(word in text_lower for word in ['retrospective', 'series', 'festival', 'marathon']):
            notes.append('Special Series')
        if 'double feature' in text_lower:
            notes.append('Double Feature')
        if 'midnight' in text_lower and 'show' in text_lower:
            notes.append('Midnight Show')

        # Themed events
        if 'terror tuesday' in text_lower:
            notes.append('Terror Tuesday')
        if 'weird wednesday' in text_lower:
            notes.append('Weird Wednesday')
        if 'video vortex' in text_lower:
            notes.append('Video Vortex')

        # Other special indicators
        if 'exclusive' in text_lower:
            notes.append('Exclusive')
        if 'limited' in text_lower and 'release' in text_lower:
            notes.append('Limited Release')

        return ' | '.join(notes)

    def _is_special_event(self, title: str, text: str) -> bool:
        """
        Determine if this is a special event worth highlighting.
        Alamo Drafthouse is known for special events, Q&As, and unique screenings.
        """
        text_lower = text.lower()
        title_lower = title.lower()

        # Check if it's a special event type in the title
        special_keywords = [
            'q&a', 'quote-along', 'sing-along', 'master pancake',
            'terror tuesday', 'weird wednesday', 'video vortex',
            'marathon', 'festival', 'retrospective', 'premiere',
            'special', 'exclusive', 'advance', 'restoration',
            '35mm', '70mm', 'imax', 'double feature'
        ]

        if any(keyword in title_lower for keyword in special_keywords):
            return True

        if any(keyword in text_lower for keyword in special_keywords):
            return True

        # Alamo Drafthouse's regular programming is often special/curated
        # but we want to focus on truly special events
        return False
