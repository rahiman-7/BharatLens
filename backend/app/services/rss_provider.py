import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
import feedparser

from app.core.datetime_utils import utc_now
from app.services.news_provider import BaseNewsProvider, RawArticle

logger = logging.getLogger("bharatlens.rss_provider")

# Official Indian Express RSS Feeds configuration
INDIAN_EXPRESS_FEEDS: List[Dict[str, Any]] = [
    {
        "name": "Indian Express India",
        "url": "https://indianexpress.com/section/india/feed/",
        "category_hint": "politics",
        "state_hint": None,
    },
    {
        "name": "Indian Express Politics",
        "url": "https://indianexpress.com/section/politics/feed/",
        "category_hint": "politics",
        "state_hint": None,
    },
    {
        "name": "Indian Express Business",
        "url": "https://indianexpress.com/section/business/feed/",
        "category_hint": "business",
        "state_hint": None,
    },
    {
        "name": "Indian Express Technology",
        "url": "https://indianexpress.com/section/technology/feed/",
        "category_hint": "technology",
        "state_hint": None,
    },
    {
        "name": "Indian Express Sports",
        "url": "https://indianexpress.com/section/sports/feed/",
        "category_hint": "sports",
        "state_hint": None,
    },
    {
        "name": "Indian Express Entertainment",
        "url": "https://indianexpress.com/section/entertainment/feed/",
        "category_hint": "movies-entertainment",
        "state_hint": None,
    },
    {
        "name": "Indian Express Education",
        "url": "https://indianexpress.com/section/education/feed/",
        "category_hint": "education",
        "state_hint": None,
    },
    {
        "name": "Indian Express Science",
        "url": "https://indianexpress.com/section/technology/science/feed/",
        "category_hint": "science",
        "state_hint": None,
    },
    {
        "name": "Indian Express Hyderabad",
        "url": "https://indianexpress.com/section/cities/hyderabad/feed/",
        "category_hint": None,  # Classified by article content / ML
        "state_hint": "Telangana",
    },
]


