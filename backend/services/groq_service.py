"""
services/groq_service.py - Groq API integration for AI-powered features.

Uses Groq's free tier to:
  1. Generate a concise 2-3 sentence summary of a news article.
  2. Generate a LinkedIn-style caption for social broadcasting.

Free tier limits:
  - 14,400 requests/day
  - 30 requests/minute
  - Rate limit is handled gracefully — returns None on failure.

Set GROQ_API_KEY in your .env file.
Models tried in order (fallback chain if one is deprecated):
  llama-3.1-8b-instant → llama3-8b-8192 → gemma2-9b-it
"""

import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Fallback model list — tried in order until one succeeds
GROQ_MODELS = [
    "llama-3.1-8b-instant",   # Fastest, newest recommended free model
    "llama3-8b-8192",          # Classic free model
    "gemma2-9b-it",            # Google Gemma fallback
]

# ⚠️  KEY FIX: Do NOT read os.getenv() at module level.
# If read at import time, the value is captured BEFORE dotenv loads the .env file.
# Always call os.getenv() inside functions so it's evaluated at call time.


def _get_api_key() -> str:
    """Read GROQ_API_KEY fresh from environment at call time."""
    return os.getenv("GROQ_API_KEY", "").strip()


def _call_groq(prompt: str, max_tokens: int = 200) -> Optional[str]:
    """
    Makes a single chat completion request to Groq API.
    Tries each model in GROQ_MODELS until one succeeds.
    Returns the response text, or None if all attempts fail.
    """
    api_key = _get_api_key()

    if not api_key:
        logger.warning(
            "GROQ_API_KEY is not set. "
            "Add it to your .env file: GROQ_API_KEY=gsk_..."
        )
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error = None
    for model in GROQ_MODELS:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        try:
            response = httpx.post(
                GROQ_API_URL, json=payload, headers=headers, timeout=20.0
            )
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"].strip()
            logger.info(f"Groq call succeeded with model: {model}")
            return text

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            body = e.response.text
            logger.warning(f"Groq model {model} returned HTTP {status}: {body[:200]}")

            # 401 = bad key — no point retrying other models
            if status == 401:
                logger.error(
                    "Groq API key is invalid (401 Unauthorized). "
                    "Check your GROQ_API_KEY in .env."
                )
                return None

            # 429 = rate limit — no point retrying other models immediately
            if status == 429:
                logger.error("Groq rate limit hit (429). Try again in a minute.")
                return None

            last_error = e

        except httpx.TimeoutException:
            logger.warning(f"Groq model {model} timed out. Trying next model...")
            last_error = "timeout"

        except Exception as e:
            logger.error(f"Groq API unexpected error with model {model}: {e}")
            last_error = e

    logger.error(f"All Groq models failed. Last error: {last_error}")
    return None


def generate_summary(title: str, raw_summary: str) -> Optional[str]:
    """
    Generates a clean 2-3 sentence AI summary of the news article.
    Uses the article title and raw RSS summary as context.
    """
    prompt = (
        f"You are a tech journalist. Summarize the following AI news article "
        f"in 2-3 clear, concise sentences. Do not add opinions.\n\n"
        f"Title: {title}\n"
        f"Content: {raw_summary[:600]}\n\n"
        f"Summary:"
    )
    return _call_groq(prompt, max_tokens=150)


def generate_linkedin_caption(title: str, summary: str) -> Optional[str]:
    """
    Generates an engaging LinkedIn-style post caption for the article.
    Includes relevant emojis and a professional tone.
    """
    prompt = (
        f"Write an engaging LinkedIn post caption (max 3 sentences) for this AI news article. "
        f"Use 1-2 relevant emojis, a professional tone, and end with a thought-provoking question "
        f"or call to action.\n\n"
        f"Title: {title}\n"
        f"Summary: {summary[:400]}\n\n"
        f"LinkedIn Caption:"
    )
    return _call_groq(prompt, max_tokens=120)


def check_api_key() -> dict:
    """
    Returns a dict describing the current API key status.
    Used by the /enrich endpoint to return helpful diagnostics.
    """
    key = _get_api_key()
    if not key:
        return {"ok": False, "reason": "GROQ_API_KEY is not set in your .env file."}
    if not key.startswith("gsk_"):
        return {"ok": False, "reason": f"GROQ_API_KEY looks malformed (got '{key[:8]}...'). It should start with 'gsk_'."}
    return {"ok": True, "reason": f"Key found: {key[:8]}...{key[-4:]}"}


def enrich_article(db, article_id: int) -> dict:
    """
    Fetches an article by ID, generates AI summary + LinkedIn caption,
    and saves them back to the database.

    Returns a result dict:
      { "success": bool, "ai_summary": str|None, "linkedin_caption": str|None, "error": str|None }
    """
    from backend.models import NewsArticle

    article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
    if not article:
        logger.warning(f"Article {article_id} not found for enrichment.")
        return {"success": False, "error": "Article not found", "ai_summary": None, "linkedin_caption": None}

    # Check API key first — give a helpful diagnostic immediately
    key_status = check_api_key()
    if not key_status["ok"]:
        return {
            "success": False,
            "error": key_status["reason"],
            "ai_summary": article.ai_summary,
            "linkedin_caption": article.linkedin_caption,
        }

    # Always re-attempt if ai_summary is missing (don't skip just because we tried before)
    if not article.ai_summary:
        logger.info(f"Generating AI summary for article {article_id}...")
        article.ai_summary = generate_summary(article.title, article.summary or "")

    if not article.linkedin_caption:
        logger.info(f"Generating LinkedIn caption for article {article_id}...")
        article.linkedin_caption = generate_linkedin_caption(
            article.title, article.ai_summary or article.summary or ""
        )

    db.commit()

    if not article.ai_summary:
        return {
            "success": False,
            "error": "Groq API call failed. Check backend logs for details (model error, rate limit, or network issue).",
            "ai_summary": None,
            "linkedin_caption": None,
        }

    return {
        "success": True,
        "error": None,
        "ai_summary": article.ai_summary,
        "linkedin_caption": article.linkedin_caption,
    }
