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
        Use Claude to generate story, then Gemini to verify content quality

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

        print("  Step 1: Calling Claude API to generate formatted story...")

        try:
            # Step 1: Call Claude API to generate the story
            claude_message = self.anthropic_client.messages.create(
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

            # Extract Claude's response
            claude_html = claude_message.content[0].text

            print(f"  ✓ Claude generated {len(claude_html)} characters of content")

            # Step 2: Use Gemini to verify and potentially refine the content
            print("  Step 2: Calling Gemini API to verify content quality...")

            verification_prompt = self._create_verification_prompt(claude_html, screenings_data)

            gemini_response = self.gemini_model.generate_content(
                verification_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=8000,
                )
            )

            # Extract the verified/refined HTML
            verified_html = gemini_response.text

            print(f"  ✓ Gemini verified content ({len(verified_html)} characters)")

            # Create subject line
            subject = self._create_subject()

            return subject, verified_html

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
        """Create the prompt for Claude to format the screenings into a story"""
        week_str = f"{self.week_start.strftime('%B %d')} - {self.week_end.strftime('%B %d, %Y')}"

        return f"""You are creating a weekly email newsletter about special movie screenings in New York City.

Below is data about special screenings, premieres, Q&As, and repertory cinema happening this week ({week_str}) in Manhattan.

Your task is to format this data into a clean, minimal HTML email.

REQUIREMENTS:
1. Create a complete HTML email (including <!DOCTYPE>, <html>, <head>, <body> tags)
2. Use MINIMAL CSS styling:
   - White background (#ffffff)
   - Simple black/gray text colors (#000, #333, #666)
   - Sans-serif fonts for headlines (system fonts like -apple-system, "Segoe UI", Arial)
   - Serif fonts for body text (Georgia)
   - Clean typography inspired by The Atlantic magazine
   - NO emojis, NO bright colors, NO decorative elements
3. Organize screenings by theater with clear sections:
   - Focus on: Lincoln Center, Angelika Film Center, AMC (Lincoln Square/84th Street), and Paris Theater
   - Use theater names as section headings (h2)
4. For each screening, include only essential details:
   - Title (bold)
   - Director (if available, in italics)
   - Date and time
   - Special notes (Q&A, premiere, etc.) - keep concise
   - Brief description (only if significant)
   - Ticket info and link
5. Keep text CONCISE and straightforward - no flowery language
6. Include simple header: "NYC Special Screenings" and the week range
7. Minimal footer: "Automated weekly digest of special movie screenings in NYC"

SCREENING DATA:
{screenings_data}

Generate the complete HTML email now. Remember: minimal formatting, white background, simple colors, no emojis, concise text."""

    def _create_verification_prompt(self, claude_html: str, screenings_data: str) -> str:
        """Create the prompt for Gemini to verify Claude's output"""
        week_str = f"{self.week_start.strftime('%B %d')} - {self.week_end.strftime('%B %d, %Y')}"

        return f"""You are a quality assurance editor reviewing an HTML email newsletter about NYC movie screenings.

Below is an HTML email that was generated by another AI system, along with the original screening data it was based on.

Your task is to:
1. Verify that all important screening information from the source data is included
2. Check for any factual errors or hallucinated information
3. Ensure the HTML is well-formed and will render correctly
4. Verify that all links, dates, times, and details are accurate
5. Ensure the formatting is MINIMAL with white background and simple colors
6. Remove any emojis if present
7. If you find any issues, correct them

IMPORTANT:
- Do NOT remove any screenings unless they were hallucinated
- Do NOT add verbose or flowery language - keep it concise
- Do focus on factual accuracy and completeness
- Ensure simple, clean formatting (like The Atlantic magazine)
- Return the complete, corrected HTML email (including all HTML tags)

ORIGINAL SCREENING DATA:
{screenings_data}

GENERATED HTML EMAIL TO VERIFY:
{claude_html}

Please return the verified/corrected HTML email:"""

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
