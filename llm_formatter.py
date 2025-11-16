"""
LLM-powered formatter for NYC movie screenings
Uses Claude API to generate stories and Gemini to verify content quality
"""
import os
import json
from typing import List, Dict
from scrapers.base import Screening
from config import get_week_range
from anthropic import Anthropic
import google.generativeai as genai


class LLMFormatter:
    """Uses Claude API to generate stories and Gemini to verify content quality"""

    def __init__(self):
        self.week_start, self.week_end = get_week_range()

        # Initialize Anthropic client
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
        if not anthropic_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Please set it to use LLM formatting."
            )
        self.anthropic_client = Anthropic(api_key=anthropic_key)

        # Initialize Gemini client
        gemini_key = os.environ.get('GEMINI_API_KEY')
        if not gemini_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable not set. "
                "Please set it to use LLM verification."
            )
        genai.configure(api_key=gemini_key)
        self.gemini_model = genai.GenerativeModel('gemini-flash-latest')

    def format_with_llm(self, grouped_screenings: Dict[str, List[Screening]]) -> tuple:
        """
        Use Claude to generate structured JSON, then Gemini to verify, then format with template

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

        print("  Step 1: Calling Claude API to generate structured JSON...")

        try:
            # Step 1: Call Claude API to generate JSON structure
            claude_message = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=8000,
                temperature=0.3,  # Lower temperature for structured output
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract Claude's response
            claude_json = claude_message.content[0].text.strip()

            # Remove markdown code blocks if present
            if claude_json.startswith('```'):
                lines = claude_json.split('\n')
                claude_json = '\n'.join(lines[1:-1]) if len(lines) > 2 else claude_json
                claude_json = claude_json.replace('```json', '').replace('```', '').strip()

            print(f"  ✓ Claude generated {len(claude_json)} characters of JSON")

            # Step 2: Use Gemini to verify and potentially refine the JSON
            print("  Step 2: Calling Gemini API to verify JSON quality...")

            verification_prompt = self._create_verification_prompt(claude_json, screenings_data)

            gemini_response = self.gemini_model.generate_content(
                verification_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Very low temperature for verification
                    max_output_tokens=8000,
                )
            )

            # Extract the verified/refined JSON
            verified_json = gemini_response.text.strip()

            # Remove markdown code blocks if present
            if verified_json.startswith('```'):
                lines = verified_json.split('\n')
                verified_json = '\n'.join(lines[1:-1]) if len(lines) > 2 else verified_json
                verified_json = verified_json.replace('```json', '').replace('```', '').strip()

            print(f"  ✓ Gemini verified JSON ({len(verified_json)} characters)")

            # Step 3: Parse JSON and format with Python template
            print("  Step 3: Formatting with HTML template...")

            import json
            from email_formatter import EmailFormatter

            screening_data = json.loads(verified_json)
            formatter = EmailFormatter()

            # Convert JSON structure to grouped_screenings format
            formatted_screenings = {}
            for theater_section in screening_data.get('theaters', []):
                theater_name = theater_section['name']
                formatted_screenings[theater_name] = []

                for screening_json in theater_section.get('screenings', []):
                    # Create Screening objects from JSON
                    from scrapers.base import Screening
                    screening = Screening(
                        title=screening_json.get('title', ''),
                        theater=theater_name,
                        date='',  # Will be parsed from date_time
                        time_slot='',  # Will be parsed from date_time
                        director=screening_json.get('director', ''),
                        special_note=screening_json.get('special_note', ''),
                        description=screening_json.get('description', ''),
                        ticket_info=screening_json.get('ticket_info', ''),
                        url=screening_json.get('url', '')
                    )

                    # Parse date_time if available
                    date_time = screening_json.get('date_time', '')
                    if date_time:
                        # Simple split on comma or time markers
                        if ',' in date_time:
                            parts = date_time.split(',', 1)
                            screening.date = parts[0].strip()
                            screening.time_slot = parts[1].strip() if len(parts) > 1 else ''
                        else:
                            screening.date = date_time

                    formatted_screenings[theater_name].append(screening)

            # Use the standard formatter
            subject, html_body = formatter.format_email(formatted_screenings)

            print(f"  ✓ HTML email generated ({len(html_body)} characters)")

            return subject, html_body

        except json.JSONDecodeError as e:
            print(f"  ✗ Error parsing JSON: {e}")
            print(f"  JSON content: {verified_json[:500]}...")
            raise
        except Exception as e:
            print(f"  ✗ Error in LLM pipeline: {e}")
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
        """Create the prompt for Claude to output structured JSON"""
        week_str = f"{self.week_start.strftime('%B %d')} - {self.week_end.strftime('%B %d, %Y')}"

        return f"""You are organizing screening data for a weekly email newsletter about special movie screenings in New York City.

