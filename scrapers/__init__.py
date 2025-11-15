"""
Scrapers for NYC movie screening sources
"""
from .screenslate import ScreenslateScraper
from .reddit import RedditScraper
from .timeout_nyc import TimeOutScraper
from .film_forum import FilmForumScraper
from .ifc_center import IFCCenterScraper
from .metrograph import MetrographScraper

__all__ = [
    'ScreenslateScraper',
    'RedditScraper',
    'TimeOutScraper',
    'FilmForumScraper',
    'IFCCenterScraper',
    'MetrographScraper'
]
