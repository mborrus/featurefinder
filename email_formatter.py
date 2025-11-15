"""
Email formatter for NYC movie screenings
"""
from typing import List, Dict, Optional
from scrapers.base import Screening
from datetime import datetime, timedelta
from config import get_week_range
import re
from urllib.parse import quote


class EmailFormatter:
    """Formats screenings into HTML email"""

    def __init__(self):
        self.week_start, self.week_end = get_week_range()

    def format_email(self, grouped_screenings: Dict[str, List[Screening]]) -> tuple:
        """
        Format screenings into email subject and HTML body

        Returns:
            tuple: (subject, html_body)
        """
        subject = self._create_subject()
        html_body = self._create_html_body(grouped_screenings)

        return subject, html_body

    def _create_subject(self) -> str:
        """Create email subject line"""
        week_str = f"{self.week_start.strftime('%b %d')} - {self.week_end.strftime('%b %d')}"
        return f"NYC Special Screenings - Week of {week_str}"

    def _create_html_body(self, grouped_screenings: Dict[str, List[Screening]]) -> str:
        """Create HTML email body"""
        html_parts = [
            self._html_header(),
            self._html_intro(),
        ]

        # Add screenings grouped by theater
        if grouped_screenings:
            for theater, screenings in grouped_screenings.items():
                html_parts.append(self._format_theater_section(theater, screenings))
        else:
            html_parts.append(self._no_screenings_message())

        html_parts.append(self._html_footer())

        return '\n'.join(html_parts)

    def _html_header(self) -> str:
        """HTML email header with styles"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1a1a1a;
            border-bottom: 3px solid #e50914;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        h2 {
            color: #e50914;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 1.5em;
        }
        .screening {
            margin-bottom: 25px;
            padding: 15px;
            background-color: #fafafa;
            border-left: 4px solid #e50914;
            border-radius: 4px;
        }
        .title {
            font-size: 1.2em;
            font-weight: bold;
            color: #1a1a1a;
            margin-bottom: 5px;
        }
        .special-note {
            display: inline-block;
            background-color: #e50914;
            color: white;
            padding: 3px 10px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .director {
            font-style: italic;
            color: #666;
            margin-bottom: 5px;
        }
        .datetime {
            color: #444;
            font-weight: 500;
            margin-bottom: 5px;
        }
        .description {
            color: #555;
            margin: 10px 0;
        }
        .ticket-info {
            color: #e50914;
            font-weight: 500;
            margin-top: 5px;
        }
        .link {
            display: inline-block;
            margin-top: 8px;
            color: #0066cc;
            text-decoration: none;
            font-size: 0.9em;
        }
        .link:hover {
            text-decoration: underline;
        }
        .calendar-button {
            display: inline-block;
            margin-top: 10px;
            padding: 8px 16px;
            background-color: #4285f4;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.9em;
            font-weight: 500;
            transition: background-color 0.2s;
        }
        .calendar-button:hover {
            background-color: #357ae8;
        }
        .intro {
            background-color: #f0f0f0;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 25px;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 0.9em;
            text-align: center;
        }
    </style>
</head>
<body>
<div class="container">
"""

    def _html_intro(self) -> str:
        """Create intro section"""
        week_str = f"{self.week_start.strftime('%B %d')} - {self.week_end.strftime('%B %d, %Y')}"
        return f"""
<h1>🎬 NYC Special Screenings</h1>
<div class="intro">
    <strong>Week of {week_str}</strong><br>
    Your curated guide to special screenings, premieres, Q&As, and repertory cinema in Manhattan.
</div>
"""

    def _format_theater_section(self, theater: str, screenings: List[Screening]) -> str:
        """Format a section for one theater"""
        html = f'<h2>{theater}</h2>\n'

        for screening in screenings:
            html += self._format_screening(screening)

        return html

    def _parse_datetime(self, screening: Screening) -> Optional[datetime]:
        """
        Parse screening date and time into a datetime object.
        Returns None if parsing fails.
        """
        if not screening.date:
            return None

        try:
            # Common date patterns: "Nov 15", "November 15", "11/15", etc.
            date_str = screening.date.strip()

            # Try to parse month and day
            # Pattern 1: "Nov 15", "November 15"
            month_day_match = re.match(r'([A-Za-z]+)\s+(\d{1,2})', date_str)
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
                month = month_names.get(month_str.lower())
                if not month:
                    return None

                # Determine year based on week range
                year = self.week_start.year
                # If the month is before week_start month and we're near year end, use next year
                if month < self.week_start.month and self.week_start.month >= 11:
                    year += 1

                # Parse time if available
                hour = 19  # Default to 7 PM
                minute = 0

                if screening.time_slot:
                    time_str = screening.time_slot.strip()
                    # Pattern: "7:30 PM", "7pm", "19:30"
                    time_match = re.match(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', time_str, re.IGNORECASE)
                    if time_match:
                        hour_str, min_str, meridiem = time_match.groups()
                        hour = int(hour_str)
                        minute = int(min_str) if min_str else 0

                        # Handle AM/PM
                        if meridiem:
                            meridiem = meridiem.lower()
                            if meridiem == 'pm' and hour < 12:
                                hour += 12
                            elif meridiem == 'am' and hour == 12:
                                hour = 0

                return datetime(year, month, day, hour, minute)

            return None
        except Exception as e:
            print(f"Error parsing datetime: {e}")
            return None

    def _create_google_calendar_url(self, screening: Screening) -> Optional[str]:
        """
        Create a Google Calendar URL for adding the screening to calendar.
        Returns None if date/time cannot be parsed.
        """
        start_time = self._parse_datetime(screening)
        if not start_time:
            return None

        # Assume 2-hour duration for movies
        end_time = start_time + timedelta(hours=2)

        # Format dates for Google Calendar (YYYYMMDDTHHmmSS)
        start_str = start_time.strftime('%Y%m%dT%H%M%S')
        end_str = end_time.strftime('%Y%m%dT%H%M%S')

        # Build calendar URL
        title = screening.title
        details_parts = []
        if screening.special_note:
            details_parts.append(f"Special: {screening.special_note}")
        if screening.director:
            details_parts.append(f"Director: {screening.director}")
        if screening.description:
            details_parts.append(screening.description)
        if screening.ticket_info:
            details_parts.append(f"Tickets: {screening.ticket_info}")
        if screening.url:
            details_parts.append(f"More info: {screening.url}")

        details = '\n\n'.join(details_parts)
        location = screening.theater

        # URL encode parameters
        params = {
            'action': 'TEMPLATE',
            'text': title,
            'dates': f'{start_str}/{end_str}',
            'details': details,
            'location': location
        }

        # Build URL
        url = 'https://www.google.com/calendar/render?'
        url += '&'.join(f'{k}={quote(v)}' for k, v in params.items())

        return url

    def _format_screening(self, screening: Screening) -> str:
        """Format a single screening"""
        parts = ['<div class="screening">']

        # Title
        parts.append(f'<div class="title">{self._escape_html(screening.title)}</div>')

        # Special note badge
        if screening.special_note:
            parts.append(f'<div class="special-note">{self._escape_html(screening.special_note)}</div>')

        # Director
        if screening.director:
            parts.append(f'<div class="director">Directed by {self._escape_html(screening.director)}</div>')

        # Date and time
        if screening.date or screening.time_slot:
            datetime_str = f"{screening.date} {screening.time_slot}".strip()
            parts.append(f'<div class="datetime">📅 {self._escape_html(datetime_str)}</div>')

        # Description
        if screening.description:
            parts.append(f'<div class="description">{self._escape_html(screening.description)}</div>')

        # Ticket info
        if screening.ticket_info:
            parts.append(f'<div class="ticket-info">🎟️ {self._escape_html(screening.ticket_info)}</div>')

        # URL
        if screening.url:
            parts.append(f'<a href="{screening.url}" class="link">More Info →</a>')

        # Google Calendar button
        calendar_url = self._create_google_calendar_url(screening)
        if calendar_url:
            parts.append(f'<a href="{calendar_url}" class="calendar-button" target="_blank">📅 Add to Google Calendar</a>')

        parts.append('</div>')

        return '\n'.join(parts)

    def _no_screenings_message(self) -> str:
        """Message when no screenings found"""
        return """
<div class="intro">
    <p>No special screenings found for this week. Check back next Monday!</p>
</div>
"""

    def _html_footer(self) -> str:
        """HTML email footer"""
        return """
<div class="footer">
    <p>This is an automated weekly digest of special movie screenings in NYC.</p>
    <p>Generated on """ + datetime.now().strftime('%B %d, %Y at %I:%M %p') + """</p>
</div>
</div>
</body>
</html>
"""

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        if not text:
            return ''
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))
