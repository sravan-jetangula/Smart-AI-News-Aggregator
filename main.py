"""
main.py - FastAPI application entry point.

Initializes the app, registers all routers, creates DB tables on startup,
and serves the frontend static files + HTML templates.

Run locally:
  uvicorn main:app --reload --port 8000
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Import database and models
from backend.database import engine, Base
from backend.models import NewsArticle, Favorite, BroadcastLog  # noqa: F401 — needed for table creation

# Import routers
from backend.routes.news import router as news_router
from backend.routes.favorites import router as favorites_router
from backend.routes.broadcast import router as broadcast_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: Create all database tables if they don't exist.
    Shutdown: Log graceful shutdown.
    """
    logger.info("Starting AI News Dashboard...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized.")
    yield
    logger.info("Shutting down AI News Dashboard.")


# ─────────────────────────────────────────────
# Create FastAPI app instance
# ─────────────────────────────────────────────
app = FastAPI(
    title="AI News Aggregation & Broadcasting Dashboard",
    description="Aggregates AI news from RSS feeds, deduplicates, summarizes with Groq, and simulates broadcasting.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow all origins for development (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Register API routers
# ─────────────────────────────────────────────
app.include_router(news_router, prefix="/api")
app.include_router(favorites_router, prefix="/api")
app.include_router(broadcast_router, prefix="/api")

# ─────────────────────────────────────────────
# Static files and templates
# ─────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")

app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(FRONTEND_DIR, "templates"))


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    """Serve the main news dashboard page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/favorites", response_class=HTMLResponse, include_in_schema=False)
def favorites_page(request: Request):
    """Serve the favorites page."""
    return templates.TemplateResponse("favorites.html", {"request": request})


@app.get("/logs", response_class=HTMLResponse, include_in_schema=False)
def logs_page(request: Request):
    """Serve the broadcast logs page."""
    return templates.TemplateResponse("logs.html", {"request": request})


@app.get("/health")
def health_check():
    """Health check endpoint for Render and Docker healthchecks."""
    return {"status": "ok", "service": "AI News Dashboard"}
