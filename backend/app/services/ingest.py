import hashlib
import logging
import argparse
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.datetime_utils import utc_now
from app.db.database import SessionLocal
from app.models.article import Article
from app.models.source import Source
from app.models.category import Category
from app.services.news_provider import BaseNewsProvider, NewsAPIProvider, RawArticle
from app.services.rss_provider import RSSNewsProvider
from app.services.gnews_provider import GNewsProvider
from app.services.classifier import classify_region, classify_category, detect_indian_state
from app.services.story_grouping import assign_article_to_story_group

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("bharatlens.ingest")

# Regional language rotation schedule for GNews ingestion (keeps calls <= 1 req/cycle)
_regional_rotation_index = 0
ROTATING_REGIONAL_SCHEDULE = [
    {"state": "Telangana", "language": "te"},
    {"state": "Tamil Nadu", "language": "ta"},
    {"state": "Karnataka", "language": "kn"},
    {"state": "Kerala", "language": "ml"},
    {"state": "Maharashtra", "language": "mr"},
    {"state": "West Bengal", "language": "bn"},
    {"state": "Uttar Pradesh", "language": "hi"},
]



def compute_url_hash(url: str) -> str:
    """Compute SHA-256 hash of the normalized canonical URL."""
    normalized = url.strip().lower()
    # Strip tracking query parameters if present (e.g., utm_*)
    try:
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed = urlparse(normalized)
        query_params = parse_qs(parsed.query)
        filtered_params = {k: v for k, v in query_params.items() if not k.startswith("utm_")}
        new_query = urlencode(filtered_params, doseq=True)
        normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, ""))
    except Exception:
        pass
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_or_create_source(db: Session, name: str, domain: Optional[str] = None, country: str = "IN") -> Source:
    """Find existing Source by name or base_url, or create a new Source record."""
    clean_name = name.strip()
    source = db.query(Source).filter(Source.name.ilike(clean_name)).first()
    if not source and domain:
        source = db.query(Source).filter(Source.base_url == domain.strip().lower()).first()

    if not source:
        source = Source(
            name=clean_name,
            base_url=domain.strip().lower() if domain else f"https://{clean_name.lower().replace(' ', '')}.com",
            country=country,
        )
        db.add(source)
        db.flush()

    return source



def get_category_by_slug(db: Session, slug: str) -> Optional[Category]:
    """Retrieve category by slug."""
    return db.query(Category).filter(Category.slug == slug.lower()).first()


def ingest_raw_article(db: Session, raw: RawArticle) -> Optional[Article]:
    """Process, classify, validate, deduplicate, and persist a single raw article."""
    # 1. Validation
    if not raw.title or not raw.canonical_url:
        logger.warning("Skipping article with missing title or canonical URL.")
        return None

    clean_url = raw.canonical_url.strip()
    if not clean_url or clean_url.lower() in ["none", "null", ""]:
        logger.warning("Skipping article with null/empty canonical URL.")
        return None

    if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
        logger.warning(f"Skipping article with invalid canonical URL: {clean_url}")
        return None

    # 2. Duplicate Detection via SHA-256 URL Hash
    url_hash = compute_url_hash(clean_url)
    existing = db.query(Article).filter(
        (Article.url_hash == url_hash) | (Article.canonical_url == clean_url)
    ).first()
    if existing:
        logger.debug(f"Duplicate article skipped: {raw.title[:40]}...")
        return None

    # 3. Deterministic Region Classification
    region = classify_region(
        title=raw.title,
        description=raw.description,
        country_hint=raw.country_hint,
        source_name=raw.source_name,
    )

    # 4. Deterministic Category Classification
    cat_slug = classify_category(
        title=raw.title,
        description=raw.description,
        raw_category=raw.raw_category,
    )
    category = get_category_by_slug(db, cat_slug)
    if not category:
        category = get_category_by_slug(db, "politics")
        if not category:
            logger.error("No valid categories found in database. Run seed script first.")
            return None

    # 5. Deterministic State Detection (for Indian articles)
    state = raw.state_hint or detect_indian_state(
        title=raw.title,
        description=raw.description,
        region=region,
    )

    # 6. Resolve or Create Source
    source = get_or_create_source(
        db,
        name=raw.source_name,
        domain=raw.source_domain,
        country="IN" if region == "INDIA" else "GLOBAL",
    )

    # 7. Create Article Record
    article = Article(
        title=raw.title.strip(),
        description=(raw.description or raw.title).strip(),
        canonical_url=raw.canonical_url.strip(),
        url_hash=url_hash,
        source_id=source.id,
        category_id=category.id,
        region=region,
        state=state,
        language_code=raw.language_code or "en",
        image_url=raw.image_url,
        author=raw.author,
        published_at=raw.published_at,
        fetched_at=utc_now(),
        is_demo=False,
    )

    db.add(article)
    db.flush()

    # 8. Story Group Detection & Multi-Source Clustering (Resilient)
    try:
        assign_article_to_story_group(db, article)
    except Exception as e:
        logger.warning(f"Non-critical failure during story grouping for article '{article.title[:30]}': {e}")

    return article


