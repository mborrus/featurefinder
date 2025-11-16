"""
Aggregator to collect and filter screenings from all sources
"""
from typing import List, Tuple
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
    MoMAScraper,
    AlamoDrafthouseScraper
)
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class ScreeningAggregator:
    """Aggregates screenings from multiple sources"""

    def __init__(self):
        self.scrapers = [
            FilmAtLincolnCenterScraper(),  # Priority 1 - premier NYC arthouse venue
            AMCScraper(),                  # Priority 1 - AMC Lincoln Square & 84th St
            MoMAScraper(),                 # Priority 1 - excellent repertory & filmmaker Q&As
            AlamoDrafthouseScraper(),      # Priority 1 - Alamo Drafthouse Lower Manhattan
            NewYorkerScraper(),            # Highest priority - best curation
            ScreenslateScraper(),
            MetrographScraper(),
            FilmForumScraper(),
            AngelikaScraper(),             # Priority arthouse theater
            IFCCenterScraper(),
            TimeOutScraper(),
            RedditScraper()
        ]

    def _scrape_single_source(self, scraper) -> Tuple[str, List[Screening], str]:
        """
        Helper method to scrape a single source with error handling.
        Returns: (scraper_name, screenings_list, error_message)
        """
        try:
            print(f"Scraping {scraper.name}...")
            start_time = time.time()
            screenings = scraper.scrape()
            elapsed = time.time() - start_time
            print(f"  ✓ Found {len(screenings)} screenings from {scraper.name} ({elapsed:.1f}s)")
            return scraper.name, screenings, None
        except Exception as e:
            print(f"  ✗ Error scraping {scraper.name}: {e}")
            return scraper.name, [], str(e)

    def collect_all_screenings(self) -> List[Screening]:
        """Collect screenings from all sources in parallel"""
        all_screenings = []
        overall_start_time = time.time()

        print(f"Starting parallel scraping of {len(self.scrapers)} sources...")

        # Use ThreadPoolExecutor to scrape all sources concurrently
        # Max workers = number of scrapers to run all in parallel
        with ThreadPoolExecutor(max_workers=len(self.scrapers)) as executor:
            # Submit all scraping tasks
            future_to_scraper = {
                executor.submit(self._scrape_single_source, scraper): scraper
                for scraper in self.scrapers
            }

            # Collect results as they complete
            for future in as_completed(future_to_scraper):
                scraper_name, screenings, error = future.result()
                if not error:
                    all_screenings.extend(screenings)

        overall_elapsed = time.time() - overall_start_time
        print(f"\n{'='*60}")
        print(f"Total screenings collected: {len(all_screenings)} in {overall_elapsed:.1f}s")
        print(f"{'='*60}")
        return all_screenings

    def filter_and_deduplicate(self, screenings: List[Screening]) -> List[Screening]:
        """Filter and deduplicate screenings"""
        # Remove duplicates based on title, theater, and date
        # This ensures same film on different dates are kept separate
        seen = set()
        unique_screenings = []
        duplicates_removed = 0

        for screening in screenings:
            key = (screening.title.lower().strip(), screening.theater.lower().strip(), screening.date.lower().strip())
            if key not in seen:
                seen.add(key)
                unique_screenings.append(screening)
            else:
                duplicates_removed += 1
                logger.debug(f"[DEDUPLICATED] '{screening.title}' at {screening.theater}")

        print(f"Unique screenings after deduplication: {len(unique_screenings)} (removed {duplicates_removed} duplicates)")

        # Filter out non-special screenings
        logger.info("\n=== FILTERING SCREENINGS ===")
        filtered_screenings = []
        filtered_out = []

        for s in unique_screenings:
            result, reason = self._is_worth_including(s)
            if result:
                filtered_screenings.append(s)
            else:
                filtered_out.append((s, reason))
                logger.info(f"[FILTERED OUT] '{s.title}' at {s.theater} - Reason: {reason}")

        print(f"Screenings after filtering: {len(filtered_screenings)} (filtered out {len(filtered_out)})")
        logger.info(f"\n=== FILTERING COMPLETE: {len(filtered_screenings)} included, {len(filtered_out)} excluded ===\n")

        return filtered_screenings

    def _is_worth_including(self, screening: Screening) -> tuple[bool, str]:
        """
        Determine if a screening is worth including in the email.
        Returns (bool, str) - whether to include and the reason.
        """
        reasons_failed = []

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
                    return (True, f"Tickets on sale within 14 days ({screening.ticket_sale_date})")
                else:
                    reasons_failed.append(f"ticket sale date too far: {screening.ticket_sale_date}")
            else:
                reasons_failed.append(f"couldn't parse ticket date: {screening.ticket_sale_date}")
        else:
            reasons_failed.append("no ticket sale date")

        # Always include if it has special notes
        if screening.special_note:
            return (True, f"Has special note: {screening.special_note}")
        else:
            reasons_failed.append("no special notes")

        # Include if from repertory/art house theaters
        repertory_theaters = [
            'film at lincoln center', 'lincoln center', 'film forum',
            'ifc center', 'metrograph', 'anthology', 'paris theater',
            'angelika', 'quad', 'amc', 'moma', 'alamo drafthouse'
        ]
        matching_theater = next((t for t in repertory_theaters if t in screening.theater.lower()), None)
        if matching_theater:
            return (True, f"From repertory/art house theater: {matching_theater}")
        else:
            reasons_failed.append(f"not from repertory theater (theater: {screening.theater})")

        # Include if title/description suggests it's special
        text = (screening.title + ' ' + screening.description).lower()
        special_keywords = [
            'q&a', 'director', 'premiere', 'festival', 'imax',
            '70mm', '35mm', 'restoration', 'retrospective',
            'exclusive', 'limited', 'advance', 'special'
        ]
        matching_keywords = [kw for kw in special_keywords if kw in text]
        if matching_keywords:
            return (True, f"Contains special keywords: {', '.join(matching_keywords)}")
        else:
            reasons_failed.append("no special keywords in title/description")

        # If we got here, screening doesn't meet any criteria
        failure_reason = "; ".join(reasons_failed)
        return (False, failure_reason)
    
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
        1. Ticket availability status (on sale now > upcoming sale > not yet/unknown)
        2. Screenings with upcoming ticket sale dates (sooner = higher priority)
        3. Priority theaters
        4. Theater name, then title
        """
        def sort_key(s):
            # Primary: ticket availability status
            availability_priority = 0
            if hasattr(s, 'tickets_on_sale'):
                if s.tickets_on_sale == 'on_sale':
                    availability_priority = 0  # Highest - tickets available now
                elif s.tickets_on_sale == 'not_yet':
                    availability_priority = 1  # Medium - tickets coming soon
                elif s.tickets_on_sale == 'sold_out':
                    availability_priority = 3  # Lower - sold out
                else:  # 'unknown'
                    availability_priority = 2  # Between not_yet and sold_out
            else:
                availability_priority = 2  # No info - medium-low priority

            # Secondary: ticket sale date (sooner = higher priority, only for not_yet status)
            ticket_date = self._parse_ticket_date(s.ticket_sale_date) if s.ticket_sale_date else None
            if ticket_date and availability_priority == 1:  # Only for 'not_yet' status
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

            # Tertiary: theater priority
            # Quaternary: theater name, title
            return (availability_priority, ticket_priority, s.priority, s.theater, s.title)

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
