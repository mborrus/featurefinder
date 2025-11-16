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
        week_str = f"{self.week_start.strftime('%B %d')} - {self.week_end.strftime('%B %d')}"
        return f"NYC Special Screenings: {week_str}"

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

        # Add day-by-day task list
        daily_tasks = self._generate_daily_tasks(grouped_screenings)
        if daily_tasks:
            html_parts.append(daily_tasks)

        html_parts.append(self._html_footer())

        return '\n'.join(html_parts)

    def _html_header(self) -> str:
        """HTML email header with styles"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Georgia, 'Times New Roman', Times, serif;
            line-height: 1.7;
            color: #2a2a2a;
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
            text-align: center;
            padding-bottom: 30px;
            margin-bottom: 35px;
            border-bottom: 1px solid #d8d8d8;
        }
        .masthead {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: #8c8c8c;
            margin-bottom: 12px;
        }
        h1 {
            font-family: Georgia, 'Times New Roman', Times, serif;
            font-size: 32px;
            font-weight: normal;
            color: #1a1a1a;
            margin: 0 0 15px 0;
            line-height: 1.3;
            letter-spacing: -0.5px;
        }
        .week-range {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 13px;
            color: #6b6b6b;
            font-style: italic;
        }
        h2 {
            font-family: Georgia, 'Times New Roman', Times, serif;
            font-size: 22px;
            font-weight: normal;
            color: #1a1a1a;
            margin: 45px 0 25px 0;
            padding-bottom: 12px;
            border-bottom: 1px solid #e8e8e8;
            letter-spacing: -0.3px;
        }
        .screening {
            margin-bottom: 35px;
            padding-bottom: 35px;
            border-bottom: 1px solid #f0f0f0;
        }
        .screening:last-child {
            border-bottom: none;
        }
        .title {
            font-family: Georgia, 'Times New Roman', Times, serif;
            font-size: 20px;
            font-weight: bold;
            color: #1a1a1a;
            margin-bottom: 8px;
            line-height: 1.4;
            letter-spacing: -0.2px;
        }
        .special-note {
            display: inline-block;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            background-color: #c9333d;
            color: #ffffff;
            padding: 4px 12px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .director {
            font-family: Georgia, 'Times New Roman', Times, serif;
            font-style: italic;
            color: #5a5a5a;
            font-size: 16px;
            margin-bottom: 8px;
        }
        .datetime {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #4a4a4a;
            font-size: 14px;
            margin-bottom: 12px;
            font-weight: 500;
        }
        .description {
            font-family: Georgia, 'Times New Roman', Times, serif;
            color: #3a3a3a;
            font-size: 16px;
            line-height: 1.7;
            margin: 12px 0;
        }
        .ticket-info {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #c9333d;
            font-size: 14px;
            margin-top: 10px;
        }
        .link {
            display: inline-block;
            margin-top: 12px;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #1a75bc;
            text-decoration: none;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.3px;
        }
        .link:hover {
            color: #145a94;
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
            font-family: Georgia, 'Times New Roman', Times, serif;
            font-size: 17px;
            line-height: 1.7;
            color: #3a3a3a;
            margin-bottom: 35px;
            padding: 20px 0;
            font-style: italic;
        }
        .footer {
            margin-top: 50px;
            padding-top: 25px;
            border-top: 1px solid #d8d8d8;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #8c8c8c;
            font-size: 12px;
            text-align: center;
            line-height: 1.6;
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
    <div class="masthead">Culture & Cinema</div>
    <h1>NYC Special Screenings</h1>
    <div class="week-range">{week_str}</div>
</div>
<div class="intro">
    Your curated guide to special screenings, premieres, Q&As, and repertory cinema in Manhattan this week.
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
            parts.append(f'<div class="datetime">{self._escape_html(datetime_str)}</div>')

        # Description
        if screening.description:
            parts.append(f'<div class="description">{self._escape_html(screening.description)}</div>')

        # Ticket info
        if screening.ticket_info:
            parts.append(f'<div class="ticket-info">{self._escape_html(screening.ticket_info)}</div>')

        # URL
        if screening.url:
            parts.append(f'<a href="{screening.url}" class="link">More information</a>')

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

    def _generate_daily_tasks(self, grouped_screenings: Dict[str, List[Screening]]) -> str:
        """Generate day-by-day task list section"""
        if not grouped_screenings:
            return ''

        # Organize tasks by day
        tasks_by_day = {}  # day_name -> [(task_description, theater)]

        for theater, screenings in grouped_screenings.items():
            for screening in screenings:
                # Add ticket sale date tasks
                if screening.ticket_sale_date:
                    day_name = self._parse_day_name(screening.ticket_sale_date)
                    if day_name:
                        task = f"Tickets go on sale for \"{screening.title}\""
                        if day_name not in tasks_by_day:
                            tasks_by_day[day_name] = []
                        tasks_by_day[day_name].append((task, theater))

                # Add screening date tasks (for special/notable screenings)
                if screening.date and screening.special_note:
                    day_name = self._parse_day_name(screening.date)
                    if day_name:
                        task_parts = [f"\"{screening.title}\" screening"]
                        if screening.time_slot:
                            task_parts.append(f"at {screening.time_slot}")
                        task = ' '.join(task_parts)
                        if day_name not in tasks_by_day:
                            tasks_by_day[day_name] = []
                        tasks_by_day[day_name].append((task, theater))

        if not tasks_by_day:
            return ''

        # Order days by week (Monday to Sunday)
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        ordered_days = [day for day in day_order if day in tasks_by_day]

        # Generate HTML
        html_parts = ['<div class="daily-tasks-section">']
        html_parts.append('<h2 class="daily-tasks-title">This Week at a Glance</h2>')

        for day in ordered_days:
            html_parts.append(f'<div class="day-section">')
            html_parts.append(f'<div class="day-header">{day}</div>')
            html_parts.append('<ul class="task-list">')

            for task, theater in tasks_by_day[day]:
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
