# 🧠 AIPulse — AI News Aggregation & Broadcasting Dashboard

> A production-quality MVP that aggregates AI news from top RSS sources, deduplicates articles, generates AI summaries via Groq, and simulates social broadcasting — all for **zero cost**.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?style=flat-square&logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-3-lightblue?style=flat-square&logo=sqlite)
![Docker](https://img.shields.io/badge/Docker-ready-blue?style=flat-square&logo=docker)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [API Reference](#-api-reference)
- [Groq Integration](#-groq-integration)
- [Docker Deployment](#-docker-deployment)
- [Render Deployment](#-render-deployment-free-tier)
- [Future Improvements](#-future-improvements)

---

## 🌟 Overview

AIPulse is a full-stack news aggregation dashboard focused on Artificial Intelligence topics. It:

1. **Fetches** AI news from 6 curated RSS sources every time you trigger a refresh
2. **Deduplicates** similar articles using `difflib.SequenceMatcher` (threshold = 0.8)
3. **Summarizes** articles using the Groq API (free tier, llama3-8b-8192)
4. **Displays** news in a clean dark-themed Bootstrap UI
5. **Broadcasts** articles to Email / LinkedIn / WhatsApp (simulated, DB-logged)

All infrastructure is **zero cost**: SQLite, FastAPI, Bootstrap CDN, Groq free tier, and Render free hosting.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📰 RSS Aggregation | 6 sources: MIT Tech Review, VentureBeat, The Verge, Wired, TechCrunch, AI News |
| 🧹 Deduplication | SequenceMatcher title comparison, threshold = 0.8 |
| ⭐ Favorites | Save/unsave articles, dedicated favorites page |
| 📣 Broadcast Simulation | Email, LinkedIn, WhatsApp — all simulated, logged in DB |
| 🤖 AI Summaries | Groq API (llama3-8b-8192) for article summaries + LinkedIn captions |
| 🔍 Source Filtering | Filter news by source with one click |
| 📄 Pagination | 20 articles per page, fully paginated |
| 📊 Broadcast Logs | Full audit trail of all simulated broadcasts |
| 🐳 Docker Ready | Single `docker-compose up` to run locally |
| ☁️ Render Ready | `render.yaml` config included for free tier deployment |

---

## 🛠 Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | FastAPI (Python) | Fast, async, auto-docs, simple routing |
| Database | SQLite + SQLAlchemy | Zero setup, file-based, ORM-managed |
| RSS Fetching | feedparser | Robust, handles malformed feeds |
| AI | Groq API (free tier) | Fast inference, generous free limits |
| HTTP Client | httpx | Async-compatible, used for Groq calls |
| Frontend | HTML + Bootstrap 5 | No build step, beginner-friendly |
| Templates | Jinja2 | Server-side rendering, built into FastAPI |
| Containerization | Docker + Compose | Reproducible builds, easy deployment |
| Hosting | Render free tier | 750 hrs/month, 512 MB RAM, persistent disk |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Browser (User)                      │
│         Bootstrap UI ← fetch() API calls → FastAPI       │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼─────────────────────────────┐
│                    FastAPI Backend                        │
│  ┌──────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │ /api/news│  │/api/favorites│  │ /api/broadcast   │   │
│  └────┬─────┘  └──────┬──────┘  └────────┬─────────┘   │
│       │               │                   │              │
│  ┌────▼───────────────▼───────────────────▼──────────┐  │
│  │              Services Layer                        │  │
│  │  news_fetcher.py │ deduplicator.py │ groq_service │  │
│  └────────────────────────┬───────────────────────────┘  │
│                           │                              │
│  ┌────────────────────────▼───────────────────────────┐  │
│  │           SQLite Database (SQLAlchemy ORM)          │  │
│  │  news_articles │ favorites │ broadcast_logs         │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │ RSS fetch (feedparser)     │ Groq API
    ┌────▼──────────────┐     ┌───────▼────────────┐
    │  6 RSS Sources    │     │  api.groq.com      │
    │  MIT, Verge, etc. │     │  llama3-8b-8192    │
    └───────────────────┘     └────────────────────┘
```

---

## 📁 Project Structure

```
ai-news-dashboard/
├── main.py                         # FastAPI app entry point
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── Dockerfile                      # Production Docker image
├── docker-compose.yml              # Local dev compose setup
├── render.yaml                     # Render.com deployment config
│
├── backend/
│   ├── __init__.py
│   ├── database.py                 # SQLAlchemy engine + session
│   ├── models.py                   # ORM models (NewsArticle, Favorite, BroadcastLog)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── news.py                 # GET /news, POST /news/fetch, POST /news/{id}/enrich
│   │   ├── favorites.py            # GET/POST/DELETE /favorites
│   │   └── broadcast.py            # POST /broadcast, GET /broadcast/logs
│   └── services/
│       ├── __init__.py
│       ├── news_fetcher.py         # feedparser RSS ingestion
│       ├── deduplicator.py         # difflib deduplication logic
│       └── groq_service.py         # Groq API calls (summary + caption)
│
└── frontend/
    ├── templates/
    │   ├── index.html              # News feed page
    │   ├── favorites.html          # Favorites page
    │   └── logs.html               # Broadcast logs page
    └── static/
        ├── css/
        │   └── style.css           # Dark editorial theme
        └── js/
            ├── main.js             # News feed logic
            ├── favorites.js        # Favorites logic
            └── logs.js             # Logs table logic
```

---

## 🚀 Quick Start

### Option 1: Local Python (recommended for development)

```bash
# 1. Clone the repository
git clone https://github.com/your-username/ai-news-dashboard.git
cd ai-news-dashboard

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY (optional but recommended)

# 5. Start the server
uvicorn main:app --reload --port 8000

# 6. Open in browser
# http://localhost:8000
```

### Option 2: Docker Compose

```bash
# 1. Clone and enter directory
git clone https://github.com/your-username/ai-news-dashboard.git
cd ai-news-dashboard

# 2. Create .env file
cp .env.example .env
# Edit GROQ_API_KEY in .env

# 3. Build and run
docker-compose up --build

# 4. Open http://localhost:8000
```

### Getting a Free Groq API Key

1. Visit [https://console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to API Keys → Create API Key
4. Copy the key into your `.env` file as `GROQ_API_KEY=your_key_here`

> **Note:** AI features (summarize, LinkedIn caption) are disabled gracefully if the key is not set. All other features work without it.

---

## 📡 API Reference

All endpoints are prefixed with `/api`. The full interactive docs are available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### News

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/news/` | Paginated list of articles. Params: `page`, `limit`, `source` |
| GET | `/api/news/{id}` | Single article by ID |
| POST | `/api/news/fetch` | Trigger RSS fetch + deduplication (runs in background) |
| POST | `/api/news/{id}/enrich` | Generate AI summary + LinkedIn caption via Groq |

### Favorites

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/favorites/` | List all favorited articles |
| POST | `/api/favorites/{id}` | Add article to favorites |
| DELETE | `/api/favorites/{id}` | Remove article from favorites |

### Broadcast

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/broadcast/` | Simulate broadcast. Body: `{"article_id": 1, "platform": "linkedin"}` |
| GET | `/api/broadcast/logs` | View last 100 broadcast logs |

### System

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check (used by Docker + Render) |

---

## 🤖 Groq Integration

Groq provides **free** LLM inference with generous rate limits.

**Model used**: `llama3-8b-8192` (fast, capable, free)

**Rate limits (free tier)**:
- 14,400 requests/day
- 30 requests/minute

**How enrichment works**:

```
User clicks "AI Summary" on a card
        ↓
POST /api/news/{id}/enrich
        ↓
groq_service.py → generate_summary(title, raw_summary)
groq_service.py → generate_linkedin_caption(title, ai_summary)
        ↓
Results saved to news_articles table (ai_summary, linkedin_caption)
        ↓
Returned to UI and displayed in a styled box
```

**Results are cached** — Groq is only called once per article. Subsequent enrich calls return the cached DB value instantly.

---

## 🐳 Docker Deployment

```bash
# Build image
docker build -t ai-news-dashboard .

# Run with environment variable
docker run -d \
  -p 8000:8000 \
  -v ai_news_data:/data \
  -e GROQ_API_KEY=your_key_here \
  --name ai-news-dashboard \
  ai-news-dashboard

# View logs
docker logs -f ai-news-dashboard

# Stop
docker stop ai-news-dashboard
```

---

## ☁️ Render Deployment (Free Tier)

Render free tier specs:
- **RAM**: 512 MB
- **CPU**: 0.1 shared
- **Hours**: 750/month (enough for always-on)
- **Disk**: 1 GB persistent (for SQLite)
- **Note**: Service sleeps after 15 minutes of inactivity; first request after sleep takes ~30s

### Steps:

1. Push your code to GitHub
2. Go to [https://render.com](https://render.com) → New → Web Service
3. Connect your GitHub repository
4. Render auto-detects `render.yaml` — click **Apply**
5. In Environment Variables, add `GROQ_API_KEY`
6. Click **Deploy**

Your app will be live at `https://your-app-name.onrender.com`

---

## 🔮 Future Improvements

| Feature | Complexity | Notes |
|---|---|---|
| Real email sending | Medium | SendGrid free tier (100 emails/day) |
| Real LinkedIn posting | High | LinkedIn OAuth + API approval required |
| Scheduled auto-fetch | Low | Add APScheduler or use Render cron jobs |
| Search functionality | Low | SQLite LIKE queries or FTS5 |
| Category tagging | Medium | Groq can classify articles by topic |
| User authentication | High | FastAPI-Users library |
| Multiple users | High | Replace SQLite with PostgreSQL |
| Read/unread tracking | Low | Add `is_read` boolean to NewsArticle |
| Mobile app | High | React Native or Flutter wrapper |
| Webhook notifications | Medium | POST to Slack/Discord on new articles |

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/) — the best Python web framework
- [Groq](https://groq.com/) — blazing fast free LLM inference
- [feedparser](https://feedparser.readthedocs.io/) — reliable RSS parsing
- [Bootstrap](https://getbootstrap.com/) — rapid UI development
- [Render](https://render.com/) — generous free hosting tier
