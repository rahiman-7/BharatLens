import re
from typing import Optional


def preprocess_text(title: Optional[str], description: Optional[str] = None) -> str:
    """Combines and cleans article title and description into a single normalized text.
    
    Handles:
    - Missing/None titles or descriptions
    - Extra whitespace and newlines
    - Safe lowercase normalization without removing critical domain vocabulary
    """
    safe_title = (title or "").strip()
    safe_desc = (description or "").strip()

    combined = f"{safe_title} {safe_desc}".strip()
    if not combined:
        return ""

    # Normalize multiple whitespace characters/newlines to a single space
    normalized = re.sub(r"\s+", " ", combined)
    return normalized.strip().lower()
