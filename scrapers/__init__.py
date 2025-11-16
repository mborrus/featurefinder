"""
Scrapers for NYC movie screening sources
"""
from .screenslate import ScreenslateScraper
from .reddit import RedditScraper
from .timeout_nyc import TimeOutScraper
from .film_forum import FilmForumScraper
from .ifc_center import IFCCenterScraper
from .metrograph import MetrographScraper
from .new_yorker import NewYorkerScraper
from .angelika import AngelikaScraper
from .film_at_lincoln_center import FilmAtLincolnCenterScraper
from .amc import AMCScraper
from .alamo_drafthouse import AlamoDrafthouseScraper

__all__ = [
    'ScreenslateScraper',
    'RedditScraper',
    'TimeOutScraper',
    'FilmForumScraper',
    'IFCCenterScraper',
    'MetrographScraper',
    'NewYorkerScraper',
    'AngelikaScraper',
    'FilmAtLincolnCenterScraper',
    'AMCScraper',
    'AlamoDrafthouseScraper'
]