def run_ingestion(
    db: Session,
    provider: Optional[BaseNewsProvider] = None,
    india_provider: Optional[BaseNewsProvider] = None,
    international_provider: Optional[BaseNewsProvider] = None,
    fetch_india: bool = True,
    fetch_international: bool = True,
    categories: Optional[list[str]] = None,
    state: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 20,
    provider_type: str = "all",
) -> Dict[str, Any]:
    """Execute complete ingestion pipeline with multi-provider resilience."""
    stats = {
        "fetched": 0,
        "saved": 0,
        "duplicates": 0,
        "errors": 0,
    }

    raw_articles: list[RawArticle] = []
    provider_errors: list[str] = []

    # Direct provider override (e.g. testing)
    if provider is not None:
        if state:
            logger.info(f"[*] Fetching Regional news ({state}, {language or 'en'}) via {type(provider).__name__}...")
            raw_articles.extend(provider.fetch_regional_news(state=state, language=language or "en", page_size=limit))
            if getattr(provider, "last_error", None):
                provider_errors.append(f"Regional ({type(provider).__name__}): {provider.last_error}")
        else:
            if fetch_india:
                logger.info(f"[*] Fetching India news via {type(provider).__name__} (limit={limit})...")
                if categories:
                    for cat in categories:
                        raw_articles.extend(provider.fetch_india_news(category=cat, page_size=limit))
                else:
                    raw_articles.extend(provider.fetch_india_news(page_size=limit))
                if getattr(provider, "last_error", None):
                    provider_errors.append(f"India ({type(provider).__name__}): {provider.last_error}")

            if fetch_international:
                logger.info(f"[*] Fetching International news via {type(provider).__name__} (limit={limit})...")
                if categories:
                    for cat in categories:
                        raw_articles.extend(provider.fetch_international_news(category=cat, page_size=limit))
                else:
                    raw_articles.extend(provider.fetch_international_news(page_size=limit))
                if getattr(provider, "last_error", None):
                    provider_errors.append(f"International ({type(provider).__name__}): {provider.last_error}")
    else:
        # If specific state is targeted
        if state:
            if provider_type in ["gnews", "all"]:
                gnews_key = getattr(settings, "GNEWS_API_KEY", None)
                if gnews_key:
                    gnews_prov = GNewsProvider()
                    logger.info(f"[*] Fetching Regional news for '{state}' (lang={language or 'en'}) via GNewsProvider...")
                    try:
                        raw_articles.extend(gnews_prov.fetch_regional_news(state=state, language=language or "en", page_size=limit))
                    except Exception as e:
                        logger.error(f"[!] Error running GNews Regional provider: {e}")
                    if getattr(gnews_prov, "last_error", None):
                        provider_errors.append(f"Regional (GNewsProvider): {gnews_prov.last_error}")

            if provider_type in ["rss", "all"]:
                rss_prov = RSSNewsProvider()
                try:
                    raw_articles.extend(rss_prov.fetch_regional_news(state=state, language=language or "en", page_size=limit))
                except Exception as e:
                    logger.error(f"[!] Error running RSS Regional provider: {e}")
        else:
            # Provider resolution based on provider_type
            if provider_type == "rss":
                rss_prov = india_provider or RSSNewsProvider()
                if fetch_india:
                    logger.info(f"[*] Fetching India news via {type(rss_prov).__name__} (limit={limit})...")
                    if categories:
                        for cat in categories:
                            raw_articles.extend(rss_prov.fetch_india_news(category=cat, page_size=limit))
                    else:
                        raw_articles.extend(rss_prov.fetch_india_news(page_size=limit))
                    if getattr(rss_prov, "last_error", None):
                        provider_errors.append(f"India ({type(rss_prov).__name__}): {rss_prov.last_error}")

            elif provider_type == "newsapi":
                napi_prov = india_provider or NewsAPIProvider()
                napi_intl = international_provider or NewsAPIProvider()
                if fetch_india:
                    logger.info(f"[*] Fetching India news via {type(napi_prov).__name__} (limit={limit})...")
                    if categories:
                        for cat in categories:
                            raw_articles.extend(napi_prov.fetch_india_news(category=cat, page_size=limit))
                    else:
                        raw_articles.extend(napi_prov.fetch_india_news(page_size=limit))
                    if getattr(napi_prov, "last_error", None):
                        provider_errors.append(f"India ({type(napi_prov).__name__}): {napi_prov.last_error}")

                if fetch_international:
                    logger.info(f"[*] Fetching International news via {type(napi_intl).__name__} (limit={limit})...")
                    if categories:
                        for cat in categories:
                            raw_articles.extend(napi_intl.fetch_international_news(category=cat, page_size=limit))
                    else:
                        raw_articles.extend(napi_intl.fetch_international_news(page_size=limit))
                    if getattr(napi_intl, "last_error", None):
                        provider_errors.append(f"International ({type(napi_intl).__name__}): {napi_intl.last_error}")

            elif provider_type == "gnews":
                gnews_prov = india_provider or GNewsProvider()
                gnews_intl = international_provider or GNewsProvider()
                if fetch_india:
                    logger.info(f"[*] Fetching India news via {type(gnews_prov).__name__} (limit={limit})...")
                    if categories:
                        for cat in categories:
                            raw_articles.extend(gnews_prov.fetch_india_news(category=cat, page_size=limit))
                    else:
                        raw_articles.extend(gnews_prov.fetch_india_news(page_size=limit))
                    if getattr(gnews_prov, "last_error", None):
                        provider_errors.append(f"India ({type(gnews_prov).__name__}): {gnews_prov.last_error}")

                if fetch_international:
                    logger.info(f"[*] Fetching International news via {type(gnews_intl).__name__} (limit={limit})...")
                    if categories:
                        for cat in categories:
                            raw_articles.extend(gnews_intl.fetch_international_news(category=cat, page_size=limit))
                    else:
                        raw_articles.extend(gnews_intl.fetch_international_news(page_size=limit))
                    if getattr(gnews_intl, "last_error", None):
                        provider_errors.append(f"International ({type(gnews_intl).__name__}): {gnews_intl.last_error}")

            else:  # "all" - Unified multi-provider ingestion
                # 1. Primary India Source: Indian Express RSS
                if fetch_india:
                    rss_prov = india_provider or RSSNewsProvider()
                    logger.info(f"[*] Ingesting India news via {type(rss_prov).__name__} (limit={limit})...")
                    try:
                        if categories:
                            for cat in categories:
                                raw_articles.extend(rss_prov.fetch_india_news(category=cat, page_size=limit))
                        else:
                            raw_articles.extend(rss_prov.fetch_india_news(page_size=limit))
                    except Exception as e:
                        logger.error(f"[!] Error running RSS provider: {e}")
                    if getattr(rss_prov, "last_error", None):
                        provider_errors.append(f"India ({type(rss_prov).__name__}): {rss_prov.last_error}")

                # 2. GNews Multi-Source (India + International + Rotating Regional)
                gnews_key = getattr(settings, "GNEWS_API_KEY", None)
                gnews_enabled = getattr(settings, "GNEWS_ENABLED", False) or bool(gnews_key)
                if gnews_enabled and gnews_key:
                    gnews_prov = GNewsProvider()
                    if fetch_india:
                        logger.info(f"[*] Ingesting India multi-source news via GNewsProvider (limit={min(limit, 10)})...")
                        try:
                            raw_articles.extend(gnews_prov.fetch_india_news(page_size=min(limit, 10)))
                        except Exception as e:
                            logger.error(f"[!] Error running GNews India provider: {e}")
                        if getattr(gnews_prov, "last_error", None):
                            provider_errors.append(f"India (GNewsProvider): {gnews_prov.last_error}")

                        # Rotating Regional News (keeps requests <= REGIONAL_NEWS_MAX_REQUESTS_PER_CYCLE)
                        if getattr(settings, "REGIONAL_NEWS_ENABLED", True) and getattr(settings, "REGIONAL_NEWS_LANGUAGES_ENABLED", True):
                            max_regional_reqs = max(0, getattr(settings, "REGIONAL_NEWS_MAX_REQUESTS_PER_CYCLE", 1))
                            for _ in range(max_regional_reqs):
                                target = ROTATING_REGIONAL_SCHEDULE[_regional_rotation_index % len(ROTATING_REGIONAL_SCHEDULE)]
                                _regional_rotation_index = (_regional_rotation_index + 1) % len(ROTATING_REGIONAL_SCHEDULE)
                                logger.info(f"[*] Ingesting Regional news ({target['state']}, lang={target['language']}) via GNewsProvider (limit={min(limit, 10)})...")
                                try:
                                    raw_articles.extend(gnews_prov.fetch_regional_news(state=target["state"], language=target["language"], page_size=min(limit, 10)))
                                except Exception as e:
                                    logger.error(f"[!] Error running GNews Regional provider for {target['state']}: {e}")
                                if getattr(gnews_prov, "last_error", None):
                                    provider_errors.append(f"Regional {target['state']} (GNewsProvider): {gnews_prov.last_error}")

                    if fetch_international:
                        logger.info(f"[*] Ingesting International news via GNewsProvider (limit={min(limit, 10)})...")
                        try:
                            raw_articles.extend(gnews_prov.fetch_international_news(page_size=min(limit, 10)))
                        except Exception as e:
                            logger.error(f"[!] Error running GNews International provider: {e}")
                        if getattr(gnews_prov, "last_error", None):
                            provider_errors.append(f"International (GNewsProvider): {gnews_prov.last_error}")

                # 3. NewsAPI International Source
                napi_key = getattr(settings, "NEWS_API_KEY", None)
                if fetch_international and napi_key:
                    napi_prov = international_provider or NewsAPIProvider()
                    logger.info(f"[*] Ingesting International news via {type(napi_prov).__name__} (limit={limit})...")
                    try:
                        if categories:
                            for cat in categories:
                                raw_articles.extend(napi_prov.fetch_international_news(category=cat, page_size=limit))
                        else:
                            raw_articles.extend(napi_prov.fetch_international_news(page_size=limit))
                    except Exception as e:
                        logger.error(f"[!] Error running NewsAPI provider: {e}")
                    if getattr(napi_prov, "last_error", None):
                        provider_errors.append(f"International ({type(napi_prov).__name__}): {napi_prov.last_error}")

    stats["fetched"] = len(raw_articles)
    logger.info(f"[*] Total raw articles fetched from providers: {stats['fetched']}")

    if provider_errors:
        stats["error"] = "; ".join(provider_errors)
        logger.warning(f"[*] Provider reports: {stats['error']}")

    for raw in raw_articles:
        try:
            article = ingest_raw_article(db, raw)
            if article:
                db.commit()
                stats["saved"] += 1
                logger.info(f"  + Saved [{article.region} | {article.state or 'National'} | {article.language_code}]: {article.title[:50]}...")
            else:
                stats["duplicates"] += 1
        except Exception as e:
            db.rollback()
            stats["errors"] += 1
            logger.error(f"  - Error saving article '{raw.title[:30]}': {e}")

    logger.info(
        f"[*] Ingestion complete: {stats['saved']} saved, {stats['duplicates']} duplicates skipped, {stats['errors']} errors."
    )
    return stats


