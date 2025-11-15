"""
Scraper for r/NYCmovies subreddit
"""
from typing import List
from .base import BaseScraper, Screening
import praw
from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
from datetime import datetime, timedelta


class RedditScraper(BaseScraper):
    """Scrapes r/NYCmovies for special screening announcements"""

    def __init__(self):
        super().__init__('r/NYCmovies')
        self.subreddit_name = 'NYCmovies'

    def scrape(self) -> List[Screening]:
        """Scrape recent posts from r/NYCmovies"""
        screenings = []

        if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
            print("Reddit credentials not configured, skipping Reddit scraper")
            return screenings

        try:
            reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent=REDDIT_USER_AGENT
            )

            subreddit = reddit.subreddit(self.subreddit_name)

            # Get posts from the last 7 days
            week_ago = datetime.now() - timedelta(days=7)

            for submission in subreddit.new(limit=50):
                try:
                    # Check if post is recent
                    post_date = datetime.fromtimestamp(submission.created_utc)
                    if post_date < week_ago:
                        continue

                    # Check if it's about a special screening
                    if self._is_special_screening(submission.title + ' ' + submission.selftext):
                        screening = self._parse_submission(submission)
                        if screening:
                            screenings.append(screening)

                except Exception as e:
                    print(f"Error parsing Reddit post: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping Reddit: {e}")

        return screenings

    def _parse_submission(self, submission) -> Screening:
        """Parse a Reddit submission into a Screening"""
        title = submission.title
        description = submission.selftext[:300] if submission.selftext else ''

        # Try to extract theater from title or text
        theater = self._extract_theater(title + ' ' + description)

        # Try to extract date
        date_str = self._extract_date(title + ' ' + description)

        # Extract special notes
        special_note = self._extract_special_notes(title + ' ' + description)

        return Screening(
            title=self._clean_title(title),
            theater=theater,
            date=date_str,
            description=description,
            special_note=special_note,
            url=f'https://reddit.com{submission.permalink}',
            priority=3
        )

    def _clean_title(self, title: str) -> str:
        """Remove common Reddit prefixes and clean title"""
        # Remove [brackets] and other common Reddit formatting
        import re
        title = re.sub(r'\[.*?\]', '', title)
        title = re.sub(r'\(.*?theater.*?\)', '', title, flags=re.I)
        return title.strip()

    def _extract_theater(self, text: str) -> str:
        """Try to extract theater name from text"""
        theaters = [
            'AMC Lincoln Square', 'AMC 84th', 'Paris Theater', 'Angelika',
            'Film Forum', 'IFC Center', 'Metrograph', 'Alamo Drafthouse',
            'Anthology', 'BAM', 'Quad', 'Nitehawk'
        ]

        text_lower = text.lower()
        for theater in theaters:
            if theater.lower() in text_lower:
                return theater

        return 'Check Post'

    def _extract_date(self, text: str) -> str:
        """Try to extract date from text"""
        import re

        # Look for common date patterns
        patterns = [
            r'\d{1,2}/\d{1,2}',  # MM/DD
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2}',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(0)

        return ''

    def _extract_special_notes(self, text: str) -> str:
        """Extract special screening notes"""
        notes = []
        text_lower = text.lower()

        if any(word in text_lower for word in ['q&a', 'q & a']):
            notes.append('Q&A')
        if 'director' in text_lower and any(word in text_lower for word in ['appearance', 'present']):
            notes.append('Director Appearance')
        if 'imax' in text_lower:
            notes.append('IMAX')
        if '70mm' in text_lower:
            notes.append('70mm')
        if 'premiere' in text_lower:
            notes.append('Premiere')
        if 'advance screening' in text_lower or 'early screening' in text_lower:
            notes.append('Advance Screening')
        if 'free' in text_lower and 'ticket' in text_lower:
            notes.append('Free Tickets')

        return ' | '.join(notes) if notes else 'Community Post'

    def _is_special_screening(self, text: str) -> bool:
        """Check if post is about a special screening"""
        text_lower = text.lower()

        # Keywords that indicate special screening
        special_keywords = [
            'screening', 'q&a', 'premiere', 'director', 'imax',
            '70mm', 'advance', 'tickets available', 'special event',
            'festival', 'opening night', 'limited', 'exclusive'
        ]

        # Check if it's a question or general discussion (exclude these)
        if any(text_lower.startswith(q) for q in ['what', 'where', 'how', 'why', 'does anyone']):
            return False

        return any(keyword in text_lower for keyword in special_keywords)
