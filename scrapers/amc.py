"""
Scraper for AMC Theatres NYC locations
"""
from typing import List
from .base import BaseScraper, Screening
from datetime import datetime, timedelta
import re


class AMCScraper(BaseScraper):
    """Scrapes AMC Lincoln Square and AMC 84th Street theaters"""

    def __init__(self):
        super().__init__('AMC Theatres')
        self.base_url = 'https://www.amctheatres.com'
        self.theaters = {
            'AMC Lincoln Square': 'amc-lincoln-square-13',
            'AMC 84th Street': 'amc-84th-street-6'
        }

    def scrape(self) -> List[Screening]:
        """Scrape AMC theaters for the next month"""
        screenings = []

        # Get date range: today to 1 month out
        today = datetime.now()
        end_date = today + timedelta(days=30)

        # Check every 3 days to catch upcoming releases and ticket sale dates
        # This gives us ~10 snapshots across the month to catch new releases
        dates_to_check = []
        current_date = today
        while current_date <= end_date:
            dates_to_check.append(current_date)
            current_date += timedelta(days=3)  # Check every 3 days

        for theater_name, theater_slug in self.theaters.items():
            print(f"  Checking {theater_name}...")
            for check_date in dates_to_check:
                try:
                    date_str = check_date.strftime('%Y-%m-%d')
                    url = f'{self.base_url}/movie-theatres/new-york-city/{theater_slug}/showtimes?date={date_str}'

                    # AMC is a JavaScript-heavy site, use Playwright
                    soup = self.fetch_page_js(
                        url,
                        wait_selector='.ShowtimesByTheatre, .Showtime, [class*="showtime"], [class*="movie"]',
                        timeout=40000
                    )

                    if not soup:
                        print(f"    Failed to load {theater_name} for {date_str}")
                        continue

                    theater_screenings = self._parse_showtimes(soup, theater_name, check_date)
                    screenings.extend(theater_screenings)

                    if theater_screenings:
                        print(f"    Found {len(theater_screenings)} screenings for {date_str}")

                except Exception as e:
                    print(f"    Error scraping {theater_name} for {check_date.strftime('%Y-%m-%d')}: {e}")
                    continue

        return screenings

    def _parse_showtimes(self, soup, theater_name: str, date: datetime) -> List[Screening]:
        """Parse showtime listings from AMC page"""
        screenings = []

        # AMC typically groups by movie, then lists showtimes
        # Look for movie containers
        movie_elements = soup.find_all(['div', 'article', 'section'],
                                      class_=re.compile(r'movie|film|showtime', re.I))

        for element in movie_elements:
            try:
                screening = self._parse_movie(element, theater_name, date)
                if screening:
                    screenings.append(screening)
            except Exception as e:
                continue

        return screenings

    def _parse_movie(self, element, theater_name: str, date: datetime) -> Screening:
        """Parse individual movie listing"""
        # Extract title
        title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'a'],
                                  class_=re.compile(r'title|name|movie', re.I))

        if not title_elem:
            # Sometimes the title is just in a link
            title_elem = element.find('a', href=re.compile(r'/movies/', re.I))

        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)
        if not title or len(title) < 2:
            return None

        # Skip non-movie content
        skip_keywords = ['MEMBERSHIP', 'GIFT', 'FOOD', 'DRINK', 'CONCESSION']
        if any(keyword in title.upper() for keyword in skip_keywords):
            return None

        # Get full text for analysis
        full_text = element.get_text()

        # Extract format information (IMAX, Dolby, etc.)
        format_info = self._extract_format(full_text)

        # Determine if this is a special screening
        special_note = self._determine_special_note(full_text, format_info)

        # Only include if it's special or a major format
        if not special_note and not format_info:
            # Skip regular showings unless they look like new releases
            if not self._is_likely_new_release(title, full_text):
                return None

        # Extract description if available
        desc_elem = element.find(['p', 'div'], class_=re.compile(r'description|synopsis', re.I))
        description = desc_elem.get_text(strip=True)[:200] if desc_elem else ''

        # Format date string
        date_str = date.strftime('%A, %B %d')

        # Extract showtimes
        time_elements = element.find_all(['button', 'a', 'span'],
                                        class_=re.compile(r'time|showtime', re.I))
        times = [t.get_text(strip=True) for t in time_elements[:3]]  # Just show first few times
        time_str = ', '.join(times) if times else ''

        # Extract URL
        link = element.find('a', href=True)
        url = link['href'] if link else ''
        if url and not url.startswith('http'):
            url = self.base_url + url

        # Build special note with format info
        notes = []
        if format_info:
            notes.append(format_info)
        if special_note:
            notes.append(special_note)

        final_note = ' | '.join(notes) if notes else ''

        # Extract ticket availability
        ticket_status, ticket_sale_date = self.extract_ticket_availability(full_text)

        # Determine priority based on what we found
        priority = self._calculate_priority(special_note, format_info)

        return Screening(
            title=title,
            theater=theater_name,
            date=date_str,
            time_slot=time_str,
            description=description,
            special_note=final_note,
            url=url,
            priority=priority,
            tickets_on_sale=ticket_status,
            ticket_sale_date=ticket_sale_date
        )

    def _extract_format(self, text: str) -> str:
        """Extract special format information (IMAX, Dolby, etc.)"""
        text_upper = text.upper()
        formats = []

        if 'IMAX' in text_upper:
            formats.append('IMAX')
        if 'DOLBY CINEMA' in text_upper or 'DOLBY ATMOS' in text_upper:
            formats.append('Dolby Cinema')
        if '70MM' in text_upper or '70 MM' in text_upper:
            formats.append('70mm')
        if '35MM' in text_upper or '35 MM' in text_upper:
            formats.append('35mm')
        if 'PRIME' in text_upper:
            formats.append('AMC Prime')

        return ', '.join(formats)

    def _determine_special_note(self, text: str, format_info: str) -> str:
        """Determine if this is a special screening"""
        text_lower = text.lower()
        notes = []

        # Check for special events
        if any(keyword in text_lower for keyword in ['q&a', 'q & a']):
            notes.append('Q&A')
        if 'director' in text_lower and ('appearance' in text_lower or 'intro' in text_lower):
            notes.append('Director Appearance')
        if 'premiere' in text_lower or 'opening night' in text_lower:
            notes.append('Premiere')
        if 'advance screening' in text_lower or 'early access' in text_lower:
            notes.append('Advance Screening')
        if 'special presentation' in text_lower or 'special screening' in text_lower:
            notes.append('Special Presentation')
        if 'fan event' in text_lower or 'fan screening' in text_lower:
            notes.append('Fan Event')
        if 'marathon' in text_lower or 'double feature' in text_lower:
            notes.append('Marathon')

        return ' | '.join(notes)

    def _is_likely_new_release(self, title: str, text: str) -> bool:
        """
        Determine if this is likely a major new release worth highlighting.
        This is a heuristic - we look for indicators of new/upcoming films.
        """
        text_lower = text.lower()

        # Keywords that suggest new releases
        new_release_keywords = [
            'opening', 'now playing', 'coming soon', 'advance tickets',
            'tickets on sale', 'new release', 'exclusive'
        ]

        if any(keyword in text_lower for keyword in new_release_keywords):
            return True

        # If it has special format (IMAX, Dolby), it's likely important
        if self._extract_format(text):
            return True

        return False

    def _calculate_priority(self, special_note: str, format_info: str) -> int:
        """
        Calculate priority for the screening.
        Lower number = higher priority
        """
        # Q&A or director appearances are highest priority
        if special_note and any(x in special_note for x in ['Q&A', 'Director', 'Premiere']):
            return 1

        # Special screenings are high priority
        if special_note and any(x in special_note for x in ['Advance', 'Fan Event', 'Marathon']):
            return 1

        # Premium formats (IMAX, 70mm, Dolby) are medium-high priority
        if format_info and any(x in format_info for x in ['IMAX', '70mm', 'Dolby']):
            return 2

        # Other formats or new releases
        return 3
