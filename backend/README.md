# BharatLens — Backend (FastAPI + SQLAlchemy + PostgreSQL / SQLite)

> **"News with a wider perspective — See India. See the World."**

The BharatLens backend is built with FastAPI, SQLAlchemy ORM, Pydantic v2 schemas, Alembic database migrations, an automated background news ingestion scheduler (APScheduler), a Historical News Archive engine, and database-powered full search.

---

## 🏗️ Architecture & Database Strategy
 
- **Current Deployment Database:** **SQLite with persistent cloud storage** (for single-instance deployment and local development).
- **Future Scale Target:** **PostgreSQL / Neon** (pre-configured schema for future horizontal multi-instance scale).
- **ORM & Compatibility:** All SQLAlchemy models, table relationships, foreign keys, timestamps, enums (`RegionType`), indexes, and unique constraints are designed to be 100% PostgreSQL and SQLite compatible.
- **Configurable:** Driven by standard `DATABASE_URL` environment variable via Pydantic Settings.

---

## 📁 Directory Structure

```text
backend/
├── alembic/                      # Alembic migration scripts and environment
│   ├── versions/                 # Individual migration revision files
│   │   └── 2f3a05526c9d_initial_schema.py
│   ├── env.py                    # Alembic env connecting to Base.metadata
│   └── script.py.mako
├── alembic.ini                   # Alembic configuration
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── health.py         # GET /api/v1/health (Includes Ingestion Telemetry)
│   │       ├── categories.py     # GET /api/v1/categories
│   │       ├── states.py         # GET /api/v1/states
│   │       ├── news.py           # GET /api/v1/news/...
│   │       ├── archive.py        # GET /api/v1/archive (Historical Date Time Machine)
│   │       └── search.py         # GET /api/v1/search (Database Full Search)
│   ├── core/
│   │   └── config.py             # Settings (CORS, DATABASE_URL, NEWS_API_KEY, SCHEDULER)
│   ├── db/
│   │   ├── base.py               # Declarative Base
│   │   └── database.py           # Engine & SessionLocal factory
│   ├── models/                   # SQLAlchemy ORM Models
│   │   ├── user.py               # User model
│   │   ├── source.py             # News publisher/source model
│   │   ├── category.py           # News category model
│   │   ├── article.py            # Article model with indexes & url_hash
│   │   ├── bookmark.py           # User bookmarks
│   │   └── reading_event.py      # User reading history for ML/personalization
│   ├── schemas/                  # Pydantic v2 Request/Response Schemas
│   │   ├── source.py
│   │   ├── category.py
│   │   └── article.py
│   ├── services/                 # Business Logic & News Ingestion Engine
│   │   ├── news_provider.py      # BaseNewsProvider & NewsAPIProvider
│   │   ├── classifier.py         # Deterministic Region, Category, and State Classifiers
│   │   ├── ingest.py             # Ingestion Pipeline & CLI Runner
│   │   └── scheduler.py          # APScheduler Background Service & Status Tracker
│   └── main.py                   # FastAPI Application entrypoint & Lifespan
├── tests/                        # Pytest Test Suite
│   ├── test_health.py
│   ├── test_categories.py
│   ├── test_news.py
│   ├── test_ingestion.py         # Ingestion, Deduplication, & Classifier tests
│   ├── test_scheduler.py         # Concurrency locking, lifecycle & error isolation
│   ├── test_archive.py           # Historical date boundary & facet tests
│   └── test_search.py            # Text search, case insensitivity, & facet tests
├── .env.example                  # Sample environment variables
├── requirements.txt              # Python dependencies
├── seed.py                       # Development seed script
└── README.md                     # Backend documentation
```

---

## 🏛️ Historical News Archive API (`GET /api/v1/archive`)

Allows exploring previously stored news snapshots based on publication calendar date (`published_at`).

### Supported Query Parameters:
* `date`: `YYYY-MM-DD` (e.g. `2026-09-05`) — Filters articles whose `published_at` falls strictly within that calendar day.
* `region`: `'INDIA'` or `'INTERNATIONAL'`
* `category`: Category slug (e.g. `'technology'`, `'business'`, `'politics'`)
* `state`: Indian state/UT (e.g. `'Telangana'`, `'Karnataka'`, `'Maharashtra'`)
* `page`: Integer (default 1)
* `limit`: Integer (default 20, max 100)

### Example Requests:
```http
GET /api/v1/archive?date=2026-09-05
GET /api/v1/archive?date=2026-09-05&region=india
GET /api/v1/archive?date=2026-09-05&category=technology&state=Telangana
```

---

## 🔍 Database-Powered Search API (`GET /api/v1/search`)

Searches across stored article headlines (`title`) and summaries (`description`) case-insensitively directly within the database.

### Supported Query Parameters:
* `q`: Search keyword or phrase (e.g. `'Semiconductor'`, `'ISRO'`, `'AI'`)
* `region`: `'INDIA'` or `'INTERNATIONAL'`
* `category`: Category slug
* `state`: Indian state name
* `date`: `YYYY-MM-DD`
* `page`: Integer (default 1)
* `limit`: Integer (default 20, max 100)

### Example Requests:
```http
GET /api/v1/search?q=ISRO
GET /api/v1/search?q=cricket&region=india
GET /api/v1/search?q=Semiconductor&category=technology&state=Gujarat
```

---

## 📰 Phase 10 — Story Grouping & "Wider Perspective"

