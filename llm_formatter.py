"""
LLM-powered formatter for NYC movie screenings
Uses Claude API to transform scraped data into engaging narrative stories
"""
import os
import json
from typing import List, Dict
from scrapers.base import Screening
from config import get_week_range
from anthropic import Anthropic


class LLMFormatter:
    """Uses Claude API to format screenings into engaging narrative stories"""

    def __init__(self):
        self.week_start, self.week_end = get_week_range()
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Please set it to use LLM formatting."
            )
        self.client = Anthropic(api_key=api_key)

    def format_with_llm(self, grouped_screenings: Dict[str, List[Screening]]) -> tuple:
        """
        Use Claude to format screenings into an engaging story

        Args:
            grouped_screenings: Dictionary mapping theater names to lists of screenings

        Returns:
            tuple: (subject, html_body)
        """
        print("  Preparing screening data for LLM...")

        # Convert screenings to a structured format for the LLM
        screenings_data = self._prepare_data_for_llm(grouped_screenings)

        # Create the prompt for Claude
        prompt = self._create_prompt(screenings_data)

        print("  Calling Claude API to generate formatted story...")

        try:
            # Call Claude API
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=8000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract the response
            html_body = message.content[0].text

            print(f"  ✓ LLM generated {len(html_body)} characters of content")

            # Create subject line
            subject = self._create_subject()

            return subject, html_body

        except Exception as e:
            print(f"  ✗ Error calling Claude API: {e}")
            raise

    def _prepare_data_for_llm(self, grouped_screenings: Dict[str, List[Screening]]) -> str:
        """Convert screening objects to a readable text format for the LLM"""
        if not grouped_screenings:
            return "No screenings found for this week."

        data_parts = []
        total_count = 0

        for theater, screenings in grouped_screenings.items():
            data_parts.append(f"\n=== {theater} ===")

            for screening in screenings:
                total_count += 1
                screening_info = [f"\nTitle: {screening.title}"]

                if screening.director:
                    screening_info.append(f"Director: {screening.director}")

                if screening.date or screening.time_slot:
                    datetime_str = f"{screening.date} {screening.time_slot}".strip()
                    screening_info.append(f"When: {datetime_str}")

                if screening.special_note:
                    screening_info.append(f"Special: {screening.special_note}")

                if screening.description:
                    screening_info.append(f"Description: {screening.description}")

                if screening.ticket_info:
                    screening_info.append(f"Tickets: {screening.ticket_info}")

                if screening.url:
                    screening_info.append(f"Info: {screening.url}")

                data_parts.append('\n'.join(screening_info))

        result = '\n'.join(data_parts)
        print(f"  Prepared {total_count} screenings from {len(grouped_screenings)} theaters")
        return result

    def _create_prompt(self, screenings_data: str) -> str:
        """Create the prompt for Claude to format the screenings into a story"""
        week_str = f"{self.week_start.strftime('%B %d')} - {self.week_end.strftime('%B %d, %Y')}"

        return f"""You are a film critic and cultural writer creating a weekly email newsletter about special movie screenings in New York City.

Below is data about special screenings, premieres, Q&As, and repertory cinema happening this week ({week_str}) in Manhattan.

Your task is to transform this raw data into an engaging, well-written HTML email that film enthusiasts will love to read.

REQUIREMENTS:
1. Create a complete HTML email (including <!DOCTYPE>, <html>, <head>, <body> tags)
2. Use attractive CSS styling - make it visually appealing with good typography and colors (suggest using a cinematic color scheme like deep reds #e50914, blacks, and elegant fonts)
3. Write an engaging introduction that highlights the most interesting or notable screenings this week
4. Organize the screenings in a narrative way - you could group by:
   - Themes (classics, new releases, director retrospectives, etc.)
   - Type of event (Q&As, special formats like 70mm/IMAX, premieres)
   - Or create a curated "top picks" section followed by other notable screenings
5. For each screening, include all the relevant details (title, director, date/time, special notes, description, ticket info, and a link)
6. Write in an enthusiastic but sophisticated tone - like a knowledgeable friend recommending films
7. Add personality and context - mention why certain screenings are special or worth attending
8. Make it scannable with clear headings, good spacing, and visual hierarchy
9. Include the title "NYC Special Screenings" and the week range prominently at the top
10. End with a brief footer noting this is an automated weekly digest

SCREENING DATA:
{screenings_data}

Generate the complete HTML email now:"""

    def _create_subject(self) -> str:
        """Create email subject line"""
        week_str = f"{self.week_start.strftime('%b %d')} - {self.week_end.strftime('%b %d')}"
        return f"NYC Special Screenings - Week of {week_str}"

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
