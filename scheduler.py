"""
scheduler.py - Standalone script to fetch and deduplicate news.

Run this manually or set up a cron job:
  # Every 6 hours:
  0 */6 * * * cd /path/to/project && /path/to/venv/bin/python scheduler.py

Or on Render, add a Cron Job service that calls:
  python scheduler.py

This does NOT require the FastAPI server to be running.
"""

import sys
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("=== AIPulse Scheduler: Starting news fetch ===")

    # Initialize DB
    from backend.database import engine, SessionLocal, Base
    from backend.models import NewsArticle, Favorite, BroadcastLog  # noqa: F401
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        from backend.services.news_fetcher import fetch_all_feeds, store_articles
        from backend.services.deduplicator import run_deduplication

        # Fetch
        articles = fetch_all_feeds()
        logger.info(f"Fetched {len(articles)} raw articles from RSS feeds.")

        # Store
        inserted = store_articles(db, articles)
        logger.info(f"Inserted {inserted} new articles into the database.")

        # Deduplicate
        flagged = run_deduplication(db)
        logger.info(f"Deduplication complete. Flagged {flagged} duplicates.")

        logger.info("=== Scheduler run complete ===")

    except Exception as e:
        logger.error(f"Scheduler failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
