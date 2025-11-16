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

    def format_email(self, grouped_screenings: Dict[str, List[Screening]], top_highlights: List[Dict] = None) -> tuple:
        """
        Format screenings into email subject and HTML body

        Args:
            grouped_screenings: Dictionary mapping theater names to lists of screenings
            top_highlights: Optional list of top 4 highlight dictionaries

        Returns:
            tuple: (subject, html_body)
        """
        subject = self._create_subject()
        html_body = self._create_html_body(grouped_screenings, top_highlights)

        return subject, html_body

    def _create_subject(self) -> str:
        """Create email subject line"""
        week_str = f"{self.week_start.strftime('%B %d')} - {self.week_end.strftime('%B %d')}"
        return f"NYC Special Screenings: {week_str}"

    def _create_html_body(self, grouped_screenings: Dict[str, List[Screening]], top_highlights: List[Dict] = None) -> str:
        """Create HTML email body"""
        html_parts = [
            self._html_header(),
            self._html_intro(),
        ]

        # Add top 4 highlights section
        if top_highlights:
            html_parts.append(self._format_top_highlights(top_highlights))

        # Add screenings grouped by theater
        if grouped_screenings:
            for theater, screenings in grouped_screenings.items():
                html_parts.append(self._format_theater_section(theater, screenings))
        else:
            html_parts.append(self._no_screenings_message())

        # Add day-by-day task list
        daily_tasks = self._generate_daily_tasks(grouped_screenings)
        if daily_tasks:
            html_parts.append(daily_tasks)

        html_parts.append(self._html_footer())

        return '\n'.join(html_parts)

    def _html_header(self) -> str:
        """HTML email header with The Atlantic-inspired styles"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        /* The Atlantic-inspired newsletter styling */
        body {
            font-family: Georgia, serif;
            font-size: 17px;
            line-height: 1.6;
            color: #1a1a1a;
            max-width: 600px;
            margin: 0 auto;
            padding: 30px 20px;
            background-color: #ffffff;
        }
        .container {
            background-color: #ffffff;
            max-width: 600px;
            margin: 0 auto;
        }
        .header-section {
            margin-bottom: 40px;
            border-bottom: 1px solid #dddddd;
            padding-bottom: 20px;
        }
        h1 {
            font-family: Georgia, serif;
            font-size: 32px;
            font-weight: bold;
            color: #1a1a1a;
            margin: 0 0 10px 0;
            line-height: 1.2;
            letter-spacing: -0.5px;
        }
        .week-range {
            font-family: Helvetica, Arial, sans-serif;
            font-size: 13px;
            color: #767676;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        h2 {
            font-family: Georgia, serif;
            font-size: 20px;
            font-weight: bold;
            color: #1a1a1a;
            margin: 40px 0 20px 0;
            padding: 15px 0 10px 0;
            border-bottom: 2px solid #1a1a1a;
            border-top: 1px solid #e5e5e5;
        }
        .top-highlights-section {
            margin: 30px 0 40px 0;
            padding: 25px;
            background-color: #f9f9f9;
            border-left: 4px solid #C74444;
        }
        .top-highlights-title {
            font-family: Helvetica, Arial, sans-serif;
            font-size: 14px;
            font-weight: 600;
            color: #C74444;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
        }
        .highlight-item {
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e5e5e5;
        }
        .highlight-item:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }
        .highlight-title {
            font-family: Georgia, serif;
            font-size: 17px;
            font-weight: bold;
            color: #1a1a1a;
            margin-bottom: 4px;
        }
        .highlight-details {
            font-family: Helvetica, Arial, sans-serif;
            font-size: 14px;
            color: #666666;
            margin-bottom: 3px;
        }
        .highlight-why {
            font-family: Georgia, serif;
            font-size: 15px;
            color: #333333;
            font-style: italic;
        }
        .screening {
            margin-bottom: 30px;
            padding-bottom: 30px;
            border-bottom: 1px solid #e5e5e5;
        }
        .screening:last-child {
            border-bottom: none;
        }
        .title {
            font-family: Georgia, serif;
            font-size: 18px;
            font-weight: bold;
            color: #1a1a1a;
            margin-bottom: 6px;
            line-height: 1.3;
        }
        .special-note {
            font-family: Helvetica, Arial, sans-serif;
            color: #C74444;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .director {
            font-family: Georgia, serif;
            font-style: italic;
            color: #666666;
            font-size: 16px;
            margin-bottom: 6px;
        }
        .datetime {
            font-family: Helvetica, Arial, sans-serif;
            color: #767676;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .description {
            font-family: Georgia, serif;
            color: #333333;
            font-size: 17px;
            line-height: 1.6;
            margin: 10px 0;
        }
        .ticket-info {
            font-family: Helvetica, Arial, sans-serif;
            color: #666666;
            font-size: 14px;
            margin-top: 8px;
        }
        .link {
            display: inline-block;
            margin-top: 10px;
            font-family: Helvetica, Arial, sans-serif;
            color: #C74444;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
        }
        .link:hover {
            text-decoration: underline;
        }
        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #dddddd;
            font-family: Helvetica, Arial, sans-serif;
            color: #999999;
            font-size: 12px;
            line-height: 1.5;
            text-align: center;
        }
        .footer p {
            margin: 5px 0;
        }
        .daily-tasks-section {
            margin-top: 50px;
            padding-top: 30px;
            border-top: 2px solid #d8d8d8;
        }
        .daily-tasks-title {
            font-family: Georgia, 'Times New Roman', Times, serif;
            font-size: 26px;
            font-weight: normal;
            color: #1a1a1a;
            margin-bottom: 25px;
            letter-spacing: -0.4px;
        }
        .day-section {
            margin-bottom: 30px;
        }
        .day-header {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 16px;
            font-weight: 600;
            color: #c9333d;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        }
        .task-list {
            list-style: none;
            padding-left: 0;
            margin: 0;
        }
        .task-item {
            font-family: Georgia, 'Times New Roman', Times, serif;
            color: #3a3a3a;
            font-size: 15px;
            line-height: 1.8;
            padding: 8px 0 8px 20px;
            border-left: 3px solid #e8e8e8;
            margin-bottom: 8px;
            position: relative;
        }
        .task-item:before {
            content: '•';
            position: absolute;
            left: 8px;
            color: #c9333d;
            font-weight: bold;
        }
        .task-theater {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #6b6b6b;
            font-size: 13px;
            font-style: italic;
            margin-top: 2px;
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
<div class="header-section">
    <h1>NYC Special Screenings</h1>
    <div class="week-range">{week_str}</div>
    <p style="font-family: Georgia, serif; color: #666666; font-size: 15px; margin-top: 15px; line-height: 1.5;">
        Catch these screenings before tickets sell out. Focused on upcoming ticket releases and special events.
    </p>
</div>
"""

    def _format_top_highlights(self, top_highlights: List[Dict]) -> str:
        """Format the top 4 highlights section"""
        if not top_highlights:
            return ''

        html = ['<div class="top-highlights-section">']
        html.append('<div class="top-highlights-title">🎫 Priority: Get These Tickets Soon</div>')

        for highlight in top_highlights[:4]:  # Ensure only 4 items
            html.append('<div class="highlight-item">')
            html.append(f'<div class="highlight-title">{self._escape_html(highlight.get("title", ""))}</div>')

            details_parts = []
            if highlight.get('theater'):
                details_parts.append(highlight['theater'])
            if highlight.get('date_time'):
                details_parts.append(highlight['date_time'])

            if details_parts:
                html.append(f'<div class="highlight-details">{self._escape_html(" • ".join(details_parts))}</div>')

            if highlight.get('why_notable'):
                html.append(f'<div class="highlight-why">{self._escape_html(highlight["why_notable"])}</div>')

            html.append('</div>')

        html.append('</div>')
        return '\n'.join(html)

    def _format_theater_section(self, theater: str, screenings: List[Screening]) -> str:
        """Format a section for one theater"""
        html = f'<h2>{theater}</h2>\n'

        if not screenings:
            # Show a message for empty theaters
            html += '<p style="font-family: Georgia, serif; color: #999999; font-size: 16px; font-style: italic; margin: 20px 0;">No notable screenings selected this week.</p>\n'
        else:
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

        # Ticket sale date (MOST PROMINENT - moved to top)
        if screening.ticket_sale_date:
            parts.append(f'<div class="special-note">🎫 Tickets on sale: {self._escape_html(screening.ticket_sale_date)}</div>')

        # Special note badge
        if screening.special_note:
            parts.append(f'<div class="special-note">{self._escape_html(screening.special_note)}</div>')

        # Director
        if screening.director:
            parts.append(f'<div class="director">Directed by {self._escape_html(screening.director)}</div>')

        # Date and time (screening date)
        if screening.date or screening.time_slot:
            datetime_str = f"{screening.date} {screening.time_slot}".strip()
            parts.append(f'<div class="datetime">Screening: {self._escape_html(datetime_str)}</div>')

        # Description
        if screening.description:
            parts.append(f'<div class="description">{self._escape_html(screening.description)}</div>')

        # Ticket info
        if screening.ticket_info:
            parts.append(f'<div class="ticket-info">{self._escape_html(screening.ticket_info)}</div>')

        # URL
        if screening.url:
            parts.append(f'<a href="{screening.url}" class="link">More information & tickets</a>')

        parts.append('</div>')

        return '\n'.join(parts)

    def _no_screenings_message(self) -> str:
        """Message when no screenings found"""
        return """
<p style="font-family: Georgia, serif; color: #666666; font-size: 17px; line-height: 1.6;">No special screenings found for this week. Check back next Monday!</p>
"""

    def _generate_daily_tasks(self, grouped_screenings: Dict[str, List[Screening]]) -> str:
        """Generate day-by-day task list section"""
        if not grouped_screenings:
            return ''

        # Organize tasks by day
        tasks_by_day = {}  # day_name -> [(task_description, theater, priority)]

        for theater, screenings in grouped_screenings.items():
            for screening in screenings:
                # Add ticket sale date tasks (HIGHEST PRIORITY)
                if screening.ticket_sale_date:
                    day_name = self._parse_day_name(screening.ticket_sale_date)
                    if day_name:
                        task = f"🎫 Tickets go on sale for \"{screening.title}\""
                        if day_name not in tasks_by_day:
                            tasks_by_day[day_name] = []
                        # Priority 0 = ticket sales (shown first)
                        tasks_by_day[day_name].append((task, theater, 0))

                # Add screening date tasks (for special/notable screenings, lower priority)
                if screening.date and screening.special_note:
                    day_name = self._parse_day_name(screening.date)
                    if day_name:
                        task_parts = [f"\"{screening.title}\" screening"]
                        if screening.time_slot:
                            task_parts.append(f"at {screening.time_slot}")
                        task = ' '.join(task_parts)
                        if day_name not in tasks_by_day:
                            tasks_by_day[day_name] = []
                        # Priority 1 = screenings (shown after ticket sales)
                        tasks_by_day[day_name].append((task, theater, 1))

        if not tasks_by_day:
            return ''

        # Order days by week (Monday to Sunday)
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        ordered_days = [day for day in day_order if day in tasks_by_day]

        # Generate HTML
        html_parts = ['<div class="daily-tasks-section">']
        html_parts.append('<h2 class="daily-tasks-title">Ticket Release Calendar</h2>')
        html_parts.append('<p style="font-family: Georgia, serif; color: #666666; font-size: 15px; margin-bottom: 20px;">Mark your calendar for these important dates.</p>')

        for day in ordered_days:
            html_parts.append(f'<div class="day-section">')
            html_parts.append(f'<div class="day-header">{day}</div>')
            html_parts.append('<ul class="task-list">')

            # Sort tasks by priority (ticket sales first)
            sorted_tasks = sorted(tasks_by_day[day], key=lambda x: x[2])
            for task, theater, _ in sorted_tasks:
                html_parts.append('<li class="task-item">')
                html_parts.append(self._escape_html(task))
                html_parts.append(f'<div class="task-theater">{self._escape_html(theater)}</div>')
                html_parts.append('</li>')

            html_parts.append('</ul>')
            html_parts.append('</div>')

        html_parts.append('</div>')

        return '\n'.join(html_parts)

    def _parse_day_name(self, date_str: str) -> Optional[str]:
        """
        Parse a date string and return the day of week name.
        Handles formats like "Nov 15", "November 15", "Tuesday", etc.
        """
        if not date_str:
            return None

        date_str = date_str.strip()

        # Check if it's already a day name
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day in day_names:
            if day.lower() in date_str.lower():
                return day

        # Try to parse as a date
        try:
            # Pattern: "Nov 15", "November 15"
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

                # Create datetime and get day name
                dt = datetime(year, month, day)
                return dt.strftime('%A')  # Returns day name like "Monday"

        except Exception as e:
            # print(f"Error parsing day name from '{date_str}': {e}")
            pass

        return None

    def _html_footer(self) -> str:
        """HTML email footer"""
        return """
<div class="footer">
    <p>Automated weekly digest of special movie screenings in NYC</p>
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
