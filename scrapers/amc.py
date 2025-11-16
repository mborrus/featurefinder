"""
Scraper for AMC Theatres NYC locations using SerpAPI
"""
from typing import List, Dict, Any
from .base import BaseScraper, Screening
from datetime import datetime, timedelta
import re
import os


class AMCScraper(BaseScraper):
    """Scrapes AMC Lincoln Square and AMC 84th Street theaters using SerpAPI"""

    def __init__(self):
        super().__init__('AMC Theatres')
        self.base_url = 'https://www.amctheatres.com'
        self.theaters = {
            'AMC Lincoln Square 13': {'query': 'AMC Lincoln Square 13', 'location': 'New York, New York, United States'},
            'AMC 84th Street 6': {'query': 'AMC 84th Street 6', 'location': 'New York, New York, United States'}
        }
        # Get API key from environment
        from config import SERPAPI_KEY
        self.api_key = SERPAPI_KEY
        if not self.api_key:
            print("  ⚠️  SERPAPI_KEY not found in environment variables")

    def scrape(self) -> List[Screening]:
        """
        Scrape AMC theaters using SerpAPI's Google Showtimes API

        This makes one API call per theater to get current showtimes from Google.
        More reliable and faster than web scraping AMC's React site.
        """
        if not self.api_key:
            print("  ⚠️  Skipping AMC - SERPAPI_KEY not configured")
            return []

        screenings = []

        for theater_name, theater_info in self.theaters.items():
            print(f"  Checking {theater_name} via SerpAPI...")
            try:
                theater_screenings = self._fetch_theater_showtimes(theater_name, theater_info)
                screenings.extend(theater_screenings)

                if theater_screenings:
                    print(f"    Found {len(theater_screenings)} screenings")
                else:
                    print(f"    No special/premium screenings found")

            except Exception as e:
                print(f"    Error fetching {theater_name}: {e}")
                continue

        return screenings

    def _fetch_theater_showtimes(self, theater_name: str, theater_info: Dict[str, str]) -> List[Screening]:
        """Fetch showtimes from SerpAPI for a specific theater"""
        import requests

        # Build SerpAPI request using correct format
        # Format: https://serpapi.com/search.json?q=AMC+Theater+Name&location=City,+State,+Country
        params = {
            'q': theater_info['query'],  # Theater name WITHOUT "showtimes"
            'location': theater_info['location'],  # Full location format
            'hl': 'en',
            'gl': 'us',
            'api_key': self.api_key
        }

        try:
            response = requests.get('https://serpapi.com/search.json', params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Parse the showtimes from the response
            return self._parse_serpapi_response(data, theater_name)

        except requests.exceptions.RequestException as e:
            print(f"    API request failed: {e}")
            return []
        except Exception as e:
            print(f"    Error parsing response: {e}")
            return []

    def _parse_serpapi_response(self, data: Dict[str, Any], theater_name: str) -> List[Screening]:
        """
        Parse SerpAPI response and extract movie screenings

        Note: SerpAPI's 'showtimes' key appears primarily for movie-specific searches
        (e.g., "Wicked showtimes"), not theater-specific searches. Theater searches
        return knowledge graph data instead. This limits the usefulness for our use case.
        """
        screenings = []

        # Check if we have showtimes data (theater-specific searches often don't include this)
        showtimes = data.get('showtimes', [])
        if not showtimes:
            # Theater-specific searches return knowledge graph instead of showtimes carousel
            # Could potentially parse organic results or use AMC's site directly
            return screenings

        for showtime_day in showtimes:
            day = showtime_day.get('day', '')
            date = showtime_day.get('date', '')

            # Parse movies for this day
            movies = showtime_day.get('movies', [])
            for movie in movies:
                try:
                    screening = self._parse_movie_showtime(movie, theater_name, day, date)
                    if screening:
                        screenings.append(screening)
                except Exception as e:
                    continue

        return screenings

    def _parse_movie_showtime(self, movie: Dict[str, Any], theater_name: str,
                             day: str, date: str) -> Screening:
        """Parse individual movie showtime from SerpAPI data"""

        # Extract movie title
        title = movie.get('name', '').strip()
        if not title or len(title) < 2:
            return None

        # Get movie link (if available)
        url = movie.get('link', '')

        # Extract showing information (times and formats)
        showings = movie.get('showing', [])
        if not showings:
            return None

        # Analyze all showing types to find special formats
        formats = []
        times_list = []

        for showing in showings:
            show_type = showing.get('type', [])
            if isinstance(show_type, list):
                formats.extend(show_type)
            elif show_type:
                formats.append(show_type)

            # Collect times
            times = showing.get('time', [])
            if isinstance(times, list):
                times_list.extend(times[:3])  # Limit to first 3 times per type
            elif times:
                times_list.append(times)

        # Filter and format the format information
        format_info = self._extract_formats_from_list(formats)

        # Only include if it has special formats or looks like a special screening
        full_text = f"{title} {' '.join(formats)}"
        special_note = self._determine_special_note(full_text, format_info)

        # Skip regular showings - only include special/premium formats
        if not format_info and not special_note:
            return None

        # Build time string
        time_str = ', '.join(times_list[:5]) if times_list else ''  # Max 5 times

        # Format date string
        date_str = f"{day}, {date}" if day and date else day or date or ''

        # Build final special note
        notes = []
        if format_info:
            notes.append(format_info)
        if special_note:
            notes.append(special_note)
        final_note = ' | '.join(notes)

        # Calculate priority
        priority = self._calculate_priority(special_note, format_info)

        return Screening(
            title=title,
            theater=theater_name,
            date=date_str,
            time_slot=time_str,
            description='',
            special_note=final_note,
            url=url,
            priority=priority,
            tickets_on_sale='unknown',
            ticket_sale_date=''
        )

    def _extract_formats_from_list(self, formats: List[str]) -> str:
        """Extract and normalize format information from list of format strings"""
        normalized_formats = set()

        for fmt in formats:
            fmt_upper = fmt.upper()

            # Map various format names to standard ones
            if 'IMAX' in fmt_upper:
                normalized_formats.add('IMAX')
            if 'DOLBY' in fmt_upper and ('CINEMA' in fmt_upper or 'ATMOS' in fmt_upper):
                normalized_formats.add('Dolby Cinema')
            elif 'DOLBY' in fmt_upper:
                normalized_formats.add('Dolby')
            if '70MM' in fmt_upper or '70 MM' in fmt_upper:
                normalized_formats.add('70mm')
            if '35MM' in fmt_upper or '35 MM' in fmt_upper:
                normalized_formats.add('35mm')
            if 'PRIME' in fmt_upper:
                normalized_formats.add('AMC Prime')
            if '3D' in fmt_upper:
                normalized_formats.add('3D')

        return ', '.join(sorted(normalized_formats))


    def _determine_special_note(self, text: str, format_info: str) -> str:
        """Determine if this is a special screening (enhanced detection)"""
        text_lower = text.lower()
        notes = []

        # Check for special events (enhanced)
        if any(keyword in text_lower for keyword in ['q&a', 'q & a', 'q and a']):
            notes.append('Q&A')

        # Director and filmmaker appearances (enhanced)
        if any(keyword in text_lower for keyword in ['with director', 'director in person', 'director present']):
            notes.append('Director Appearance')
        elif 'director' in text_lower and ('appearance' in text_lower or 'intro' in text_lower or 'in person' in text_lower):
            notes.append('Director Appearance')

        if any(keyword in text_lower for keyword in ['with filmmaker', 'filmmaker in person', 'filmmaker present']):
            notes.append('Filmmaker Appearance')
        elif 'filmmaker' in text_lower and ('appearance' in text_lower or 'in person' in text_lower):
            notes.append('Filmmaker Appearance')

        # Premieres and opening nights (enhanced)
        if 'opening night' in text_lower:
            notes.append('Opening Night')
        elif 'premiere' in text_lower:
            notes.append('Premiere')

        # Preview screenings (enhanced)
        if any(keyword in text_lower for keyword in ['sneak preview', 'sneak peek']):
            notes.append('Sneak Preview')
        elif 'advance screening' in text_lower or 'early access' in text_lower:
            notes.append('Advance Screening')

        # Special events
        if 'special presentation' in text_lower or 'special screening' in text_lower:
            notes.append('Special Presentation')
        if 'fan event' in text_lower or 'fan screening' in text_lower:
            notes.append('Fan Event')
        if 'marathon' in text_lower or 'double feature' in text_lower or 'triple feature' in text_lower:
            notes.append('Marathon')

        # Anniversary screenings (new)
        if any(keyword in text_lower for keyword in ['anniversary', 'th anniversary']):
            notes.append('Anniversary')

        return ' | '.join(notes)


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
