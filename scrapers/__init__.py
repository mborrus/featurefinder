"""
Scrapers for NYC movie screening sources
"""
from .screenslate import ScreenslateScraper
from .reddit import RedditScraper
from .timeout_nyc import TimeOutScraper
from .film_forum import FilmForumScraper
from .ifc_center import IFCCenterScraper
from .metrograph import MetrographScraper
# from .new_yorker import NewYorkerScraper  # REMOVED: 403 Forbidden - site blocks scrapers
from .angelika import AngelikaScraper
from .film_at_lincoln_center import FilmAtLincolnCenterScraper
from .amc import AMCScraper
from .roxy_cinema import RoxyCinemaScraper
from .paris_theater import ParisTheaterScraper
from .moma import MoMAScraper
from .alamo_drafthouse import AlamoDrafthouseScraper

__all__ = [
    'ScreenslateScraper',
    'RedditScraper',
    'TimeOutScraper',
    'FilmForumScraper',
    'IFCCenterScraper',
    'MetrographScraper',
    # 'NewYorkerScraper',  # REMOVED: 403 Forbidden
    'AngelikaScraper',
    'FilmAtLincolnCenterScraper',
    'AMCScraper',
    'RoxyCinemaScraper',
    'ParisTheaterScraper',
    'MoMAScraper',
    'AlamoDrafthouseScraper'
]
