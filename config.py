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
        'priority': 2
    },
    'Angelika Film Center': {
        'url': 'https://www.angelikafilmcenter.com/nyc',
        'location': 'Manhattan',
        'priority': 2
    },
    'Film Forum': {
        'url': 'https://filmforum.org/',
        'location': 'Manhattan',
        'priority': 2
    },
    'IFC Center': {
        'url': 'https://www.ifccenter.com/',
        'location': 'Manhattan',
        'priority': 2
    },
    'Metrograph': {
        'url': 'https://metrograph.com/',
        'location': 'Manhattan',
        'priority': 2
    },
    'Alamo Drafthouse NYC': {
        'url': 'https://drafthouse.com/nyc',
        'location': 'Manhattan',
        'priority': 3
    }
}

# Keywords that indicate special screenings
SPECIAL_KEYWORDS = [
    'q&a', 'q & a', 'director', 'opening night', 'premiere',
    'festival', 'series', 'special screening', 'advance screening',
    'early access', 'preview', 'repertory', 'retrospective',
    'restoration', 'anniversary', '35mm', '70mm', 'imax',
    'dolby', 'exclusive', 'limited release', 'pre-release',
    'midnight', 'late night', 'classics', 'cult', 'rare'
]

# Major film festivals - keywords to detect festival pedigree
FESTIVAL_KEYWORDS = [
    'cannes', 'palme d\'or', 'palme dor',
    'venice', 'golden lion', 'silver lion',
    'berlin', 'berlinale', 'golden bear', 'silver bear',
    'sundance', 'grand jury prize',
    'toronto', 'tiff', 'people\'s choice',
    'telluride',
    'new york film festival', 'nyff',
    'tribeca',
    'sxsw', 'south by southwest',
    'locarno',
    'karlovy vary',
    'san sebastian',
    'busan',
    'rotterdam',
    'karlovy vary',
    'certified fresh', 'rotten tomatoes'
]

# Awards keywords - Oscar, Golden Globe, etc.
AWARDS_KEYWORDS = [
    'oscar', 'academy award', 'oscar nominee', 'oscar winner',
    'golden globe', 'bafta', 'sag award', 'screen actors guild',
    'critics choice', 'gotham', 'independent spirit',
    'cesar', 'critic\'s pick', 'new york times critic',
    'best picture', 'best director', 'best actor', 'best actress',
    'best screenplay', 'best cinematography',
    'national board of review', 'nbr'
]

