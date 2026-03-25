"""
services/news_fetcher.py - RSS feed fetcher using feedparser.

Fetches AI-related news from 6 curated RSS sources, normalizes
the data into a consistent schema, and stores it in SQLite.
Duplicate detection is applied after insertion.
"""

import feedparser
import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Curated AI news RSS sources (all free/public)
# ─────────────────────────────────────────────
RSS_SOURCES = [
    {
        "name": "MIT Technology Review - AI",
        "url": "https://www.technologyreview.com/feed/"
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/"
    },
    {
        "name": "The Verge - AI",
        "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"
    },
    {
        "name": "Wired - AI",
        "url": "https://www.wired.com/feed/tag/ai/latest/rss"
    },
    {
        "name": "TechCrunch - AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/"
    },
    {
        "name": "AI News",
        "url": "https://www.artificialintelligence-news.com/feed/"
    },
]


def _parse_date(entry) -> Optional[datetime]:
    """
    Safely parse a date from a feedparser entry.
    Tries published_parsed first, then falls back to string parsing.
    """
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])
        if hasattr(entry, "published") and entry.published:
            return parsedate_to_datetime(entry.published).replace(tzinfo=None)
    except Exception:
        pass
    return datetime.utcnow()


def _clean_text(text: Optional[str], max_length: int = 1000) -> str:
    """Strip HTML tags, normalize whitespace, and truncate."""
    if not text:
        return ""
    import re
    text = re.sub(r"<[^>]+>", " ", text)      # Remove HTML tags
    text = re.sub(r"\s+", " ", text).strip()   # Collapse whitespace
    return text[:max_length]


def fetch_all_feeds() -> List[Dict]:
    """
    Iterates through all RSS_SOURCES, parses each feed with feedparser,
    and returns a flat list of normalized article dictionaries.

    Each dict contains:
      - title (str)
      - summary (str)
      - url (str)
      - source (str)
      - published_at (datetime)
    """
    articles = []

    for source in RSS_SOURCES:
        try:
            logger.info(f"Fetching feed: {source['name']}")
            feed = feedparser.parse(source["url"])

            if feed.bozo and not feed.entries:
                logger.warning(f"Feed parse error for {source['name']}: {feed.bozo_exception}")
                continue

            for entry in feed.entries[:20]:  # Limit 20 articles per source
                url = entry.get("link", "").strip()
                title = _clean_text(entry.get("title", ""), max_length=512)

                if not url or not title:
                    continue

                summary = _clean_text(
                    entry.get("summary", "") or entry.get("description", ""),
                    max_length=1000
                )

                articles.append({
                    "title": title,
                    "summary": summary,
                    "url": url,
                    "source": source["name"],
                    "published_at": _parse_date(entry),
                })

            logger.info(f"Fetched {len(feed.entries)} entries from {source['name']}")

        except Exception as e:
            logger.error(f"Failed to fetch {source['name']}: {e}")

    logger.info(f"Total raw articles fetched: {len(articles)}")
    return articles


def store_articles(db, articles: List[Dict]) -> int:
    """
    Stores normalized articles into SQLite via SQLAlchemy session.
    Skips articles whose URL already exists in the database.

    Returns the count of newly inserted articles.
    """
    from backend.models import NewsArticle

    inserted = 0
    for item in articles:
        # Skip if URL already exists
        exists = db.query(NewsArticle).filter(NewsArticle.url == item["url"]).first()
        if exists:
            continue

        article = NewsArticle(
            title=item["title"],
            summary=item["summary"],
            url=item["url"],
            source=item["source"],
            published_at=item["published_at"],
        )
        db.add(article)
        inserted += 1

    db.commit()
    logger.info(f"Inserted {inserted} new articles into the database.")
    return inserted
