"""
LLM-powered formatter for NYC movie screenings
Uses Claude API to generate structured JSON for email formatting
"""
import os
import json
from typing import List, Dict
from scrapers.base import Screening
from config import get_week_range
from anthropic import Anthropic


class LLMFormatter:
    """Uses Claude API to generate structured JSON for email formatting"""

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

    def format_with_llm(self, grouped_screenings: Dict[str, List[Screening]]) -> tuple:
        """
        Use Claude to generate structured JSON, then format with template

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

        print("  Calling Claude API to generate structured JSON...")

        try:
            # Call Claude API to generate JSON structure
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

            # Parse JSON and format with Python template
            print("  Formatting with HTML template...")

            import json
            from email_formatter import EmailFormatter

            # Parse Claude's JSON
            try:
                screening_data = json.loads(claude_json)
                print("  ✓ Successfully parsed JSON")
            except json.JSONDecodeError as e:
                print(f"  ✗ Claude's JSON is invalid: {e}")
                print(f"  ✗ JSON (first 500 chars): {claude_json[:500]}")
                raise

            formatter = EmailFormatter()

            # Validate and ensure priority theaters have screenings if available in source
            print("  Validating priority theater inclusion...")
            screening_data = self._validate_priority_theaters(screening_data, grouped_screenings)

            # Extract top highlights
            top_highlights = screening_data.get('top_highlights', [])

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
                        ticket_sale_date=screening_json.get('ticket_sale_date', ''),
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
            subject, html_body = formatter.format_email(formatted_screenings, top_highlights)

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

                if screening.ticket_sale_date:
                    screening_info.append(f"Tickets on sale: {screening.ticket_sale_date}")

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

Below is data about special screenings, premieres, Q&As, and repertory cinema happening in Manhattan.

**CRITICAL FOCUS**: This newsletter helps readers CATCH TICKETS BEFORE THEY SELL OUT. The main purpose is to alert readers when tickets are going on sale for upcoming screenings, not just when screenings are happening.

Your task is to organize this data into a clean JSON structure that will be used by a Python template to generate the HTML email.

CURATION GUIDELINES (IMPORTANT):
- **PRIMARY PRIORITY**: Screenings with tickets going on sale THIS WEEK or in the next 7-10 days
- Focus on screenings where timing is critical (limited tickets, advance sales, special events)
- EMPHASIZE when tickets become available, not just when the screening happens
- Example: If tickets for a big December screening go on sale November 18, that's TOP PRIORITY for a November 18 newsletter

- **HIGHEST PRIORITY FILMS - MAJOR FESTIVAL PREMIERS & OSCAR CONTENDERS**:
  * Films from CANNES (Palme d'Or winners, Grand Prix, etc.)
  * Films from VENICE (Golden Lion winners, Silver Lion, etc.)
  * Films from SUNDANCE, TELLURIDE, TORONTO (TIFF), NEW YORK FILM FESTIVAL (NYFF)
  * Films from BERLIN (Berlinale), SAN SEBASTIAN, LOCARNO, KARLOVY VARY
  * OSCAR CONTENDERS for current awards season (Best Picture, major categories)
  * Golden Globe nominees, BAFTA contenders, Critics Choice nominees
  * These prestigious films should ALWAYS be included, even if not at priority theaters
  * Examples of 2024-2025 season must-includes: Anora, The Brutalist, Conclave, The Substance, Emilia Pérez, Nickel Boys, A Real Pain, Sing Sing, Dune Part Two, Wicked, Nosferatu, Queer, Maria, All We Imagine As Light, The Piano Lesson, Babygirl, A Different Man, September 5, Didi, The Order, Flow
  * Examples of 2025-2026 season must-includes: Hamnet, One Battle After Another, Sinners, Marty Supreme, Sentimental Value, Bugonia, Frankenstein, Wicked: For Good

- Secondary priority: Q&As, director appearances, 70mm/IMAX, restorations, premieres, classic film revivals
- PREFER US films over foreign films when making curation decisions, UNLESS the foreign film is a major festival winner or Oscar contender
- Include mainstream repertory (Godfather, Casablanca, etc.) and important US/American cinema
- When including foreign films, prioritize festival winners and accessible classics over obscure art cinema
- EXCLUDE: Highly experimental/underground films, ultra-niche micro-cinema events (UNLESS they won major festival prizes)
- AIM FOR: 12-20 total screenings across all theaters
- MUST include screenings from Film at Lincoln Center, Angelika Film Center, and AMC theaters if they have ANY screenings available
- Each priority theater (Lincoln Center, Angelika, AMC) should have at least 2-3 screenings if available
- Film Forum is lower priority - only include their most notable screenings (1-2 max)
- If there are many similar screenings, keep only the most notable ones

REQUIREMENTS:
1. Output ONLY valid JSON (no markdown, no explanations, no HTML)
2. CREATE A "top_highlights" SECTION with exactly 4 of the most notable screenings
   - PRIORITIZE screenings where tickets go on sale soon (this week or next)
   - Include when tickets become available in the "why_notable" field
   - It's okay to repeat these in the theater sections later
3. Organize screenings by theater into separate sections
4. THEATER ORDERING - theaters MUST appear in this exact order:
   a) Film at Lincoln Center (or Lincoln Center variants)
   b) AMC Lincoln Square, AMC 84th Street (any AMC theaters)
   c) Angelika Film Center (or Angelika variants)
   d) Paris Theater
   e) Roxy Cinema
   f) All other theaters alphabetically
5. PRIORITY THEATERS - these theaters MUST always appear in the output (even if they have no screenings selected):
   - Film at Lincoln Center
   - AMC Lincoln Square (or any AMC theater)
   - Angelika Film Center
   - Paris Theater
   - Roxy Cinema
   If no screenings are selected for a priority theater, include it with an empty screenings array
6. Other theaters to include if they have notable screenings:
   - Metrograph
   - Film Forum
   - IFC Center
7. For each screening, extract and organize:
   - title (string)
   - director (string or null)
   - date_time (string - combined date and time of the SCREENING)
   - special_note (string or null - brief, e.g., "Q&A with director")
   - description (string or null - keep concise, 1-2 sentences max)
   - ticket_info (string or null)
   - ticket_sale_date (string or null - **CRITICAL**: ALWAYS include when tickets go on sale if available, e.g., "November 15", "Tuesday", "This Friday")
   - url (string or null - IMPORTANT: preserve all URLs from the source data)
8. Keep all text CONCISE and factual - no flowery language

JSON STRUCTURE:
{{
  "top_highlights": [
    {{
      "title": "Film Title",
      "theater": "Theater Name",
      "date_time": "November 20, 7:00 PM",
      "why_notable": "Tickets go on sale Tuesday, November 15 - 70mm IMAX presentation with Q&A"
    }}
  ],
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
          "ticket_sale_date": "November 15",
          "url": "https://..."
        }}
      ]
    }}
  ]
}}

SCREENING DATA:
{screenings_data}

Generate the JSON now. Output ONLY the JSON, nothing else:"""

    def _validate_priority_theaters(self, screening_data: dict, grouped_screenings: Dict[str, List[Screening]]) -> dict:
        """
        Validate that priority theaters with available screenings have at least some selected.
        If LLM excluded all screenings from a priority theater, add back the top 2-3.
        
        Args:
            screening_data: The JSON data returned by the LLM
            grouped_screenings: Original screening data by theater
            
        Returns:
            Updated screening_data with priority theaters properly included
        """
        # Define priority theaters (should match names in the grouped_screenings)
        priority_theaters = [
            'Film at Lincoln Center',
            'Angelika Film Center',
            'AMC Lincoln Square',
            'Paris Theater',
            'Roxy Cinema'
        ]
        
        # Helper function to find theater in grouped_screenings with fuzzy matching
        def find_source_theater(theater_name: str) -> tuple:
            """Find theater in source data, return (exact_name, screenings_list)"""
            # First try exact match
            if theater_name in grouped_screenings:
                return theater_name, grouped_screenings[theater_name]
            
            # Try case-insensitive partial match
            theater_lower = theater_name.lower()
            for source_name, screenings in grouped_screenings.items():
                source_lower = source_name.lower()
                # Match if either contains the other (e.g., "Lincoln Center" matches "Film at Lincoln Center")
                if theater_lower in source_lower or source_lower in theater_lower:
                    return source_name, screenings
            
            return None, []
        
        # Check each priority theater
        theaters_list = screening_data.get('theaters', [])
        
        for priority_name in priority_theaters:
            # Find if this theater exists in LLM output
            llm_theater = None
            for theater_section in theaters_list:
                if priority_name.lower() in theater_section['name'].lower() or \
                   theater_section['name'].lower() in priority_name.lower():
                    llm_theater = theater_section
                    break
            
            # Find source screenings for this theater
            source_name, source_screenings = find_source_theater(priority_name)
            
            # If theater has source screenings but LLM selected none (or very few), add some back
            if source_screenings and len(source_screenings) >= 2:
                llm_count = len(llm_theater.get('screenings', [])) if llm_theater else 0
                
                if llm_count < 2:  # Less than 2 screenings selected
                    print(f"  ⚠ {priority_name}: Found {len(source_screenings)} source screenings but only {llm_count} selected")
                    print(f"  → Adding top 3 screenings from {source_name}")
                    
                    # Convert top 3 source screenings to JSON format
                    added_screenings = []
                    for screening in source_screenings[:3]:  # Take top 3
                        screening_json = {
                            'title': screening.title,
                            'director': screening.director or None,
                            'date_time': f"{screening.date} {screening.time_slot}".strip() or "See website for times",
                            'special_note': screening.special_note or None,
                            'description': screening.description or None,
                            'ticket_info': screening.ticket_info or None,
                            'ticket_sale_date': screening.ticket_sale_date or None,
                            'url': screening.url or None
                        }
                        added_screenings.append(screening_json)
                    
                    # If theater exists in LLM output, update its screenings
                    if llm_theater:
                        llm_theater['screenings'] = added_screenings
                        print(f"  ✓ Updated {llm_theater['name']} with {len(added_screenings)} screenings")
                    else:
                        # Theater doesn't exist in output, add it
                        new_theater = {
                            'name': source_name,
                            'screenings': added_screenings
                        }
                        # Insert in the correct position based on priority order
                        # Find where to insert (after lower priority, before higher priority)
                        insert_pos = len(theaters_list)  # Default to end
                        for i, existing in enumerate(theaters_list):
                            # If we find a higher priority theater, insert before it
                            existing_name = existing['name']
                            if priority_theaters.index(priority_name) < len(priority_theaters):
                                # This is a bit tricky - for simplicity, just append
                                pass
                        theaters_list.append(new_theater)
                        print(f"  ✓ Added {source_name} with {len(added_screenings)} screenings")
                        
        return screening_data

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