# Notable festival films 2024-2025 and 2025-2026 seasons
# These films premiered at major festivals and should be prioritized
FESTIVAL_FILMS_2024_2025 = {
    # ===== 2024-2025 OSCAR SEASON (95th Academy Awards) =====

    # Cannes 2024
    'anora': {'festivals': ['Cannes'], 'awards': ['Palme d\'Or']},
    'the substance': {'festivals': ['Cannes'], 'awards': ['Best Screenplay']},
    'all we imagine as light': {'festivals': ['Cannes'], 'awards': ['Grand Prix']},
    'emilia pérez': {'festivals': ['Cannes'], 'awards': ['Jury Prize']},
    'megalopolis': {'festivals': ['Cannes'], 'awards': []},
    'the shrouds': {'festivals': ['Cannes'], 'awards': []},
    'oh canada': {'festivals': ['Cannes'], 'awards': []},
    'kinds of kindness': {'festivals': ['Cannes'], 'awards': []},
    'parthenope': {'festivals': ['Cannes'], 'awards': []},

    # Venice 2024
    'the brutalist': {'festivals': ['Venice'], 'awards': ['Silver Lion']},
    'the room next door': {'festivals': ['Venice'], 'awards': ['Golden Lion']},
    'joker: folie à deux': {'festivals': ['Venice'], 'awards': []},
    'queer': {'festivals': ['Venice'], 'awards': []},
    'maria': {'festivals': ['Venice'], 'awards': []},
    'babygirl': {'festivals': ['Venice'], 'awards': []},
    'the order': {'festivals': ['Venice'], 'awards': []},
    'wolfs': {'festivals': ['Venice'], 'awards': []},

    # Telluride 2024
    'conclave': {'festivals': ['Telluride', 'TIFF'], 'awards': []},
    'a real pain': {'festivals': ['Telluride', 'TIFF'], 'awards': []},
    'nickel boys': {'festivals': ['Telluride', 'NYFF'], 'awards': []},
    'september 5': {'festivals': ['Telluride', 'TIFF'], 'awards': []},
    'the piano lesson': {'festivals': ['Telluride', 'TIFF'], 'awards': []},

    # Toronto 2024 (TIFF)
    'the end': {'festivals': ['TIFF'], 'awards': []},
    'eden': {'festivals': ['TIFF'], 'awards': []},
    'we live in time': {'festivals': ['TIFF'], 'awards': []},
    'the life of chuck': {'festivals': ['TIFF'], 'awards': ['People\'s Choice Award']},
    'better man': {'festivals': ['TIFF'], 'awards': []},

    # Sundance 2024
    'a different man': {'festivals': ['Sundance', 'Berlin'], 'awards': []},
    'i saw the tv glow': {'festivals': ['Sundance'], 'awards': []},
    'didi': {'festivals': ['Sundance'], 'awards': ['Audience Award']},
    'sing sing': {'festivals': ['TIFF', 'Sundance'], 'awards': []},

    # NYFF 2024
    'no other land': {'festivals': ['NYFF', 'Berlin'], 'awards': ['Berlinale Documentary Prize']},
    'hard truths': {'festivals': ['NYFF'], 'awards': []},
    'flow': {'festivals': ['NYFF', 'Annecy'], 'awards': []},
    'dahomey': {'festivals': ['NYFF', 'Berlin'], 'awards': ['Golden Bear']},

    # Other notable releases 2024-2025
    'dune: part two': {'festivals': [], 'awards': []},
    'wicked': {'festivals': [], 'awards': []},
    'nosferatu': {'festivals': [], 'awards': []},
    'a complete unknown': {'festivals': [], 'awards': []},

    # ===== 2025-2026 OSCAR SEASON (96th Academy Awards) =====

    # Cannes 2025
    'sentimental value': {'festivals': ['Cannes', 'Telluride'], 'awards': ['Grand Prix']},

    # Venice 2025
    'bugonia': {'festivals': ['Venice'], 'awards': []},
    'frankenstein': {'festivals': ['Venice'], 'awards': []},

    # Telluride 2025
    'hamnet': {'festivals': ['Telluride', 'TIFF'], 'awards': ['TIFF People\'s Choice Award']},

    # NYFF 2025
    'marty supreme': {'festivals': ['NYFF'], 'awards': []},

    # Wide releases 2025 (Oscar contenders)
    'one battle after another': {'festivals': [], 'awards': []},
    'sinners': {'festivals': [], 'awards': []},
    'wicked: for good': {'festivals': [], 'awards': []},
}

# Oscar contenders 2024-2025 and 2025-2026 seasons
# Based on predictions and industry buzz from Variety, Gold Derby, and other sources
OSCAR_CONTENDERS_2025 = [
    # 2024-2025 season (95th Academy Awards, March 2025)
    'anora', 'the brutalist', 'conclave', 'dune: part two',
    'emilia pérez', 'wicked', 'a real pain', 'sing sing',
    'nickel boys', 'the substance', 'nosferatu', 'a complete unknown',
    'queer', 'the piano lesson', 'babygirl', 'maria',
    'all we imagine as light', 'september 5', 'didi',
    'a different man', 'the order', 'flow',

    # 2025-2026 season (96th Academy Awards, March 2026)
    'hamnet', 'one battle after another', 'sinners', 'marty supreme',
    'sentimental value', 'bugonia', 'frankenstein', 'wicked: for good',
    'avatar: fire and ash'
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

# =============================================================================
# Dynamic Awards Data Loading
# =============================================================================

def get_live_awards_data(use_cache: bool = True) -> tuple:
    """
    Get the latest festival films and Oscar contenders data.

    If cache exists and is fresh (< 7 days), uses cached data.
    Otherwise, attempts to fetch latest predictions from web sources.
    Falls back to hardcoded data if fetching fails.

    Args:
        use_cache: If True, use cached data when available.
                   If False, force refresh from web sources.

    Returns:
        tuple: (festival_films_dict, oscar_contenders_list)
    """
    try:
        from awards_updater import AwardsUpdater

        updater = AwardsUpdater()

        # Check if we should update (cache expired or force refresh)
        if not use_cache or updater.should_update():
            print("  Fetching latest awards predictions...")
            updater.update_cache()

        # Load awards data
        data = updater.get_awards_data()

        festival_films = data.get('festival_films', FESTIVAL_FILMS_2024_2025)
        oscar_contenders = data.get('oscar_contenders', OSCAR_CONTENDERS_2025)

        return festival_films, oscar_contenders

    except Exception as e:
        print(f"  Warning: Could not load live awards data: {e}")
        print("  Using hardcoded awards data")
        return FESTIVAL_FILMS_2024_2025, OSCAR_CONTENDERS_2025
