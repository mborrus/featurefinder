"""
Event Classifier for detecting and tagging special screening types

This module provides centralized logic for detecting what makes a screening special
based on keywords in the title, description, and other text fields.
"""
from typing import List, Set
import re


class EventClassifier:
    """Classifier for detecting special screening types and tagging them appropriately"""

    # Comprehensive keyword categories with all requested keywords
    KEYWORDS = {
        # Q&A and appearances
        'Q&A': ['q&a', 'q & a', 'q and a', 'question and answer', 'questions and answers'],
        'Director Appearance': [
            'with director', 'director in person', 'director present',
            'director appearance', 'director attending', 'director will be',
            'followed by director', 'introduced by director'
        ],
        'Filmmaker Appearance': [
            'filmmaker', 'filmmakers', 'with filmmaker', 'filmmaker in person',
            'filmmaker present', 'filmmaker appearance', 'filmmaker attending',
            'followed by filmmaker', 'introduced by filmmaker'
        ],
        'Special Guest': [
            'cast', 'actor', 'actress', 'producer', 'cinematographer',
            'in person', 'guest appearance', 'special guest', 'guests in attendance'
        ],

        # Premieres and special events
        'Premiere': [
            'premiere', 'world premiere', 'us premiere', 'nyc premiere',
            'new york premiere', 'theatrical premiere'
        ],
        'Opening Night': ['opening night', 'opening film', 'opens'],
        'Closing Night': ['closing night', 'closing film'],
        'Advance Screening': [
            'advance screening', 'early screening', 'early access',
            'pre-release', 'before release', 'first look'
        ],
        'Sneak Preview': [
            'sneak preview', 'sneak peek', 'preview screening',
            'special preview', 'advanced preview'
        ],

        # Film formats
        'IMAX': ['imax'],
        'Dolby': ['dolby', 'dolby cinema', 'dolby atmos', 'dolby vision'],
        '70mm': ['70mm', '70 mm'],
        '35mm': ['35mm', '35 mm'],
        '16mm': ['16mm', '16 mm'],

        # Restorations and special prints
        'Restoration': [
            'restoration', 'restored', 'newly restored', 'new restoration',
            '4k restoration', '4k', '2k restoration', 'remastered'
        ],
        'Anniversary': [
            'anniversary', 'th anniversary', 'year anniversary',
            'years later', 'celebrating', 'milestone'
        ],

        # Festival and series
        'Festival': [
            'festival', 'film festival', 'fest', 'nyff',
            'new york film festival', 'tribeca', 'sundance'
        ],
        'Special Series': [
            'series', 'retrospective', 'tribute', 'homage',
            'sidebar', 'special program', 'curated by'
        ],
        'Repertory': [
            'repertory', 'revival', 'classic screening', 'classics',
            'cult classic', 'midnight movie'
        ],

        # Special programming
        'Exclusive': ['exclusive', 'only at', 'exclusive engagement'],
        'Limited Release': ['limited release', 'limited engagement', 'limited run'],
        'Fan Event': [
            'fan event', 'fan screening', 'marathon', 'double feature',
            'triple feature', 'all night', 'all-night'
        ],
        'Special Event': [
            'special screening', 'special event', 'special presentation',
            'gala', 'benefit', 'fundraiser'
        ]
    }

    @classmethod
    def classify(cls, text: str, title: str = '', description: str = '') -> List[str]:
        """
        Classify a screening and return list of special event tags

        Args:
            text: Primary text to analyze (could be combined text)
            title: Film title (optional, for additional context)
            description: Description text (optional, for additional context)

        Returns:
            List of event type tags (e.g., ['Q&A', 'Director Appearance', '35mm'])
        """
        # Combine all text for analysis
        combined_text = f"{text} {title} {description}".lower()

        tags: Set[str] = set()

        # Check each category
        for tag_name, keywords in cls.KEYWORDS.items():
            if cls._has_keyword(combined_text, keywords):
                tags.add(tag_name)

        # Apply some logic to merge/prioritize tags
        tags = cls._refine_tags(tags, combined_text)

        # Return sorted list for consistency
        return sorted(list(tags))

    @classmethod
    def _has_keyword(cls, text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords"""
        return any(keyword in text for keyword in keywords)

    @classmethod
    def _refine_tags(cls, tags: Set[str], text: str) -> Set[str]:
        """
        Refine tags by applying logic to merge or prioritize certain combinations

        For example:
        - If we have both "Director Appearance" and "Filmmaker Appearance", keep both
        - If we have both "Premiere" and "Opening Night", keep both as they're distinct
        - If format is mentioned multiple times, keep all formats
        """
        refined = tags.copy()

        # If we detect both director and Q&A mentioned together, keep both
        # (This is already handled by separate detection, but we could add logic here)

        # Special case: if "with director" but also "filmmaker", keep both
        # (already handled)

        # Remove generic "Special Event" if we have more specific tags
        specific_event_tags = {
            'Q&A', 'Director Appearance', 'Filmmaker Appearance', 'Premiere',
            'Opening Night', 'Closing Night', 'Advance Screening', 'Sneak Preview',
            'Festival', 'Fan Event'
        }
        if 'Special Event' in refined and any(tag in refined for tag in specific_event_tags):
            refined.discard('Special Event')

        # If we have "Filmmaker Appearance" and "Director Appearance", keep both
        # (They might both be present)

        return refined

    @classmethod
    def format_tags(cls, tags: List[str]) -> str:
        """
        Format tags as pipe-separated string for special_note field

        Args:
            tags: List of event type tags

        Returns:
            Pipe-separated string (e.g., "Q&A | Director Appearance | 35mm")
        """
        return ' | '.join(tags) if tags else ''

    @classmethod
    def is_special(cls, text: str, title: str = '', description: str = '') -> bool:
        """
        Quick check if a screening has any special characteristics

        Args:
            text: Primary text to analyze
            title: Film title (optional)
            description: Description text (optional)

        Returns:
            True if any special keywords detected
        """
        tags = cls.classify(text, title, description)
        return len(tags) > 0

    @classmethod
    def get_all_keywords_flat(cls) -> List[str]:
        """
        Get a flat list of all keywords (useful for config)

        Returns:
            List of all unique keywords across all categories
        """
        all_keywords = []
        for keywords in cls.KEYWORDS.values():
            all_keywords.extend(keywords)
        # Remove duplicates and sort
        return sorted(list(set(all_keywords)))


# Convenience function for backward compatibility
def classify_screening(text: str, title: str = '', description: str = '') -> str:
    """
    Classify a screening and return formatted special note string

    Args:
        text: Primary text to analyze
        title: Film title (optional)
        description: Description text (optional)

    Returns:
        Pipe-separated string of tags (e.g., "Q&A | Director Appearance | 35mm")
    """
    classifier = EventClassifier()
    tags = classifier.classify(text, title, description)
    return classifier.format_tags(tags)
