from typing import List, Union, Optional
from pathlib import Path
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "BharatLens API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    
    # Primary DB URL (PostgreSQL default, falls back to SQLite for local dev when Postgres is offline)
    DATABASE_URL: str = "sqlite:///./bharatlens.db"
    
    # External News API Configuration (NewsAPI.org)
    NEWS_API_KEY: str | None = None
    NEWS_API_BASE_URL: str = "https://newsapi.org/v2"

    # External News Provider Configuration (GNews.io)
    GNEWS_API_KEY: str | None = None
    GNEWS_BASE_URL: str = "https://gnews.io/api/v4"
    GNEWS_ENABLED: bool = False
    GNEWS_TIMEOUT_SECONDS: float = 10.0
    GNEWS_PAGE_SIZE: int = 10
    GNEWS_LANGUAGE: str = "en"
    GNEWS_COUNTRY: str = "in"

    # Regional News & Indian Languages Configuration (Phase 16)
    REGIONAL_NEWS_ENABLED: bool = True
    REGIONAL_NEWS_LANGUAGES_ENABLED: bool = True
    REGIONAL_NEWS_MAX_REQUESTS_PER_CYCLE: int = 1

    # Background Scheduler Configuration
    ENABLE_NEWS_SCHEDULER: bool = True
    NEWS_INGEST_INTERVAL_MINUTES: int = 60
    NEWS_INGEST_ON_STARTUP: bool = True
    
    # JWT & Authentication Configuration
    JWT_SECRET_KEY: str = "bharatlens-super-secret-key-change-in-production-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Phase 10 — Story Grouping Configuration
    STORY_GROUP_SIMILARITY_THRESHOLD: float = 0.55
    STORY_GROUP_CANDIDATE_WINDOW_DAYS: int = 14

    # Phase 12 — Demo Data Isolation Configuration
    SHOW_DEMO_ARTICLES: bool = False

    # CORS Configuration

    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def resolve_sqlite_url(cls, v: Union[str, None]) -> str:
        if not v or v == "sqlite:///./bharatlens.db":
            backend_dir = Path(__file__).resolve().parent.parent.parent
            return f"sqlite:///{backend_dir / 'bharatlens.db'}".replace("\\", "/")
        if v.startswith("sqlite:///."):
            backend_dir = Path(__file__).resolve().parent.parent.parent
            rel_path = v.replace("sqlite:///./", "")
            return f"sqlite:///{backend_dir / rel_path}".replace("\\", "/")
        return v

    @field_validator("NEWS_API_KEY", "GNEWS_API_KEY", mode="before")
    @classmethod
    def clean_api_keys(cls, v: Union[str, None]) -> Optional[str]:
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=(".env", str(Path(__file__).resolve().parent.parent.parent / ".env")),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
