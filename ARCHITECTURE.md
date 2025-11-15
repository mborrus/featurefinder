# Newsletter Architecture

## Overview

The newsletter generation system uses a multi-step pipeline that separates data extraction (via LLMs) from presentation (via Python templates). This ensures consistent styling across all emails.

## Pipeline Flow

```
Scrapers → Aggregator → LLM (JSON) → Gemini (Verify) → Python Template → HTML Email
```

### Step 1: Data Collection

Multiple scrapers collect screening data from various sources:

**Priority 1 Sources (Highly Curated):**
- **The New Yorker** (`new_yorker.py`) - "Goings On About Town" film section, excellent curation
- **Metrograph** (`metrograph.py`) - Highly curated arthouse cinema
- **Film Forum** (`film_forum.py`) - Classic repertory and special screenings

**Priority 2 Sources (Aggregators):**
- **Screenslate** (`screenslate.py`) - NYC film screening aggregator
- **Time Out NYC** (`timeout_nyc.py`) - Film events and special screenings
- **IFC Center** (`ifc_center.py`) - Independent film center

**Priority 3 Sources (Community):**
- **Reddit** (`reddit.py`) - r/nyc and film-related subreddits

Data is aggregated and deduplicated by `ScreeningAggregator`

### Step 2: LLM Processing (`llm_formatter.py`)

1. **Claude API**: Receives raw screening data, outputs structured JSON
   - Temperature: 0.3 (factual, structured output)
   - Output format: JSON with theaters and screenings
   - **Curation Guidelines:**
     - Focus on notable, accessible screenings (not ultra avant garde)
     - Prioritize: Q&As, 70mm/IMAX, restorations, director appearances, classic revivals
     - Include mainstream repertory and important art films
     - Exclude: Highly experimental/underground, ultra-niche micro-cinema
     - Aim for 8-15 total screenings (curate down if too many)
   - **Key Theaters:**
     - Film at Lincoln Center
     - AMC Lincoln Square / AMC 84th Street
     - Paris Theater
     - Angelika Film Center
     - Metrograph, Film Forum, IFC Center

2. **Gemini API**: Verifies Claude's JSON output
   - Temperature: 0.1 (conservative verification)
   - Checks factual accuracy and completeness
   - Double-checks curation (removes avant garde, limits to 8-15 screenings)
   - Ensures concise, non-flowery language

### Step 3: Template Formatting (`email_formatter.py`)
- Converts JSON structure back to `Screening` objects
- Applies consistent HTML/CSS template
- Uses The Atlantic-inspired styling

## The Atlantic Styling Guide

### Typography
- **Headlines**: Georgia serif, 32px (h1), 20px (h2), 18px (titles)
- **Body text**: Georgia serif, 17px
- **Metadata**: Helvetica/Arial sans-serif, 13-14px
- **Line height**: 1.6 for readability

### Color Palette
- **Background**: White (#ffffff)
- **Primary text**: Near-black (#1a1a1a)
- **Body text**: Dark gray (#333333)
- **Metadata**: Medium gray (#767676, #666666)
- **Accent**: Atlantic red (#C74444)
- **Borders**: Light gray (#dddddd, #e5e5e5)
- **Footer**: Light gray (#999999)

### Layout Principles
- Clean, generous whitespace
- Single column (600px max width)
- Subtle 1px borders between sections
- Hierarchical content organization
- Minimal, elegant design
- High text-to-image ratio

## JSON Schema

```json
{
  "theaters": [
    {
      "name": "Theater Name",
      "screenings": [
        {
          "title": "Film Title",
          "director": "Director Name",
          "date_time": "November 20, 7:00 PM",
          "special_note": "Q&A with director",
          "description": "Brief description",
          "ticket_info": "$15",
          "url": "https://..."
        }
      ]
    }
  ]
}
```

## Key Benefits

1. **Consistent Styling**: Python templates ensure identical formatting every email
2. **Separation of Concerns**: LLM extracts/organizes data, template handles presentation
3. **Maintainability**: Easy to update styling in one place
4. **Quality Control**: Two-step LLM verification (Claude + Gemini)
5. **Flexibility**: Can easily switch between formatters or add new ones

## Files

- `llm_formatter.py`: LLM-based JSON extraction and verification
- `email_formatter.py`: HTML/CSS template with Atlantic styling
- `main.py`: Orchestrates the entire pipeline
- `scrapers/`: Data collection from various sources
- `aggregator.py`: Deduplication and grouping logic