Below is data about special screenings, premieres, Q&As, and repertory cinema happening this week ({week_str}) in Manhattan.

Your task is to organize this data into a clean JSON structure that will be used by a Python template to generate the HTML email.

CURATION GUIDELINES (IMPORTANT):
- Focus on NOTABLE and ACCESSIBLE screenings - not super avant garde or experimental films
- Prioritize: Q&As, director appearances, 70mm/IMAX, restorations, premieres, classic film revivals
- Include mainstream repertory (Godfather, Casablanca, etc.) and important art films (Bergman, Fellini, etc.)
- EXCLUDE: Highly experimental/underground films, ultra-niche micro-cinema events
- AIM FOR: 8-15 total screenings across all theaters (curate down if there are too many)
- If there are many similar screenings, keep only the most notable ones

REQUIREMENTS:
1. Output ONLY valid JSON (no markdown, no explanations, no HTML)
2. Organize screenings by theater into separate sections
3. Focus on these key theaters (create one section for each that has screenings):
   - Film at Lincoln Center
   - AMC Lincoln Square
   - AMC 84th Street
   - Paris Theater
   - Angelika Film Center
   - Metrograph
   - Film Forum
   - IFC Center
4. For each screening, extract and organize:
   - title (string)
   - director (string or null)
   - date_time (string - combined date and time)
   - special_note (string or null - brief, e.g., "Q&A with director")
   - description (string or null - keep concise, 1-2 sentences max)
   - ticket_info (string or null)
   - url (string or null)
5. Keep all text CONCISE and factual - no flowery language
6. If a theater has no notable screenings, omit that section entirely

JSON STRUCTURE:
{{
  "theaters": [
    {{
      "name": "Theater Name",
      "screenings": [
        {{
          "title": "Film Title",
          "director": "Director Name",
          "date_time": "November 20, 7:00 PM",
          "special_note": "Q&A with director",
          "description": "Brief description here",
          "ticket_info": "$15",
          "url": "https://..."
        }}
      ]
    }}
  ]
}}

SCREENING DATA:
{screenings_data}

Generate the JSON now. Output ONLY the JSON, nothing else:"""

    def _create_verification_prompt(self, claude_json: str, screenings_data: str) -> str:
        """Create the prompt for Gemini to verify Claude's JSON output"""
        week_str = f"{self.week_start.strftime('%B %d')} - {self.week_end.strftime('%B %d, %Y')}"

        return f"""You are a quality assurance editor reviewing structured data for an NYC movie screenings newsletter.

Below is JSON output generated by another AI system, along with the original screening data it was based on.

Your task is to:
1. Verify that important screening information is included
2. Check for any factual errors or hallucinated information
3. Ensure the JSON is valid and properly formatted
4. Verify that all dates, times, and details are accurate
5. Ensure all text is CONCISE and factual - no flowery language
6. CURATE: Ensure the selection is focused on notable, accessible screenings (not ultra avant garde)
7. LIMIT: Aim for 8-15 total screenings max - remove less notable ones if there are too many
8. If you find any issues, correct them

IMPORTANT:
- Do NOT include super experimental/avant garde films - focus on accessible special screenings
- Prioritize: Q&As, 70mm/IMAX, restorations, director appearances, notable revivals
- Do NOT add verbose or creative language - keep it concise and factual
- Do focus on factual accuracy
- Return ONLY valid JSON (no markdown, no explanations)

ORIGINAL SCREENING DATA:
{screenings_data}

GENERATED JSON TO VERIFY:
{claude_json}

Please return the verified/corrected JSON:"""

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
