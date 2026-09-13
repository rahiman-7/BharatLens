# BharatLens Recommendation Engine (Phase 9)

## Overview
BharatLens provides an explainable, lightweight, content-based recommendation engine for personalized news under the "For You" tab.

## Principles & Design
1. **Explainable & Content-Based**: Recommendations are derived strictly from the user's own reading events (`view`, `read` with dwell duration) and bookmarks. No user-to-user collaborative filtering or opaque black-box deep learning models are used.
2. **Behavioral Privacy**: Users are not forced into onboarding questionnaires. Affinity is built organically through implicit engagement.
3. **Graceful Cold-Start**: If a user has fewer than 3 interactions, the system seamlessly falls back to a chronologically balanced feed of latest news across all categories. The page is never empty.
4. **Scoring Formula**:
   $$\text{Final Score} = (S_{\text{cat}} \times 0.70) + (S_{\text{fresh}} \times 0.30)$$
   where:
   - $S_{\text{cat}}$ = User category affinity computed via interaction weights with 7-day half-life recency decay: $w = e^{-\Delta t / 7.0}$
   - $S_{\text{fresh}}$ = Article publication freshness score with 72-hour half-life: $e^{-\Delta t_{\text{hours}} / 72.0}$
5. **Diversity & Deduplication**:
   - Recently read articles (within 7 days) are filtered out from the candidate pool.
   - A category diversity filter prevents more than 2 consecutive articles of the same category in the feed.

## Module Structure
- `profile.py`: Computes normalized category affinity distribution from user events and bookmarks.
- `scoring.py`: Calculates article freshness and combined recommendation scores.
- `service.py`: Handles candidate windowing, read-filtering, ranking, diversity re-ordering, cold-start fallback, and pagination.