def main():
    parser = argparse.ArgumentParser(description="BharatLens News Ingestion CLI")
    parser.add_argument("--provider", choices=["all", "rss", "newsapi", "gnews"], default="all", help="News provider to use (default: all)")
    parser.add_argument("--region", choices=["all", "india", "international"], default="all", help="Region scope to ingest")
    parser.add_argument("--category", type=str, help="Optional specific category slug")
    parser.add_argument("--state", type=str, help="Optional specific Indian state name (e.g. Telangana, Maharashtra)")
    parser.add_argument("--language", type=str, help="Optional language code (e.g. te, mr, hi, en)")
    parser.add_argument("--limit", type=int, default=20, help="Articles to fetch per request/feed")
    args = parser.parse_args()

    fetch_india = args.region in ["all", "india"]
    fetch_international = args.region in ["all", "international"]
    categories = [args.category] if args.category else None

    db = SessionLocal()
    try:
        stats = run_ingestion(
            db=db,
            provider_type=args.provider,
            fetch_india=fetch_india,
            fetch_international=fetch_international,
            categories=categories,
            state=args.state,
            language=args.language,
            limit=args.limit,
        )
        print("\n==================================================")
        print("       BharatLens Ingestion Summary Report        ")
        print("==================================================")
        print(f"Fetched:    {stats['fetched']}")
        print(f"Saved:      {stats['saved']}")
        print(f"Duplicates: {stats['duplicates']}")
        print(f"Errors:     {stats['errors']}")
        if stats.get("error"):
            print(f"Blocker:    {stats['error']}")
        print("==================================================\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()