Story Grouping identifies when multiple news publishers are covering substantially the **same news story/event** and clusters them into a single `StoryGroup`. This allows BharatLens users to explore how different domestic and international newsrooms report the same development.

### Key Architecture & Implementation Details:
* **Similarity Method**: TF-IDF Unigram Vectorization with Cosine Similarity (`backend/app/ml/similarity.py`). Preprocessing normalizes case, removes punctuation/numbers, and filters standard English stopwords.
* **Calibrated Similarity Threshold**: `STORY_GROUP_SIMILARITY_THRESHOLD = 0.55` (configurable via `.env` or `app.core.config.Settings`).
  * *Rationale*: In unigram bag-of-words similarity, different journalistic outlets covering the exact same event produce similarity scores between **0.55 and 0.80** due to differing headlines and phrasing (e.g. "Parliament Passes Landmark Digital Personal Data Protection Bill" vs "Digital Personal Data Protection Bill Passed by Indian Parliament" scores `0.6091`). A rigid 0.80 threshold only captures near-duplicate wire syndications (0.85–1.00) and misses multi-outlet coverage. Meanwhile, unrelated articles score `0.00–0.15` and different events within the same domain score `~0.10`.
* **Bounded Candidate Pool**: Compares incoming articles only against candidates published within the last **14 days** (`CANDIDATE_WINDOW_DAYS = 14`), avoiding $O(N^2)$ global comparisons.
* **Deterministic Representative Article**: The representative article for each `StoryGroup` is deterministically selected as the article with the **earliest valid `published_at` timestamp** (with lowest article ID as a deterministic fallback).
* **Ingestion Resilience**: Clustered during `ingest_raw_article`. If story grouping encounters an unexpected error, the failure is logged and the article is safely persisted without interrupting the ingestion pipeline.
* **Content-Based Similarity vs. LLM**: Story grouping uses deterministic, content-based TF-IDF cosine similarity. It does **NOT** use external LLMs, vector databases, or generative AI APIs.

### Story Group API Endpoints:
* `GET /api/v1/stories`: Paginated list of story clusters with representative headlines, article count, and distinct sources.
  * Query parameters: `page` (default 1), `limit` (default 10, max 50), `min_articles` (default 1).
* `GET /api/v1/stories/{story_id}`: Detailed coverage timeline of a story group, returning all grouped articles sorted deterministically by `published_at DESC`.
* `GET /api/v1/news/{article_id}/related`: Returns other articles in the same story group, strictly excluding the current article (`[]` if no peer coverage exists).

## 🛡️ Phase 11 — Product Hardening, Quality & Demo Readiness

Phase 11 transitions BharatLens from active feature development into a production-hardened, demo-ready college capstone project.

### Hardening Highlights:
* **End-to-End User Flow Testing (`tests/test_e2e_user_flows.py`)**:
  * **Flow A (Public Reader Flow)**: Unauthenticated complete journey across Home feed, India/International regional splits, category tabs, state filters, single article lookup with Wider Perspective related stories, free-text database search, archive date machine, and story clusters (`/api/v1/stories`).
  * **Flow B (Onboarding & Personalization Flow)**: End-to-end user lifecycle from registration, JWT login, `/auth/me` profile resolution, bookmark toggle (`POST /api/v1/bookmarks`), bookmark status inspection (`GET /api/v1/bookmarks/{article_id}/check`), bookmark listing (`GET /api/v1/bookmarks`), reading dwell events (`POST /api/v1/reading-events`), personalized TF-IDF recommendation feed calculation (`GET /api/v1/news/for-you`), and bookmark deletion.
  * **Flow C (Multi-Tenant Security & Access Control)**: Rigorous tenant isolation ensuring User A cannot see or delete User B's bookmarks; unauthenticated 401 enforcement across all protected routes (`/bookmarks`, `/news/for-you`, `/reading-events`, `/auth/me`); and malformed/expired JWT rejection.
* **Frontend Error Resilience**:
  * Dedicated editorial `NotFoundPage` catch-all (`*`) route for invalid URLs.
  * Resilient image error boundaries (`onError`) across `NewsCard`, `HeroStory`, and `ArticleDetailPage` with editorial gradient fallbacks and source monograms.
  * Accessible login and registration forms with explicit `htmlFor` and element IDs.
  * Automatic 401 token revocation in `client.ts` preventing stale authentication deadlocks.
* **Database & Concurrency Safety**:
  * Thread-safe APScheduler background runner with mutex isolation (`ingestion_lock`) preventing overlapping pipeline runs.
  * SHA-256 canonical URL hashing (`url_hash`) preventing duplicate article insertion.
  * Safe cascade deletions on User bookmarks and reading events with PostgreSQL-compatible schema.

---

## 🧪 Running Automated Tests

Run the complete 179-test Pytest test suite:
```bash
venv\Scripts\pytest -v
```
All 179 test cases pass cleanly with 0 failures, validating:
- Database connectivity and schema constraints
- Category and State ordering & filtering
- News pagination and single article lookups
- URL hash normalization and deduplication
- Deterministic region, category, and state classification
- APScheduler lifecycle, concurrency locking, and failure isolation
- Historical News Archive date boundary filters
- Full database search with multi-field matching
- ML TF-IDF text classification and content similarity
- Content-based personalized "For You" scoring and decay
- Phase 10 story grouping clustering and related coverage
- Phase 11 End-to-End multi-step user flows (Flow A, Flow B, Flow C)
- Phase 12 demo data isolation and regional language support


