"""
routes/broadcast.py - Simulated broadcast endpoints.

No real API calls are made. All broadcasts are logged in the DB
with status="simulated". This satisfies the MVP requirement while
providing a realistic logging and audit trail structure for future
real integrations (SendGrid, LinkedIn API, WhatsApp Business API).

Endpoints:
  POST /broadcast           - Simulate a broadcast
  GET  /broadcast/logs      - View broadcast history
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Literal

from backend.database import get_db
from backend.models import BroadcastLog, NewsArticle

router = APIRouter(prefix="/broadcast", tags=["Broadcast"])

SUPPORTED_PLATFORMS = {"email", "linkedin", "whatsapp"}


class BroadcastRequest(BaseModel):
    article_id: int
    platform: str  # "email", "linkedin", "whatsapp"


@router.post("/", summary="Simulate broadcasting an article to a platform")
def broadcast_article(req: BroadcastRequest, db: Session = Depends(get_db)):
    """
    Simulates sending an article to the selected platform.
    Logs the action in the broadcast_logs table.
    Returns a mock success response.
    """
    platform = req.platform.lower()
    if platform not in SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported platform. Choose from: {', '.join(SUPPORTED_PLATFORMS)}"
        )

    article = db.query(NewsArticle).filter(NewsArticle.id == req.article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Use LinkedIn caption if available; otherwise use summary
    caption = article.linkedin_caption or article.summary or article.title

    # Simulate platform-specific behavior
    mock_messages = {
        "email": f"📧 Email drafted with subject: '{article.title[:60]}...'",
        "linkedin": f"🔗 LinkedIn post queued with caption: '{caption[:80]}...'",
        "whatsapp": f"💬 WhatsApp message prepared: '{article.title[:60]}...'"
    }

    # Log the broadcast
    log = BroadcastLog(
        article_id=req.article_id,
        platform=platform,
        status="simulated",
        caption_used=caption[:500]
    )
    db.add(log)
    db.commit()

    return {
        "status": "simulated",
        "platform": platform,
        "article_id": req.article_id,
        "message": mock_messages[platform],
        "note": "This is a simulated broadcast. No real message was sent."
    }


@router.get("/logs", summary="View all broadcast logs")
def get_broadcast_logs(db: Session = Depends(get_db)):
    logs = db.query(BroadcastLog).order_by(BroadcastLog.broadcasted_at.desc()).limit(100).all()
    return {
        "total": len(logs),
        "logs": [
            {
                "id": log.id,
                "article_id": log.article_id,
                "article_title": log.article.title if log.article else "N/A",
                "platform": log.platform,
                "status": log.status,
                "broadcasted_at": log.broadcasted_at.isoformat(),
                "caption_used": log.caption_used,
            }
            for log in logs
        ]
    }
