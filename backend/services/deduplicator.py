"""
services/deduplicator.py - Title-based deduplication using difflib.SequenceMatcher.

Logic:
  1. Load all non-duplicate articles from DB ordered by date (newest first).
  2. For each article, compare its title against all previously seen titles.
  3. If similarity ratio >= THRESHOLD (0.8), mark it as duplicate.

This approach is O(n²) which is acceptable for MVP scale (<10,000 articles).
For larger datasets, consider MinHash / LSH.
"""

import logging
from difflib import SequenceMatcher
from typing import List

logger = logging.getLogger(__name__)

# Similarity threshold — articles with ratio >= this are flagged as duplicates
THRESHOLD = 0.8


def _similarity(a: str, b: str) -> float:
    """
    Returns a float in [0, 1] representing title similarity.
    Uses SequenceMatcher ratio which considers character-level overlap.
    Both titles are lowercased for case-insensitive comparison.
    """
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def run_deduplication(db) -> int:
    """
    Scans all active (non-duplicate) articles in the database and
    flags near-duplicate titles using SequenceMatcher.

    Returns the count of articles newly marked as duplicates.
    """
    from backend.models import NewsArticle

    # Fetch all articles that haven't been flagged yet
    articles = (
        db.query(NewsArticle)
        .filter(NewsArticle.is_duplicate == False)  # noqa: E712
        .order_by(NewsArticle.published_at.desc())
        .all()
    )

    seen_titles: List[str] = []  # Accumulates canonical titles
    flagged = 0

    for article in articles:
        title = article.title.strip()
        is_dup = False

        for seen in seen_titles:
            score = _similarity(title, seen)
            if score >= THRESHOLD:
                logger.debug(f"Duplicate found (score={score:.2f}): '{title}' ≈ '{seen}'")
                is_dup = True
                break

        if is_dup:
            article.is_duplicate = True
            flagged += 1
        else:
            seen_titles.append(title)

    db.commit()
    logger.info(f"Deduplication complete. Flagged {flagged} duplicates out of {len(articles)} articles.")
    return flagged
