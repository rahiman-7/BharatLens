import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import httpx
from app.core.config import settings
from app.core.datetime_utils import utc_now

logger = logging.getLogger("bharatlens.news_provider")


class RawArticle(BaseModel):
    title: str
    description: Optional[str] = None
    canonical_url: str
    source_name: str
    source_domain: Optional[str] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    published_at: datetime
    raw_category: Optional[str] = None
    country_hint: Optional[str] = None
    state_hint: Optional[str] = None
    language_code: Optional[str] = "en"


class BaseNewsProvider(ABC):
    """Abstract Base Class for External News Providers."""

    def __init__(self):
        self.last_error: Optional[str] = None

    @abstractmethod
    def fetch_india_news(self, category: Optional[str] = None, page_size: int = 20) -> List[RawArticle]:
        pass

    @abstractmethod
    def fetch_international_news(self, category: Optional[str] = None, page_size: int = 20) -> List[RawArticle]:
        pass

    def fetch_regional_news(self, state: Optional[str] = None, language: Optional[str] = None, page_size: int = 10) -> List[RawArticle]:
        """Fetch state/regional news with optional native language filtering (default: empty)."""
        return []


class NewsAPIProvider(BaseNewsProvider):
    """NewsAPI.org implementation of BaseNewsProvider."""

    # NewsAPI categories mapping
    CATEGORY_MAPPING = {
        "business": "business",
        "entertainment": "entertainment",
        "general": "general",
        "health": "health",
        "science": "science",
        "sports": "sports",
        "technology": "technology",
        "politics": "general",
        "education": "general",
        "environment": "science",
        "lifestyle": "general",
        "crime": "general",
    }

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__()
        self.api_key = api_key if api_key is not None else settings.NEWS_API_KEY
        self.base_url = (base_url or settings.NEWS_API_BASE_URL).rstrip("/")
        self.timeout = 10.0

    def _get_headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        return {
            "X-Api-Key": self.api_key,
            "User-Agent": "BharatLens-Aggregator/1.0",
        }

    def _extract_error_detail(self, response: httpx.Response) -> str:
        """Extract structured NewsAPI error code and message without exposing secrets."""
        try:
            err_data = response.json()
            code = err_data.get("code", "unknown")
            msg = err_data.get("message", response.reason_phrase or "Error")
            return f"HTTP {response.status_code} [{code}]: {msg}"
        except Exception:
            return f"HTTP {response.status_code} {response.reason_phrase or 'Error'}"

    def _parse_article(self, item: Dict[str, Any], country_hint: Optional[str] = None, raw_category: Optional[str] = None) -> Optional[RawArticle]:
        try:
            title = (item.get("title") or "").strip()
            url = (item.get("url") or "").strip()
            
            # Skip invalid articles or removed articles
            if not title or not url or title == "[Removed]" or url.startswith("https://removed.com"):
                return None

            # Parse published timestamp
            published_str = item.get("publishedAt")
            if published_str:
                try:
                    published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    published_at = utc_now()
            else:
                published_at = utc_now()

            # Source extraction
            source_data = item.get("source") or {}
            source_name = (source_data.get("name") or "News Provider").strip()
            
            # Extract domain from URL if available
            source_domain = None
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                source_domain = parsed.netloc.replace("www.", "")
            except Exception:
                pass

            description = item.get("description")
            if description:
                description = description.strip()

            image_url = item.get("urlToImage")
            if image_url:
                image_url = image_url.strip()

            author = item.get("author")
            if author:
                author = author.strip()
                # Clean up if author is a URL or too long
                if len(author) > 100 or "http" in author:
                    author = None

            return RawArticle(
                title=title,
                description=description or title,
                canonical_url=url,
                source_name=source_name,
                source_domain=source_domain,
                author=author,
                image_url=image_url,
                published_at=published_at,
                raw_category=raw_category,
                country_hint=country_hint,
            )
        except Exception as e:
            logger.warning(f"Error parsing raw article: {e}")
            return None

    def fetch_india_news(self, category: Optional[str] = None, page_size: int = 20) -> List[RawArticle]:
        """Fetch Indian news headlines from NewsAPI.
        
        Strategy:
        1. Attempt /v2/top-headlines?country=in.
        2. If /v2/top-headlines returns 0 results (NewsAPI regional top-headlines coverage gap),
           transparently use /v2/everything with India discovery strategy (q='India' or 'India AND {cat}')
           sorted by publishedAt to ensure real-time fresh articles populate the BharatLens feed.
        """
        if not self.api_key:
            err = "NEWS_API_KEY is not configured in backend/.env. Live news ingestion cannot fetch external articles."
            logger.warning(f"[NewsAPI Provider] {err}")
            self.last_error = err
            return []

        endpoint = f"{self.base_url}/top-headlines"
        params: Dict[str, Any] = {
            "country": "in",
            "pageSize": min(page_size, 100),
        }

        if category and category in self.CATEGORY_MAPPING:
            params["category"] = self.CATEGORY_MAPPING[category]

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(endpoint, params=params, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != "ok":
                    err = f"NewsAPI error ({data.get('code', 'unknown')}): {data.get('message', 'Unspecified error')}"
                    logger.error(f"[NewsAPI Provider] {err}")
                    self.last_error = err
                    return []

                raw_articles = []
                for item in data.get("articles", []):
                    parsed = self._parse_article(item, country_hint="IN", raw_category=category)
                    if parsed:
                        raw_articles.append(parsed)

                if raw_articles:
                    return raw_articles

                # Fallback to /v2/everything when top-headlines has 0 articles for country=in
                logger.info("[NewsAPI Provider] /v2/top-headlines?country=in returned 0 articles. Falling back to /v2/everything with India discovery strategy.")
                everything_endpoint = f"{self.base_url}/everything"
                query_term = f"India AND {category}" if category else "India"
                everything_params: Dict[str, Any] = {
                    "q": query_term,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": min(page_size, 100),
                }
                ev_response = client.get(everything_endpoint, params=everything_params, headers=self._get_headers())
                ev_response.raise_for_status()
                ev_data = ev_response.json()
                
                if ev_data.get("status") != "ok":
                    err = f"NewsAPI error ({ev_data.get('code', 'unknown')}): {ev_data.get('message', 'Unspecified error')}"
                    logger.error(f"[NewsAPI Provider] {err}")
                    self.last_error = err
                    return []

                for item in ev_data.get("articles", []):
                    parsed = self._parse_article(item, country_hint="IN", raw_category=category)
                    if parsed:
                        raw_articles.append(parsed)

                return raw_articles
        except httpx.HTTPStatusError as e:
            err = f"NewsAPI India headlines request failed: {self._extract_error_detail(e.response)}"
            logger.error(f"[NewsAPI Provider] {err}")
            self.last_error = err
            return []
        except Exception as e:
            err = f"Failed to fetch India news from NewsAPI: {e}"
            logger.error(f"[NewsAPI Provider] {err}")
            self.last_error = err
            return []

    def fetch_international_news(self, category: Optional[str] = None, page_size: int = 20) -> List[RawArticle]:
        """Fetch International/Global news from NewsAPI."""
        if not self.api_key:
            err = "NEWS_API_KEY is not configured in backend/.env. Live news ingestion cannot fetch external articles."
            logger.warning(f"[NewsAPI Provider] {err}")
            self.last_error = err
            return []

        # Use top-headlines for world news with global language or general category
        endpoint = f"{self.base_url}/top-headlines"
        params: Dict[str, Any] = {
            "language": "en",
            "pageSize": min(page_size, 100),
        }

        if category and category in self.CATEGORY_MAPPING:
            params["category"] = self.CATEGORY_MAPPING[category]
        else:
            params["category"] = "general"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(endpoint, params=params, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != "ok":
                    err = f"NewsAPI error ({data.get('code', 'unknown')}): {data.get('message', 'Unspecified error')}"
                    logger.error(f"[NewsAPI Provider] {err}")
                    self.last_error = err
                    return []

                raw_articles = []
                for item in data.get("articles", []):
                    parsed = self._parse_article(item, country_hint="GLOBAL", raw_category=category)
                    if parsed:
                        raw_articles.append(parsed)
                return raw_articles
        except httpx.HTTPStatusError as e:
            err = f"NewsAPI International headlines request failed: {self._extract_error_detail(e.response)}"
            logger.error(f"[NewsAPI Provider] {err}")
            self.last_error = err
            return []
        except Exception as e:
            err = f"Failed to fetch international news from NewsAPI: {e}"
            logger.error(f"[NewsAPI Provider] {err}")
            self.last_error = err
            return []


# Avoid circular import by importing RSSNewsProvider at bottom of module
from app.services.rss_provider import RSSNewsProvider  # noqa: E402


