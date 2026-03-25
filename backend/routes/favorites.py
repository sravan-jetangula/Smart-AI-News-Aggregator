"""
routes/favorites.py - Favorites management endpoints.

Endpoints:
  POST /favorite/{article_id}   - Add article to favorites
  DELETE /favorite/{article_id} - Remove from favorites
  GET  /favorites               - List all favorited articles
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Favorite, NewsArticle

router = APIRouter(prefix="/favorites", tags=["Favorites"])


def article_to_dict(a: NewsArticle) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "summary": a.summary,
        "url": a.url,
        "source": a.source,
        "published_at": a.published_at.isoformat() if a.published_at else None,
        "ai_summary": a.ai_summary,
        "linkedin_caption": a.linkedin_caption,
    }


@router.get("/", summary="List all favorited articles")
def list_favorites(db: Session = Depends(get_db)):
    favorites = db.query(Favorite).order_by(Favorite.favorited_at.desc()).all()
    return {
        "total": len(favorites),
        "articles": [article_to_dict(f.article) for f in favorites]
    }


@router.post("/{article_id}", summary="Add article to favorites")
def add_favorite(article_id: int, db: Session = Depends(get_db)):
    # Verify article exists
    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Check already favorited
    existing = db.query(Favorite).filter(Favorite.article_id == article_id).first()
    if existing:
        return {"message": "Already in favorites", "article_id": article_id}

    favorite = Favorite(article_id=article_id)
    db.add(favorite)
    db.commit()
    return {"message": "Added to favorites", "article_id": article_id}


@router.delete("/{article_id}", summary="Remove article from favorites")
def remove_favorite(article_id: int, db: Session = Depends(get_db)):
    favorite = db.query(Favorite).filter(Favorite.article_id == article_id).first()
    if not favorite:
        raise HTTPException(status_code=404, detail="Not in favorites")

    db.delete(favorite)
    db.commit()
    return {"message": "Removed from favorites", "article_id": article_id}
