"""
Base scraper class for movie screening sources
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import time


class Screening:
    """Data class for a movie screening"""
    def __init__(self, title: str, theater: str, date: str = '', time_slot: str = '',
                 description: str = '', special_note: str = '', director: str = '',
                 ticket_info: str = '', url: str = '', priority: int = 5):
        self.title = title
        self.theater = theater
        self.date = date
        self.time_slot = time_slot
        self.description = description
        self.special_note = special_note
        self.director = director
        self.ticket_info = ticket_info
        self.url = url
        self.priority = priority  # Lower number = higher priority

    def to_dict(self) -> Dict:
        return {
            'title': self.title,
            'theater': self.theater,
            'date': self.date,
            'time': self.time_slot,
            'description': self.description,
            'special_note': self.special_note,
            'director': self.director,
            'ticket_info': self.ticket_info,
            'url': self.url,
            'priority': self.priority
        }

    def __repr__(self):
        return f"Screening({self.title} at {self.theater} on {self.date})"


class BaseScraper(ABC):
    """Base class for all scrapers"""

    def __init__(self, name: str):
        self.name = name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    @abstractmethod
    def scrape(self) -> List[Screening]:
        """Scrape screenings from the source"""
        pass

    def fetch_page(self, url: str, retries: int = 3) -> BeautifulSoup:
        """Fetch a page and return BeautifulSoup object"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                if attempt == retries - 1:
                    print(f"Failed to fetch {url}: {e}")
                    raise
                time.sleep(2 ** attempt)
        return None

    def is_special_screening(self, text: str) -> bool:
        """Check if text indicates a special screening"""
        text_lower = text.lower()
        keywords = [
            'q&a', 'q & a', 'director', 'opening night', 'premiere',
            'festival', 'special screening', 'advance screening',
            'preview', 'repertory', 'retrospective', 'restoration',
            '35mm', '70mm', 'imax', 'exclusive', 'limited release',
            'anniversary', 'midnight', 'classics', 'cult'
        ]
        return any(keyword in text_lower for keyword in keywords)
