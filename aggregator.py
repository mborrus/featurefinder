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
    FilmAtLincolnCenterScraper
)
from datetime import datetime


class ScreeningAggregator:
    """Aggregates screenings from multiple sources"""

    def __init__(self):
        self.scrapers = [
            FilmAtLincolnCenterScraper(),  # Priority 1 - premier NYC arthouse venue
            NewYorkerScraper(),            # Highest priority - best curation
            ScreenslateScraper(),
            MetrographScraper(),
            FilmForumScraper(),
            AngelikaScraper(),             # Priority arthouse theater
            IFCCenterScraper(),
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
        # Always include if it has special notes
        if screening.special_note:
            return True

        # Include if from repertory/art house theaters
        repertory_theaters = [
            'film at lincoln center', 'lincoln center', 'film forum',
            'ifc center', 'metrograph', 'anthology', 'paris theater',
            'angelika', 'quad'
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

    def sort_screenings(self, screenings: List[Screening]) -> List[Screening]:
        """Sort screenings by priority and date"""
        return sorted(screenings, key=lambda s: (s.priority, s.theater, s.title))

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
