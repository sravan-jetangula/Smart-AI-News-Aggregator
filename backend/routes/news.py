"""
routes/news.py - News feed API endpoints.

Endpoints:
  GET  /news           - Paginated list of non-duplicate articles
  GET  /news/{id}      - Single article detail
  POST /news/fetch     - Trigger manual RSS fetch + deduplication
  POST /news/{id}/enrich - Trigger Groq AI enrichment for one article
"""

from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.database import get_db
from backend.models import NewsArticle
from backend.services.news_fetcher import fetch_all_feeds, store_articles
from backend.services.deduplicator import run_deduplication
from backend.services.groq_service import enrich_article

router = APIRouter(prefix="/news", tags=["News"])


def article_to_dict(a: NewsArticle) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "summary": a.summary,
        "url": a.url,
        "source": a.source,
        "published_at": a.published_at.isoformat() if a.published_at else None,
        "fetched_at": a.fetched_at.isoformat() if a.fetched_at else None,
        "is_duplicate": a.is_duplicate,
        "ai_summary": a.ai_summary,
        "linkedin_caption": a.linkedin_caption,
        "is_favorited": len(a.favorites) > 0,
    }


@router.get("/", summary="List all non-duplicate news articles")
def list_news(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    source: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns paginated news articles.
    Excludes duplicates. Optionally filters by source name.
    """
    query = db.query(NewsArticle).filter(NewsArticle.is_duplicate == False)

    if source:
        query = query.filter(NewsArticle.source.ilike(f"%{source}%"))

    total = query.count()
    articles = (
        query.order_by(NewsArticle.published_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "articles": [article_to_dict(a) for a in articles]
    }


@router.get("/{article_id}", summary="Get single article by ID")
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article_to_dict(article)


@router.post("/fetch", summary="Manually trigger RSS fetch and deduplication")
def fetch_news(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Fetches latest articles from all RSS sources, stores new ones,
    and runs deduplication in the background.
    """
    def _fetch_and_dedup():
        articles = fetch_all_feeds()
        inserted = store_articles(db, articles)
        flagged = run_deduplication(db)
        return inserted, flagged

    background_tasks.add_task(_fetch_and_dedup)
    return {"message": "Fetch started in background. Refresh news feed in a few seconds."}


@router.post("/{article_id}/enrich", summary="Generate AI summary and LinkedIn caption")
def enrich_news(article_id: int, db: Session = Depends(get_db)):
    """
    Calls Groq API to generate AI summary and LinkedIn caption for a given article.
    Returns structured result including error details when Groq is unavailable.
    """
    result = enrich_article(db, article_id)

    if result.get("error") == "Article not found":
        raise HTTPException(status_code=404, detail="Article not found")

    # Always return 200 with full diagnostic info — let frontend decide how to display
    return {
        "success": result["success"],
        "message": "Enrichment complete" if result["success"] else "Enrichment failed",
        "error": result.get("error"),
        "ai_summary": result["ai_summary"],
        "linkedin_caption": result["linkedin_caption"],
    }
