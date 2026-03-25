"""
models.py - SQLAlchemy ORM models for all database tables.

Tables:
  - NewsArticle: Stores fetched and normalized news items
  - Favorite: Tracks user-favorited articles
  - BroadcastLog: Logs simulated broadcast actions
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class NewsArticle(Base):
    """
    Stores normalized news articles fetched from RSS feeds.
    `is_duplicate` is flagged by the deduplication service.
    `ai_summary` and `linkedin_caption` are filled by Groq API.
    """
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    summary = Column(Text, nullable=True)
    url = Column(String(1024), unique=True, nullable=False)
    source = Column(String(256), nullable=True)
    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    is_duplicate = Column(Boolean, default=False)
    ai_summary = Column(Text, nullable=True)
    linkedin_caption = Column(Text, nullable=True)

    # Relationships
    favorites = relationship("Favorite", back_populates="article", cascade="all, delete")
    broadcasts = relationship("BroadcastLog", back_populates="article", cascade="all, delete")


class Favorite(Base):
    """
    Tracks articles marked as favorites by the user.
    One article can only be favorited once (unique constraint on article_id).
    """
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id"), unique=True, nullable=False)
    favorited_at = Column(DateTime, default=datetime.utcnow)

    article = relationship("NewsArticle", back_populates="favorites")


class BroadcastLog(Base):
    """
    Simulated broadcast logs — no real API calls are made.
    Records platform, status, and timestamp for each broadcast attempt.
    """
    __tablename__ = "broadcast_logs"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("news_articles.id"), nullable=False)
    platform = Column(String(64), nullable=False)   # "email", "linkedin", "whatsapp"
    status = Column(String(32), default="simulated") # always "simulated" in MVP
    broadcasted_at = Column(DateTime, default=datetime.utcnow)
    caption_used = Column(Text, nullable=True)

    article = relationship("NewsArticle", back_populates="broadcasts")
