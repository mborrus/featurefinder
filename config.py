"""
Configuration for NYC Movie Screening Notifier
"""
import os
from datetime import datetime, timedelta

# Email configuration
RECIPIENT_EMAIL = "msborrus@gmail.com"
SENDER_EMAIL = "msborrus@gmail.com"  # Must be verified in SendGrid
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')

# LLM API configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

# Reddit configuration
# Note: Reddit API credentials are no longer needed - we use web scraping via .json endpoints
REDDIT_CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID', '')  # Deprecated
REDDIT_CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET', '')  # Deprecated
REDDIT_USER_AGENT = 'NYC Movie Screening Scraper v1.0'  # Kept for compatibility

# Date range for upcoming week
def get_week_range():
    """Get the date range for the upcoming week"""
    today = datetime.now()
    # Get next Monday (or today if it's Monday)
    days_ahead = 0 - today.weekday()  # Monday is 0
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    next_monday = today + timedelta(days=days_ahead)
    next_sunday = next_monday + timedelta(days=6)
    return next_monday, next_sunday

# Theater configurations
THEATERS = {
    'Film at Lincoln Center': {
        'url': 'https://www.filmlinc.org/',
        'location': 'Manhattan',
        'priority': 1
    },
    'AMC Lincoln Square': {
        'url': 'https://www.amctheatres.com/movie-theatres/new-york-city/amc-lincoln-square-13',
        'location': 'Manhattan',
        'priority': 1
    },
    'AMC 84th Street': {
        'url': 'https://www.amctheatres.com/movie-theatres/new-york-city/amc-84th-street-6',
        'location': 'Manhattan',
        'priority': 1
    },
    'Paris Theater': {
        'url': 'https://www.paristheatrenyc.com/',
        'location': 'Manhattan',
        'priority': 1
    },
    'Angelika Film Center': {
        'url': 'https://www.angelikafilmcenter.com/nyc',
        'location': 'Manhattan',
        'priority': 1
    },
    'Film Forum': {
        'url': 'https://filmforum.org/',
        'location': 'Manhattan',
        'priority': 2
    },
    'IFC Center': {
        'url': 'https://www.ifccenter.com/',
        'location': 'Manhattan',
        'priority': 3
    },
    'Metrograph': {
        'url': 'https://metrograph.com/',
        'location': 'Manhattan',
        'priority': 2
    },
    'The Roxy Cinema': {
        'url': 'https://www.roxycinemanewyork.com/',
        'location': 'Manhattan',
        'priority': 2
    },
    'Alamo Drafthouse Lower Manhattan': {
        'url': 'https://drafthouse.com/nyc',
        'location': 'Manhattan',
        'priority': 1
    },
    'MoMA': {
        'url': 'https://www.moma.org/calendar/film',
        'location': 'Manhattan',
        'priority': 3
    }
}

# Keywords that indicate special screenings (comprehensive list)
SPECIAL_KEYWORDS = [
    # Q&A and appearances
    'q&a', 'q & a', 'q and a', 'question and answer',
    'director', 'with director', 'director in person', 'director present',
    'filmmaker', 'filmmakers', 'with filmmaker', 'filmmaker in person',
    'cast', 'actor', 'actress', 'in person', 'guest appearance', 'special guest',

    # Premieres and special events
    'premiere', 'world premiere', 'us premiere', 'nyc premiere',
    'opening night', 'closing night',
    'advance screening', 'early access', 'pre-release',
    'sneak preview', 'sneak peek', 'preview screening',

    # Film formats
    'imax', 'dolby', 'dolby atmos', 'dolby cinema',
    '70mm', '35mm', '16mm',

    # Restorations and anniversaries
    'restoration', 'restored', '4k restoration', '4k', 'remastered',
    'anniversary', 'th anniversary', 'celebrating',

    # Festival and series
    'festival', 'film festival', 'nyff', 'new york film festival',
    'series', 'retrospective', 'tribute', 'special program',
    'repertory', 'revival', 'classic screening', 'classics', 'cult',

    # Special programming
    'exclusive', 'limited release', 'limited engagement',
    'fan event', 'marathon', 'double feature',
    'special screening', 'special event', 'gala', 'benefit',
    'midnight', 'late night', 'rare'
]

# Priority theaters that should NEVER be filtered out
# All screenings from these theaters are always included in emails
PRIORITY_THEATERS = [
    'Angelika Film Center',
    'AMC Lincoln Square',
    'AMC 84th Street',
    'Paris Theater'
]

# Wide release exclusion patterns
EXCLUDE_PATTERNS = [
    'brooklyn',  # Unless marked as exclusive
    'regular screening'
]

def get_theater_url(theater_name: str) -> str:
    """
    Get the base URL for a theater by name.
    Returns the theater's URL or empty string if not found.
    """
    theater_config = THEATERS.get(theater_name, {})
    return theater_config.get('url', '')
