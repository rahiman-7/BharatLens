# BharatLens Story Grouping & Multi-Source Coverage (Phase 10)

## Overview
BharatLens features a content-based, multi-source **Story Grouping** engine that identifies when multiple news publishers are covering substantially the same news event and groups them together into cohesive story clusters.

This powers the core value proposition of BharatLens:
> **“News with a wider perspective — See how different sources cover the same story.”**

---

## 1. Design & Core Principles
- **Explainable & Content-Based**: Built on TF-IDF cosine similarity vectorization ([similarity.py](file:///c:/Users/rahim/OneDrive/Desktop/BharatLens/backend/app/ml/similarity.py)). No black-box LLMs, generative APIs, or vector databases.
- **Publisher Agnostic**: Clustered stories can span multiple distinct publishers (*The Hindu, Indian Express, NDTV, Reuters, BBC, etc.*) or handle near-duplicate updates from the same outlet.
- **Deterministic Representative Article**: For each `StoryGroup`, the representative article is deterministically selected as the article with the earliest publication timestamp (`min(published_at)`), with ID as a tie-breaker.
- **Bounded O(1) Candidate Window**: Newly ingested articles are compared only against candidate articles published within the past **14 days**.
- **Ingestion Resilience**: Story grouping executes as a non-blocking step during ingestion; any unforeseen anomaly is logged without dropping the saved article.

---

## 2. Similarity Metric & Thresholds
- **Algorithm**: TF-IDF token weighting with L2 normalized cosine similarity across article titles and descriptions.
- **Configurable Threshold**: `STORY_GROUP_SIMILARITY_THRESHOLD = 0.75`
- **Empirical Similarity Benchmarks**:
  - `1.0000`: Identical titles / duplicate press releases
  - `0.9000 - 0.9800`: Near-duplicates and updated wire reports
  - `0.7500 - 0.8900`: Multi-source coverage of the same underlying event
  - `< 0.4000`: Unrelated stories

---

## 3. Database Architecture
- **`story_groups` table**:
  - `id`: Primary key (Integer)
  - `representative_article_id`: Foreign key to `articles.id` (`ondelete="SET NULL"`)
  - `created_at`: Timestamp (UTC)
  - `updated_at`: Timestamp (UTC)
- **`articles` table**:
  - `story_group_id`: Foreign key to `story_groups.id` (`ondelete="SET NULL"`, indexed)

---

## 4. API Endpoints
- **`GET /api/v1/stories`**: Paginated story groups with representative headlines, source lists, and article counts.
- **`GET /api/v1/stories/{story_id}`**: Full multi-source coverage timeline for a specific story group.
- **`GET /api/v1/news/{article_id}/related`**: Peer articles covering the same story cluster (excluding the current article).
