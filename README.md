# BharatLens — "News with a wider perspective"

> **"See India. See the World."**
> A modern, full-stack, AI/ML-enhanced news aggregation, clustering, and personalized reading platform.

---

## 🌟 Overview

BharatLens is an intelligent news platform designed to bridge domestic reporting across Indian states with global perspectives from international journalism. It aggregates, classifies, clusters, and personalizes news coverage without relying on expensive or black-box external LLM APIs.

### Core Architecture Highlights
- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite, Lucide icons, responsive mobile-first UI with dark/light themes.
- **Backend**: FastAPI, SQLAlchemy ORM, Pydantic v2 schemas, Alembic database migrations, SQLite (with persistent volume; PostgreSQL supported for future upgrade).
- **ML / NLP Engine**: Deterministic TF-IDF cosine similarity, keyword-assisted rule-based text classification, and time-decayed user profile vectors for personalized "For You" recommendations.
- **Story Grouping ("Wider Perspective")**: Automatic event-level clustering of multi-outlet reporting on the same story, enabling multi-angle coverage comparison.
- **Automated Ingestion**: APScheduler background engine with thread-safe mutex locks and SHA-256 canonical URL deduplication.
- **Historical Archive & Search**: Calendar date-bounded historical time machine and full database search.
- **Security & Multi-Tenancy**: JWT (HS256) bearer authentication, bcrypt password hashing, and strict multi-tenant data isolation.

---

## 🚀 Quick Start Guide

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate Python virtual environment
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
copy .env.example .env

# Seed development database
python seed.py

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

FastAPI server runs at `http://localhost:8000`  
Swagger / OpenAPI Docs: `http://localhost:8000/docs`  
Health & Telemetry Endpoint: `http://localhost:8000/api/v1/health`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```

Frontend application runs at `http://localhost:5173`.

---

## 🧪 Testing & Verification

### Backend Automated Test Suite (179 Tests)
```bash
cd backend
venv\Scripts\pytest -v
```
- **179 passed, 0 failed** across all 16 test domains (Archive, Auth, Bookmarks, Categories, E2E user flows, GNews provider, Health, Ingestion, ML Classifier & Similarity, News endpoints, Phase 11 hardening, Reading dwell events, Recommendations / "For You", Regional Indian languages, RSS provider & demo isolation, APScheduler & concurrency locking, Search, and Story grouping).

### Frontend Production Build
```bash
cd frontend
cmd.exe /c npm run build
```
- **0 errors**: TypeScript verification (`tsc -b`) and Vite production bundle generated cleanly.

---

## 🚢 Production Deployment Guide

BharatLens is designed for a modular, serverless-ready cloud deployment:

| Tier | Provider | Configuration / Build Command | Runtime / Start Command |
| :--- | :--- | :--- | :--- |
| **Frontend** | **Vercel** | **Build:** `npm run build`<br>**Output:** `dist`<br>**Env:** `VITE_API_BASE_URL=https://<your-render-backend>.onrender.com/api/v1` | Static SPA CDN (handled via `frontend/vercel.json` rewrites) |
| **Backend & Scheduler** | **Render Web Service** | **Build:** `pip install -r requirements.txt && alembic upgrade head`<br>**Disk Mount:** `/var/data` (1 GB)<br>**Env:** `DATABASE_URL=sqlite:////var/data/bharatlens.db`, `ENABLE_NEWS_SCHEDULER=true`, `NEWS_INGEST_INTERVAL_MINUTES=60`, `NEWS_INGEST_ON_STARTUP=false`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, `NEWS_API_KEY`, `GNEWS_API_KEY` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT`<br>**Health Check:** `/api/v1/health` |
| **Database** | **Render Persistent Disk** | Persistent Volume mounted at `/var/data/bharatlens.db` attached directly to the Web Service container. *(PostgreSQL/Neon remains configured for future multi-instance scale)* | Single-instance SQLite with WAL mode & busy timeout |

> [!IMPORTANT]
> **Production Deployment Architecture:**
> BharatLens runs as a unified single-instance FastAPI Web Service on Render with a Persistent Disk mounted at `/var/data`. Automated news ingestion runs in-process via **APScheduler** (`ENABLE_NEWS_SCHEDULER=true`, `NEWS_INGEST_ON_STARTUP=false`), protected by thread-safe mutex locks and exposed via `/api/v1/health` telemetry. Zero separate cron services are required.

---

## 🎬 College Demo Walkthrough Script

1. **Editorial Homepage (`/`)**:
   - Show hero banner with top headlines.
   - Toggle between **All Stories**, **India**, and **International** lenses.
   - Point out broken image resilience (graceful editorial monograms/gradients).
2. **"Wider Perspective" Story Groups (`/stories` & `/news/:id`)**:
   - Open a grouped story showing multi-outlet coverage of the same event.
   - Click an article to view detail page; inspect "Wider Perspective" related stories from peer newsrooms.
3. **Historical Archive (`/archive`)**:
   - Demonstrate the simplified 3-control layout (`[ Today ]`, `[ Yesterday ]`, `[ 📅 Choose a date ]`).
   - Filter previously collected news across dates, categories, states, and regional languages.
4. **Regional Indian Languages (`/state/:stateSlug` & Top Navigation)**:
   - Browse regional news in native Indian scripts (Telugu, Tamil, Kannada, Malayalam, Marathi, Bengali, Hindi).
5. **Live Search (`/search`)**:
   - Search for keywords (e.g. "Space", "AI", "Economy") across headlines and descriptions.
6. **User Onboarding & Personalization (`/register` & `/login`)**:
   - Register a new reader account or log in with demo accounts.
   - Read and bookmark articles across specific categories.
   - Visit the **"For You"** feed to demonstrate live TF-IDF content-based recommendation scoring tailored to reading dwell history.

