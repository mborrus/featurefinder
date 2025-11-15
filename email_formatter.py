"""
Email formatter for NYC movie screenings
"""
from typing import List, Dict
from scrapers.base import Screening
from datetime import datetime
from config import get_week_range


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
