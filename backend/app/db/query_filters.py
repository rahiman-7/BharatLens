from sqlalchemy.orm import Query
from app.core.config import settings
from app.models.article import Article


def apply_demo_filter(query: Query, model=Article) -> Query:
    """Filter out demo articles from public query results unless SHOW_DEMO_ARTICLES is explicitly enabled."""
    if not settings.SHOW_DEMO_ARTICLES:
        return query.filter(model.is_demo.is_(False))
    return query
