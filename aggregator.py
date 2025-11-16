"""
Aggregator to collect and filter screenings from all sources
"""
from typing import List
from scrapers.base import Screening
from scrapers import (
    ScreenslateScraper,
    RedditScraper,
    TimeOutScraper,
    FilmForumScraper,
    IFCCenterScraper,
    MetrographScraper,
    NewYorkerScraper,
    AngelikaScraper,
    FilmAtLincolnCenterScraper,
    AMCScraper,
    RoxyCinemaScraper
)
from datetime import datetime, timedelta
import re


class ScreeningAggregator:
    """Aggregates screenings from multiple sources"""

    def __init__(self):
        self.scrapers = [
            FilmAtLincolnCenterScraper(),  # Priority 1 - premier NYC arthouse venue
            AMCScraper(),                  # Priority 1 - AMC Lincoln Square & 84th St
            NewYorkerScraper(),            # Highest priority - best curation
            ScreenslateScraper(),
            MetrographScraper(),
            FilmForumScraper(),
            AngelikaScraper(),             # Priority arthouse theater
            IFCCenterScraper(),
            RoxyCinemaScraper(),           # Priority 2 - Tribeca arthouse theater
            TimeOutScraper(),
            RedditScraper()
        ]

    def collect_all_screenings(self) -> List[Screening]:
        """Collect screenings from all sources"""
        all_screenings = []

        for scraper in self.scrapers:
            try:
                print(f"Scraping {scraper.name}...")
                screenings = scraper.scrape()
                print(f"  Found {len(screenings)} screenings from {scraper.name}")
                all_screenings.extend(screenings)
            except Exception as e:
                print(f"  Error scraping {scraper.name}: {e}")
                continue

        print(f"\nTotal screenings collected: {len(all_screenings)}")
        return all_screenings

    def filter_and_deduplicate(self, screenings: List[Screening]) -> List[Screening]:
        """Filter and deduplicate screenings"""
        # Remove duplicates based on title and theater
        seen = set()
        unique_screenings = []

        for screening in screenings:
            key = (screening.title.lower().strip(), screening.theater.lower().strip())
            if key not in seen:
                seen.add(key)
                unique_screenings.append(screening)

        print(f"Unique screenings after deduplication: {len(unique_screenings)}")

        # Filter out non-special screenings
        filtered_screenings = [s for s in unique_screenings if self._is_worth_including(s)]
        print(f"Screenings after filtering: {len(filtered_screenings)}")

        return filtered_screenings

    def _is_worth_including(self, screening: Screening) -> bool:
        """Determine if a screening is worth including in the email"""
        # PRIORITIZE: screenings with upcoming ticket sale dates
        if screening.ticket_sale_date:
            # Check if ticket sale date is in the near future (next 2 weeks)
            ticket_date = self._parse_ticket_date(screening.ticket_sale_date)
            if ticket_date:
                # Normalize current date to midnight for consistent comparison
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                days_until_sale = (ticket_date - today).days
                # Prioritize if tickets go on sale within the next 14 days
                if 0 <= days_until_sale <= 14:
                    return True
        
        # Always include if it has special notes
        if screening.special_note:
            return True

        # Include if from repertory/art house theaters
        repertory_theaters = [
            'film at lincoln center', 'lincoln center', 'film forum',
            'ifc center', 'metrograph', 'anthology', 'paris theater',
            'angelika', 'quad', 'amc', 'roxy'
        ]
        if any(theater in screening.theater.lower() for theater in repertory_theaters):
            return True

        # Include if title/description suggests it's special
        text = (screening.title + ' ' + screening.description).lower()
        special_keywords = [
            'q&a', 'director', 'premiere', 'festival', 'imax',
            '70mm', '35mm', 'restoration', 'retrospective',
            'exclusive', 'limited', 'advance', 'special'
        ]
        if any(keyword in text for keyword in special_keywords):
            return True

        return False
    
    def _parse_ticket_date(self, date_str: str) -> datetime:
        """
        Parse ticket sale date string to datetime.
        Handles formats like "Nov 15", "November 15", "Tuesday", "this Friday", etc.
        Returns None if parsing fails.
        """
        if not date_str:
            return None
        
        date_str = date_str.strip().lower()
        now = datetime.now()
        
        # Handle day names (Monday, Tuesday, etc.)
        day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for i, day_name in enumerate(day_names):
            if day_name in date_str:
                # Calculate next occurrence of this day
                days_ahead = i - now.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                target_date = now + timedelta(days=days_ahead)
                return target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Handle relative dates
        if 'today' in date_str:
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        if 'tomorrow' in date_str:
            return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Handle "this week" or "next week"
        if 'this week' in date_str or 'next week' in date_str:
            days_to_add = 7 if 'next week' in date_str else 0
            return (now + timedelta(days=days_to_add)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Try to parse month and day (e.g., "Nov 15", "November 15")
        month_day_match = re.match(r'([a-z]+)\s+(\d{1,2})', date_str)
        if month_day_match:
            month_str, day_str = month_day_match.groups()
            day = int(day_str)
            
            # Convert month name to number
            month_names = {
                'jan': 1, 'january': 1,
                'feb': 2, 'february': 2,
                'mar': 3, 'march': 3,
                'apr': 4, 'april': 4,
                'may': 5,
                'jun': 6, 'june': 6,
                'jul': 7, 'july': 7,
                'aug': 8, 'august': 8,
                'sep': 9, 'september': 9,
                'oct': 10, 'october': 10,
                'nov': 11, 'november': 11,
                'dec': 12, 'december': 12
            }
            month = month_names.get(month_str[:3])  # First 3 chars of month
            if month:
                # Determine year (assume current year, or next year if month has passed)
                year = now.year
                if month < now.month or (month == now.month and day < now.day):
                    year += 1
                
                try:
                    return datetime(year, month, day, 0, 0, 0)
                except ValueError:
                    pass
        
        return None

    def sort_screenings(self, screenings: List[Screening]) -> List[Screening]:
        """
        Sort screenings prioritizing:
        1. Screenings with upcoming ticket sale dates (sooner = higher priority)
        2. Priority theaters
        3. Theater name, then title
        """
        def sort_key(s):
            # Primary: ticket sale date (sooner = lower number = higher priority)
            ticket_date = self._parse_ticket_date(s.ticket_sale_date) if s.ticket_sale_date else None
            if ticket_date:
                # Normalize current date to midnight for consistent comparison
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                days_until_sale = (ticket_date - today).days
                # Prioritize tickets going on sale within 14 days
                if 0 <= days_until_sale <= 14:
                    ticket_priority = days_until_sale  # 0 = today (highest), 14 = 2 weeks out
                else:
                    ticket_priority = 999  # Far future, low priority
            else:
                ticket_priority = 1000  # No ticket date, lowest priority
            
            # Secondary: theater priority
            # Tertiary: theater name, title
            return (ticket_priority, s.priority, s.theater, s.title)
        
        return sorted(screenings, key=sort_key)

    def group_by_theater(self, screenings: List[Screening]) -> dict:
        """Group screenings by theater"""
        grouped = {}
        for screening in screenings:
            theater = screening.theater
            if theater not in grouped:
                grouped[theater] = []
            grouped[theater].append(screening)

        # Sort theaters by priority
        return dict(sorted(grouped.items(), key=lambda x: min(s.priority for s in x[1])))
