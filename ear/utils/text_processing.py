"""Text processing utilities for EAR reports."""

import re
from typing import Optional


def strip_images_from_text(text: str) -> str:
    """Remove image references from markdown/HTML text."""
    if not text:
        return ""

    # Remove markdown images: ![alt](url)
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)

    # Remove HTML img tags: <img ... />
    text = re.sub(r'<img[^>]*>', '', text)

    # Remove extra whitespace/newlines left behind
    text = re.sub(r'\n\s*\n', '\n', text)
    text = text.strip()

    return text


def get_first_n_words(text: str, n: int = 10) -> str:
    """Extract first N words from text, removing images and markdown formatting."""
    if not text:
        return ""

    # Remove images first
    text = strip_images_from_text(text)

    # Remove markdown code blocks
    text = re.sub(r'```[^`]*```', '', text)
    text = re.sub(r'`[^`]*`', '', text)

    # Remove markdown links but keep the text: [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Remove markdown formatting: **bold**, *italic*, __bold__, _italic_
    text = re.sub(r'[*_]{1,2}([^*_]+)[*_]{1,2}', r'\1', text)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    # Split into words and take first N
    words = text.split()[:n]

    if not words:
        return ""

    result = ' '.join(words)

    # Add ellipsis if there are more words
    if len(text.split()) > n:
        result += '...'

    return result


def extract_name_from_odoo_tuple(field_value) -> Optional[str]:
    """
    Extract name from Odoo field value.
    Odoo returns many-to-one fields as tuples/lists: (id, name)

    Args:
        field_value: Can be tuple, list, int, str, or None

    Returns:
        String name or None
    """
    if not field_value:
        return None

    if isinstance(field_value, (list, tuple)) and len(field_value) >= 2:
        return str(field_value[1])

    if isinstance(field_value, (int, str)):
        return str(field_value)

    return None
