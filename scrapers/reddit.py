"""
Scraper for r/NYCmovies subreddit using web scraping
"""
from typing import List, Dict, Any
from .base import BaseScraper, Screening
import requests
import re
import time
import json
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


class RedditScraper(BaseScraper):
    """Scrapes r/NYCmovies for special screening announcements"""

    def __init__(self):
        super().__init__('r/NYCmovies')
        self.subreddit_name = 'NYCmovies'
        self.base_url = f'https://www.reddit.com/r/{self.subreddit_name}'
        # Use realistic browser headers to avoid 403 errors
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def scrape(self) -> List[Screening]:
        """Scrape recent posts from r/NYCmovies using web scraping"""
        screenings = []

        try:
            # 1. Get the hot posts (includes pinned weekly summary)
            print("Fetching hot posts (includes pinned weekly summaries)...")
            hot_screenings = self._scrape_hot_posts()
            screenings.extend(hot_screenings)
            time.sleep(1)  # Brief delay between requests

            # 2. Get posts with "Screening Info" flair
            print("Fetching posts with 'Screening Info' flair...")
            flair_screenings = self._scrape_by_flair('Screening Info')
            screenings.extend(flair_screenings)
            time.sleep(1)  # Brief delay between requests

            # 3. Get recent new posts
            print("Fetching recent new posts...")
            new_screenings = self._scrape_new_posts()
            screenings.extend(new_screenings)

            # Remove duplicates based on URL
            seen_urls = set()
            unique_screenings = []
            for screening in screenings:
                if screening.url not in seen_urls:
                    seen_urls.add(screening.url)
                    unique_screenings.append(screening)

            print(f"Found {len(unique_screenings)} unique screening posts from Reddit")
            return unique_screenings

        except Exception as e:
            print(f"Error scraping Reddit: {e}")
            return screenings

    def _fetch_json(self, url: str) -> Dict[str, Any]:
        """Fetch JSON data from a Reddit URL using Playwright to bypass blocking"""
        json_url = url if url.endswith('.json') else f"{url}.json"

        try:
            with sync_playwright() as p:
                # Launch browser in headless mode
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
                )
                page = context.new_page()

                # Navigate to the JSON endpoint
                try:
                    response = page.goto(json_url, wait_until='networkidle', timeout=30000)

                    if response.status == 403:
                        print(f"Access forbidden (403). Reddit may be blocking access.")
                        browser.close()
                        return {'data': {'children': []}}

                    # Get the page content
                    content = page.content()

                    # Extract JSON from the page
                    # Reddit serves JSON in a <pre> tag when accessed via browser
                    if '<pre>' in content:
                        # Extract JSON from <pre> tag
                        start = content.find('<pre>') + 5
                        end = content.find('</pre>')
                        json_text = content[start:end]
                    else:
                        json_text = content

                    browser.close()
                    return json.loads(json_text)

                except PlaywrightTimeout:
                    print(f"Timeout loading {json_url}")
                    browser.close()
                    return {'data': {'children': []}}

        except Exception as e:
            print(f"Error fetching JSON with Playwright: {e}")
            # Fallback to simple requests as last resort
            try:
                response = requests.get(json_url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    return response.json()
            except:
                pass

            return {'data': {'children': []}}

    def _scrape_hot_posts(self) -> List[Screening]:
        """Scrape hot posts (includes pinned weekly summary)"""
        screenings = []
        try:
            data = self._fetch_json(f"{self.base_url}/hot")
            posts = data['data']['children']

            for post_data in posts[:20]:  # Check first 20 hot posts
                post = post_data['data']

                # Prioritize stickied/pinned posts (weekly summary)
                is_pinned = post.get('stickied', False) or post.get('pinned', False)

                if is_pinned:
                    print(f"Found pinned post: {post['title']}")

                screening = self._parse_post(post, is_pinned=is_pinned)
                if screening:
                    screenings.append(screening)

        except Exception as e:
            print(f"Error scraping hot posts: {e}")

        return screenings

    def _scrape_by_flair(self, flair_name: str) -> List[Screening]:
        """Scrape posts filtered by flair"""
        screenings = []
        try:
            # Use search with flair filter
            search_url = f"{self.base_url}/search"
            params = {
                'q': f'flair:"{flair_name}"',
                'restrict_sr': 'on',
                'sort': 'new',
                'limit': 25
            }

            # Construct URL with parameters
            url = f"{search_url}?q=flair%3A%22{flair_name.replace(' ', '%20')}%22&restrict_sr=on&sort=new&limit=25"
            data = self._fetch_json(url)

            posts = data['data']['children']

            for post_data in posts:
                post = post_data['data']
                screening = self._parse_post(post, has_screening_flair=True)
                if screening:
                    screenings.append(screening)

        except Exception as e:
            print(f"Error scraping posts by flair '{flair_name}': {e}")

        return screenings

    def _scrape_new_posts(self) -> List[Screening]:
        """Scrape recent new posts"""
        screenings = []
        try:
            data = self._fetch_json(f"{self.base_url}/new")
            posts = data['data']['children']

            week_ago = datetime.now() - timedelta(days=7)

            for post_data in posts[:30]:  # Check first 30 new posts
                post = post_data['data']

                # Check if post is recent
                post_date = datetime.fromtimestamp(post['created_utc'])
                if post_date < week_ago:
                    continue

                screening = self._parse_post(post)
                if screening:
                    screenings.append(screening)

        except Exception as e:
            print(f"Error scraping new posts: {e}")

        return screenings

    def _parse_post(self, post: Dict[str, Any], is_pinned: bool = False,
                    has_screening_flair: bool = False) -> Screening:
        """Parse a Reddit post JSON object into a Screening"""
        try:
            title = post['title']
            selftext = post.get('selftext', '')
            permalink = post['permalink']

            # Combined text for analysis
            full_text = f"{title} {selftext}"

            # Check if it's about a special screening (unless pinned or has screening flair)
            if not is_pinned and not has_screening_flair:
                if not self._is_special_screening(full_text):
                    return None

            # Extract information
            description = selftext[:500] if selftext else ''
            theater = self._extract_theater(full_text)
            date_str = self._extract_date(full_text)
            special_note = self._extract_special_notes(full_text)

            # Extract ticket availability
            ticket_status, ticket_sale_date = self.extract_ticket_availability(full_text)

            # Higher priority for pinned posts
            priority = 2 if is_pinned else 3

            return Screening(
                title=self._clean_title(title),
                theater=theater,
                date=date_str,
                description=description,
                special_note=special_note,
                url=f'https://reddit.com{permalink}',
                priority=priority,
                tickets_on_sale=ticket_status,
                ticket_sale_date=ticket_sale_date
            )

        except Exception as e:
            print(f"Error parsing post: {e}")
            return None

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
