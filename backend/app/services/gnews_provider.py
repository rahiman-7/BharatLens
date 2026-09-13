import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse
import httpx

from app.core.config import settings
from app.core.datetime_utils import utc_now
from app.services.news_provider import BaseNewsProvider, RawArticle

# Ensure HTTP clients do not log sensitive URLs with query parameters
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("bharatlens.gnews_provider")



class GNewsProvider(BaseNewsProvider):
    """GNews.io API v4 implementation of BaseNewsProvider."""

    # GNews supported categories: general, world, nation, business, technology, entertainment, sports, science, health
    CATEGORY_MAPPING = {
        "business": "business",
        "entertainment": "entertainment",
        "general": "general",
        "health": "health",
        "science": "science",
        "sports": "sports",
        "technology": "technology",
        "politics": "nation",
        "education": "general",
        "environment": "science",
        "lifestyle": "general",
        "crime": "nation",
        "world": "world",
        "nation": "nation",
    }

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__()
        self.api_key = api_key if api_key is not None else settings.GNEWS_API_KEY
        self.base_url = (base_url or settings.GNEWS_BASE_URL).rstrip("/")
        self.timeout = float(getattr(settings, "GNEWS_TIMEOUT_SECONDS", 10.0))

    def _extract_error_detail(self, response: httpx.Response) -> str:
        """Extract structured GNews error detail without exposing API keys."""
        try:
            err_data = response.json()
            errors = err_data.get("errors")
            if isinstance(errors, list):
                msg = "; ".join(str(e) for e in errors)
            elif isinstance(errors, str):
                msg = errors
            elif isinstance(err_data.get("message"), str):
                msg = err_data.get("message")
            else:
                msg = response.reason_phrase or "Error"
            return f"HTTP {response.status_code}: {msg}"
        except Exception:
            return f"HTTP {response.status_code} {response.reason_phrase or 'Error'}"

    def _validate_url(self, url: str) -> bool:
        """Validate that the URL is a legitimate external publisher URL."""
        if not url:
            return False
        clean = url.strip().lower()
        if not clean.startswith("http://") and not clean.startswith("https://"):
            return False
        # Reject placeholders, api endpoints, localhost, or example domains
        invalid_hosts = ["localhost", "127.0.0.1", "example.com", "gnews.io/api", "removed.com"]
        for inv in invalid_hosts:
            if inv in clean:
                return False
        return True

    def _parse_article(
        self,
        item: Dict[str, Any],
        country_hint: Optional[str] = None,
        raw_category: Optional[str] = None,
        language_code: Optional[str] = "en",
        state_hint: Optional[str] = None,
    ) -> Optional[RawArticle]:
        """Normalize raw GNews item into unified RawArticle format."""
        try:
            title = (item.get("title") or "").strip()
            url = (item.get("url") or "").strip()

            if not title or not self._validate_url(url):
                return None

            # Parse published timestamp (ISO 8601 format e.g. "2026-09-12T04:00:00Z")
            published_str = item.get("publishedAt")
            if published_str:
                try:
                    published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    published_at = utc_now()
            else:
                published_at = utc_now()

            # Source extraction (preserve original publisher)
            source_data = item.get("source") or {}
            source_name = (source_data.get("name") or "").strip()
            source_url = (source_data.get("url") or "").strip()

            source_domain = None
            if source_url:
                try:
                    parsed_src = urlparse(source_url)
                    source_domain = parsed_src.netloc.replace("www.", "")
                except Exception:
                    pass

            if not source_domain:
                try:
                    parsed_url = urlparse(url)
                    source_domain = parsed_url.netloc.replace("www.", "")
                except Exception:
                    pass

            if not source_name:
                source_name = source_domain or "News Provider"

            description = item.get("description")
            if description:
                description = description.strip()

            image_url = item.get("image")
            if image_url:
                image_url = image_url.strip()
                if not image_url.startswith("http://") and not image_url.startswith("https://"):
                    image_url = None

            return RawArticle(
                title=title,
                description=description or title,
                canonical_url=url,
                source_name=source_name,
                source_domain=source_domain,
                author=None,
                image_url=image_url,
                published_at=published_at,
                raw_category=raw_category,
                country_hint=country_hint,
                state_hint=state_hint,
                language_code=language_code or "en",
            )
        except Exception as e:
            logger.warning(f"Error parsing raw GNews article: {e}")
            return None

    def fetch_india_news(self, category: Optional[str] = None, page_size: int = 10) -> List[RawArticle]:
        """Fetch Indian news headlines from GNews API v4."""
        if not self.api_key:
            err = "GNEWS_API_KEY is not configured in backend/.env. GNews live ingestion is disabled."
            logger.warning(f"[GNews Provider] {err}")
            self.last_error = err
            return []

        endpoint = f"{self.base_url}/top-headlines"
        params: Dict[str, Any] = {
            "country": settings.GNEWS_COUNTRY or "in",
            "lang": settings.GNEWS_LANGUAGE or "en",
            "max": min(page_size, 25),
            "apikey": self.api_key,
        }

        if category and category.lower() in self.CATEGORY_MAPPING:
            params["category"] = self.CATEGORY_MAPPING[category.lower()]

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(endpoint, params=params)
                response.raise_for_status()
                data = response.json()

                if "errors" in data and data["errors"]:
                    err = f"GNews error: {data['errors']}"
                    logger.error(f"[GNews Provider] {err}")
                    self.last_error = err
                    return []

                raw_articles: List[RawArticle] = []
                for item in data.get("articles", []):
                    parsed = self._parse_article(
                        item,
                        country_hint="IN",
                        raw_category=category,
                        language_code=settings.GNEWS_LANGUAGE or "en",
                    )
                    if parsed:
                        raw_articles.append(parsed)

                return raw_articles
        except httpx.HTTPStatusError as e:
            err = f"GNews India headlines request failed: {self._extract_error_detail(e.response)}"
            logger.error(f"[GNews Provider] {err}")
            self.last_error = err
            return []
        except Exception as e:
            err = f"Failed to fetch India news from GNews: {e}"
            logger.error(f"[GNews Provider] {err}")
            self.last_error = err
            return []

    def fetch_international_news(self, category: Optional[str] = None, page_size: int = 10) -> List[RawArticle]:
        """Fetch International/World news headlines from GNews API v4."""
        if not self.api_key:
            err = "GNEWS_API_KEY is not configured in backend/.env. GNews live ingestion is disabled."
            logger.warning(f"[GNews Provider] {err}")
            self.last_error = err
            return []

        endpoint = f"{self.base_url}/top-headlines"
        params: Dict[str, Any] = {
            "lang": settings.GNEWS_LANGUAGE or "en",
            "max": min(page_size, 25),
            "apikey": self.api_key,
        }

        if category and category.lower() in self.CATEGORY_MAPPING:
            params["category"] = self.CATEGORY_MAPPING[category.lower()]
        else:
            params["category"] = "world"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(endpoint, params=params)
                response.raise_for_status()
                data = response.json()

                if "errors" in data and data["errors"]:
                    err = f"GNews error: {data['errors']}"
                    logger.error(f"[GNews Provider] {err}")
                    self.last_error = err
                    return []

                raw_articles: List[RawArticle] = []
                for item in data.get("articles", []):
                    parsed = self._parse_article(
                        item,
                        country_hint="GLOBAL",
                        raw_category=category or "world",
                        language_code=settings.GNEWS_LANGUAGE or "en",
                    )
                    if parsed:
                        raw_articles.append(parsed)

                return raw_articles
        except httpx.HTTPStatusError as e:
            err = f"GNews International headlines request failed: {self._extract_error_detail(e.response)}"
            logger.error(f"[GNews Provider] {err}")
            self.last_error = err
            return []
        except Exception as e:
            err = f"Failed to fetch international news from GNews: {e}"
            logger.error(f"[GNews Provider] {err}")
            self.last_error = err
            return []

    def fetch_regional_news(
        self,
        state: Optional[str] = None,
        language: Optional[str] = None,
        page_size: int = 10,
    ) -> List[RawArticle]:
        """Fetch state-specific regional news with native language filtering via GNews Search endpoint."""
        if not self.api_key:
            err = "GNEWS_API_KEY is not configured in backend/.env. GNews live ingestion is disabled."
            logger.warning(f"[GNews Provider] {err}")
            self.last_error = err
            return []

        query = state.strip() if state else "India"
        lang_code = language.strip().lower() if language else "en"

        endpoint = f"{self.base_url}/search"
        params: Dict[str, Any] = {
            "q": query,
            "lang": lang_code,
            "country": "in",
            "max": min(page_size, 25),
            "apikey": self.api_key,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(endpoint, params=params)
                response.raise_for_status()
                data = response.json()

                if "errors" in data and data["errors"]:
                    err = f"GNews regional error: {data['errors']}"
                    logger.error(f"[GNews Provider] {err}")
                    self.last_error = err
                    return []

                raw_articles: List[RawArticle] = []
                for item in data.get("articles", []):
                    parsed = self._parse_article(
                        item,
                        country_hint="IN",
                        state_hint=state,
                        language_code=lang_code,
                    )
                    if parsed:
                        raw_articles.append(parsed)

                return raw_articles
        except httpx.HTTPStatusError as e:
            err = f"GNews regional request failed: {self._extract_error_detail(e.response)}"
            logger.error(f"[GNews Provider] {err}")
            self.last_error = err
            return []
        except Exception as e:
            err = f"Failed to fetch regional news from GNews: {e}"
            logger.error(f"[GNews Provider] {err}")
            self.last_error = err
            return []