class RSSNewsProvider(BaseNewsProvider):
    """RSS News Provider for India-focused publishers (initially Indian Express).
    
    Adheres strictly to the BaseNewsProvider interface and returns standard RawArticle
    records without scraping HTML or downloading full article texts.
    """

    def __init__(self, feeds: Optional[List[Dict[str, Any]]] = None, timeout: float = 10.0):
        super().__init__()
        self.feeds = feeds if feeds is not None else INDIAN_EXPRESS_FEEDS
        self.timeout = timeout

    def _extract_image(self, entry: Any) -> Optional[str]:
        """Safely extract image URL from standard RSS entry metadata."""
        def is_valid_img_url(u: Optional[str]) -> bool:
            if not u or not isinstance(u, str):
                return False
            clean_u = u.strip()
            return clean_u.startswith("http://") or clean_u.startswith("https://")

        # 1. Media content (Yahoo Media RSS extension)
        media_content = entry.get("media_content")
        if media_content:
            if isinstance(media_content, list) and len(media_content) > 0:
                for item in media_content:
                    url = item.get("url") if isinstance(item, dict) else None
                    if is_valid_img_url(url):
                        return str(url).strip()
            elif isinstance(media_content, dict):
                url = media_content.get("url")
                if is_valid_img_url(url):
                    return str(url).strip()

        # 2. Media thumbnail
        media_thumbnail = entry.get("media_thumbnail")
        if media_thumbnail:
            if isinstance(media_thumbnail, list) and len(media_thumbnail) > 0:
                for item in media_thumbnail:
                    url = item.get("url") if isinstance(item, dict) else None
                    if is_valid_img_url(url):
                        return str(url).strip()
            elif isinstance(media_thumbnail, dict):
                url = media_thumbnail.get("url")
                if is_valid_img_url(url):
                    return str(url).strip()

        # 3. Enclosures
        enclosures = entry.get("enclosures")
        if enclosures and isinstance(enclosures, list) and len(enclosures) > 0:
            for enc in enclosures:
                if isinstance(enc, dict):
                    href = enc.get("href") or enc.get("url")
                    enc_type = enc.get("type", "")
                    if is_valid_img_url(href) and (enc_type.startswith("image/") or not enc_type):
                        return str(href).strip()

        # 4. Links with image mime types or image extensions
        links = entry.get("links")
        if links and isinstance(links, list):
            for link in links:
                if isinstance(link, dict):
                    href = link.get("href")
                    link_type = link.get("type", "")
                    if is_valid_img_url(href):
                        if link_type.startswith("image/") or any(href.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp", ".avif"]):
                            return str(href).strip()

        # 5. Image dict or direct field
        img = entry.get("image")
        if isinstance(img, dict):
            url = img.get("href") or img.get("url")
            if is_valid_img_url(url):
                return str(url).strip()
        elif is_valid_img_url(img):
            return str(img).strip()

        # 6. Specific RSS publisher image tags (e.g. storyimage)
        story_img = entry.get("storyimage") or entry.get("featured_image")
        if is_valid_img_url(story_img):
            return str(story_img).strip()

        return None

    def _parse_entry(self, entry: Any, feed_config: Dict[str, Any]) -> Optional[RawArticle]:
        """Convert a feedparser entry into a standardized RawArticle."""
        try:
            title = (entry.get("title") or "").strip()
            url = (entry.get("link") or "").strip()

            if not title or not url:
                return None

            # Must have http/https protocol
            if not url.startswith("http://") and not url.startswith("https://"):
                return None

            # Reject feed URLs mistakenly provided as link
            feed_url = feed_config.get("url", "")
            if url == feed_url or url.endswith("/feed/") or url.endswith("/rss") or url.endswith("/feed"):
                return None

            # Skip removed or non-article entries
            if title.lower() in ["[removed]", "google news"]:
                return None

            # Parse publication timestamp safely
            published_at = utc_now()
            if entry.get("published_parsed"):
                try:
                    published_at = datetime(*entry.published_parsed[:6])
                except Exception:
                    pass

            # Summary / Description
            description = (
                entry.get("summary")
                or entry.get("description")
                or title
            ).strip()
            if not description:
                description = title

            author = entry.get("author")
            if author:
                author = author.strip()
                if len(author) > 100 or "http" in author:
                    author = None

            image_url = self._extract_image(entry)

            return RawArticle(
                title=title,
                description=description,
                canonical_url=url,
                source_name="Indian Express",
                source_domain="indianexpress.com",
                author=author,
                image_url=image_url,
                published_at=published_at,
                raw_category=feed_config.get("category_hint"),
                country_hint="IN",
                state_hint=feed_config.get("state_hint"),
                language_code=feed_config.get("language_code", "en"),
            )
        except Exception as e:
            logger.warning(f"[RSS Provider] Error parsing entry: {e}")
            return None

    def fetch_india_news(self, category: Optional[str] = None, page_size: int = 20) -> List[RawArticle]:
        """Fetch Indian news from configured RSS feeds.
        
        Fetches configured feeds, isolates individual feed failures, deduplicates
        within the batch, and enforces per-feed / per-category limits.
        """
        self.last_error = None
        feeds_to_fetch = self.feeds

        # If a category is requested, filter feeds matching category_hint or general
        if category:
            matched = [
                f for f in self.feeds
                if f.get("category_hint") == category.lower()
            ]
            if matched:
                feeds_to_fetch = matched

        raw_articles: List[RawArticle] = []
        seen_urls: set[str] = set()
        feed_errors: List[str] = []
        successful_feeds = 0

        headers = {
            "User-Agent": "BharatLens-RSS-Aggregator/1.0",
            "Accept": "application/rss+xml, application/xml, text/xml; q=0.9",
        }

        with httpx.Client(timeout=self.timeout, headers=headers) as client:
            for feed in feeds_to_fetch:
                feed_name = feed.get("name", "Unknown Feed")
                feed_url = feed.get("url")
                if not feed_url:
                    continue

                try:
                    response = client.get(feed_url)
                    response.raise_for_status()

                    parsed = feedparser.parse(response.content)
                    if parsed.bozo and not parsed.entries:
                        err_msg = f"Feed '{feed_name}' parsed with error: {parsed.bozo_exception}"
                        logger.warning(f"[RSS Provider] {err_msg}")
                        feed_errors.append(err_msg)
                        continue

                    feed_articles_count = 0
                    entries = parsed.entries or []
                    for entry in entries:
                        article = self._parse_entry(entry, feed)
                        if article and article.canonical_url not in seen_urls:
                            seen_urls.add(article.canonical_url)
                            raw_articles.append(article)
                            feed_articles_count += 1
                            if feed_articles_count >= page_size:
                                break

                    successful_feeds += 1
                    logger.debug(f"[RSS Provider] Fetched {feed_articles_count} items from '{feed_name}'")

                except httpx.HTTPStatusError as e:
                    err = f"HTTP {e.response.status_code} for feed '{feed_name}'"
                    logger.warning(f"[RSS Provider] {err}")
                    feed_errors.append(err)
                except Exception as e:
                    err = f"Error requesting feed '{feed_name}': {e}"
                    logger.warning(f"[RSS Provider] {err}")
                    feed_errors.append(err)

        if successful_feeds == 0 and feed_errors:
            self.last_error = f"All {len(feeds_to_fetch)} RSS feeds failed: {'; '.join(feed_errors[:3])}"
            logger.error(f"[RSS Provider] {self.last_error}")
            return []

        # Sort combined articles by published_at DESC
        raw_articles.sort(key=lambda a: a.published_at.timestamp() if a.published_at else 0.0, reverse=True)
        return raw_articles

    def fetch_regional_news(self, state: str, language: Optional[str] = "en", page_size: int = 20) -> List[RawArticle]:
        """Fetch regional Indian news from RSS feeds filtered by state/language if matching feeds exist."""
        self.last_error = None
        state_clean = state.strip().lower()
        lang_clean = (language or "en").strip().lower()

        matching_feeds = [
            f for f in self.feeds
            if f.get("state_hint") and f.get("state_hint", "").strip().lower() == state_clean
            and f.get("language_code", "en").lower() == lang_clean
        ]

        if not matching_feeds:
            return []

        raw_articles: List[RawArticle] = []
        seen_urls: set[str] = set()

        headers = {
            "User-Agent": "BharatLens-RSS-Aggregator/1.0",
            "Accept": "application/rss+xml, application/xml, text/xml; q=0.9",
        }

        with httpx.Client(timeout=self.timeout, headers=headers) as client:
            for feed in matching_feeds:
                feed_url = feed.get("url")
                if not feed_url:
                    continue
                try:
                    response = client.get(feed_url)
                    response.raise_for_status()
                    parsed = feedparser.parse(response.content)
                    for entry in (parsed.entries or []):
                        article = self._parse_entry(entry, feed)
                        if article and article.canonical_url not in seen_urls:
                            seen_urls.add(article.canonical_url)
                            raw_articles.append(article)
                            if len(raw_articles) >= page_size:
                                break
                except Exception as e:
                    logger.warning(f"[RSS Provider] Error fetching regional feed {feed.get('name')}: {e}")

        return raw_articles

    def fetch_international_news(self, category: Optional[str] = None, page_size: int = 20) -> List[RawArticle]:
        """Indian Express RSS provider is India-focused; international is delegated to NewsAPI."""
        return []

