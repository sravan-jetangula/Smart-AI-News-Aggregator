"""
main.py - FastAPI application entry point.
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

load_dotenv()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# DB imports
from backend.database import engine, Base
from backend.models import NewsArticle, Favorite, BroadcastLog

# Routers
from backend.routes.news import router as news_router
from backend.routes.favorites import router as favorites_router
from backend.routes.broadcast import router as broadcast_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting AI News Dashboard...")

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ DB Error: {e}")
        raise e

    yield

    logger.info("🛑 Shutting down AI News Dashboard...")


app = FastAPI(
    title="AI News Dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(news_router, prefix="/api")
app.include_router(favorites_router, prefix="/api")
app.include_router(broadcast_router, prefix="/api")

# -------------------------------
# STATIC + TEMPLATES (SAFE FIX)
# -------------------------------
BASE_DIR = os.path.dirname(__file__)
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

static_dir = os.path.join(FRONTEND_DIR, "static")
templates_dir = os.path.join(FRONTEND_DIR, "templates")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    logger.warning("⚠️ Static folder not found")

if os.path.exists(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
else:
    templates = None
    logger.warning("⚠️ Templates folder not found")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    if templates:
        return templates.TemplateResponse("index.html", {"request": request})
    return {"message": "Frontend not available"}


@app.get("/favorites", response_class=HTMLResponse)
def favorites_page(request: Request):
    if templates:
        return templates.TemplateResponse("favorites.html", {"request": request})
    return {"message": "Frontend not available"}


@app.get("/logs", response_class=HTMLResponse)
def logs_page(request: Request):
    if templates:
        return templates.TemplateResponse("logs.html", {"request": request})
    return {"message": "Frontend not available"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
